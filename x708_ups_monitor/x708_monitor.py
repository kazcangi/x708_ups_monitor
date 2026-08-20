#!/usr/bin/env python3
"""
X708 UPS Monitor - Addon Home Assistant
-----------------------------------------
Lit la tension et le pourcentage de charge de la batterie du HAT
Geekworm X708 via la puce de jauge de batterie MAX17040 (I2C, adresse 0x36),
publie ces valeurs comme capteurs Home Assistant via l'API Supervisor,
et déclenche un arrêt propre du Raspberry Pi quand le seuil critique
est atteint (par défaut 15%).

Références matérielles (Geekworm Wiki - X708-script) :
  - Puce de jauge de batterie : MAX17040 / MAX17041, adresse I2C 0x36
  - Registre 0x02 : tension de la cellule (VCELL)
  - Registre 0x04 : état de charge (SOC, %)
  - GPIO 13 (chip 0) : broche utilisée par xSoft.sh pour l'arrêt logiciel
"""

import os
import sys
import time
import struct
import logging

import requests

try:
    import smbus2 as smbus
except ImportError:  # fallback si seul smbus est dispo
    import smbus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - x708 - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("x708")

# ----------------------------------------------------------------------------
# Configuration (fournie par run.sh via variables d'environnement)
# ----------------------------------------------------------------------------
I2C_BUS = int(os.environ.get("I2C_BUS", 1))
I2C_ADDRESS = int(os.environ.get("I2C_ADDRESS", "0x36"), 16)
POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", 30))
LOW_BATTERY_THRESHOLD = float(os.environ.get("LOW_BATTERY_THRESHOLD", 25))
SHUTDOWN_THRESHOLD = float(os.environ.get("SHUTDOWN_THRESHOLD", 15))
GPIO_CHIP = os.environ.get("GPIO_CHIP", "gpiochip0")
GPIO_PIN = int(os.environ.get("GPIO_PIN", 13))
ENABLE_GPIO_SHUTDOWN_PULSE = os.environ.get(
    "ENABLE_GPIO_SHUTDOWN_PULSE", "true"
).lower() in ("1", "true", "yes")
SENSOR_PREFIX = os.environ.get("SENSOR_PREFIX", "x708")

SUPERVISOR_TOKEN = os.environ.get("SUPERVISOR_TOKEN")
SUPERVISOR_API = "http://supervisor"
HA_HEADERS = {
    "Authorization": f"Bearer {SUPERVISOR_TOKEN}",
    "Content-Type": "application/json",
}

STATE_FLAG_FILE = "/data/shutdown_triggered"


# ----------------------------------------------------------------------------
# Lecture I2C - MAX17040
# ----------------------------------------------------------------------------
def _read_word_swapped(bus, address, register):
    """Le MAX17040 retourne les mots en big-endian, smbus lit en little-endian."""
    raw = bus.read_word_data(address, register)
    swapped = struct.unpack("<H", struct.pack(">H", raw))[0]
    return swapped


def read_voltage(bus):
    """Tension de la batterie en volts."""
    raw = _read_word_swapped(bus, I2C_ADDRESS, 0x02)
    return raw * 1.25 / 1000 / 16


def read_capacity(bus):
    """Pourcentage de charge estimé (0-100)."""
    raw = _read_word_swapped(bus, I2C_ADDRESS, 0x04)
    percent = raw / 256.0
    return max(0.0, min(100.0, percent))


# ----------------------------------------------------------------------------
# API Home Assistant Supervisor
# ----------------------------------------------------------------------------
def set_state(entity_id, state, attributes=None):
    if not SUPERVISOR_TOKEN:
        log.warning("SUPERVISOR_TOKEN absent, capteur %s non publié", entity_id)
        return
    url = f"{SUPERVISOR_API}/core/api/states/{entity_id}"
    payload = {"state": state, "attributes": attributes or {}}
    try:
        r = requests.post(url, headers=HA_HEADERS, json=payload, timeout=10)
        r.raise_for_status()
    except requests.RequestException as exc:
        log.error("Impossible de publier %s : %s", entity_id, exc)


def notify(title, message):
    if not SUPERVISOR_TOKEN:
        return
    url = f"{SUPERVISOR_API}/core/api/services/persistent_notification/create"
    try:
        requests.post(
            url,
            headers=HA_HEADERS,
            json={"title": title, "message": message, "notification_id": "x708_ups"},
            timeout=10,
        )
    except requests.RequestException as exc:
        log.error("Notification impossible : %s", exc)


def trigger_host_shutdown():
    """Demande au Supervisor d'éteindre proprement l'hôte (le Raspberry Pi)."""
    url = f"{SUPERVISOR_API}/host/shutdown"
    try:
        r = requests.post(url, headers=HA_HEADERS, timeout=15)
        r.raise_for_status()
        log.info("Arrêt de l'hôte demandé avec succès via l'API Supervisor.")
    except requests.RequestException as exc:
        log.error("Échec de la demande d'arrêt via l'API Supervisor : %s", exc)


# ----------------------------------------------------------------------------
# Impulsion GPIO (reproduit le comportement de xSoft.sh pour couper le X708)
# ----------------------------------------------------------------------------
def gpio_shutdown_pulse():
    if not ENABLE_GPIO_SHUTDOWN_PULSE:
        return
    try:
        import gpiod

        chip = gpiod.Chip(GPIO_CHIP)
        line = chip.get_line(GPIO_PIN)
        line.request(consumer="x708-ups-monitor", type=gpiod.LINE_REQ_DIR_OUT)
        line.set_value(1)
        time.sleep(1)
        line.set_value(0)
        line.release()
        chip.close()
        log.info("Impulsion GPIO %s/%s envoyée au X708.", GPIO_CHIP, GPIO_PIN)
    except Exception as exc:  # noqa: BLE001
        log.error(
            "Impossible d'envoyer l'impulsion GPIO (%s). "
            "L'arrêt logiciel de l'OS sera quand même déclenché, mais le X708 "
            "risque de rester alimenté par la batterie. Pensez à garder le "
            "service natif 'x708-pwr' installé sur l'hôte en complément.",
            exc,
        )


# ----------------------------------------------------------------------------
# Boucle principale
# ----------------------------------------------------------------------------
def already_shutdown_triggered():
    return os.path.exists(STATE_FLAG_FILE)


def mark_shutdown_triggered():
    try:
        os.makedirs(os.path.dirname(STATE_FLAG_FILE), exist_ok=True)
        with open(STATE_FLAG_FILE, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass


def main():
    log.info("Connexion au bus I2C %s (adresse 0x%02X)...", I2C_BUS, I2C_ADDRESS)
    bus = smbus.SMBus(I2C_BUS)

    triggered = already_shutdown_triggered()
    if triggered:
        log.warning(
            "Un arrêt a déjà été déclenché précédemment (fichier %s présent). "
            "Supprimez ce fichier dans /data pour réarmer la surveillance.",
            STATE_FLAG_FILE,
        )

    while True:
        try:
            voltage = read_voltage(bus)
            percent = read_capacity(bus)

            log.info("Batterie : %.1f%% - %.3f V", percent, voltage)

            set_state(
                f"sensor.{SENSOR_PREFIX}_battery_level",
                round(percent, 1),
                {
                    "unit_of_measurement": "%",
                    "device_class": "battery",
                    "state_class": "measurement",
                    "friendly_name": "X708 Batterie",
                    "icon": "mdi:battery",
                },
            )
            set_state(
                f"sensor.{SENSOR_PREFIX}_battery_voltage",
                round(voltage, 3),
                {
                    "unit_of_measurement": "V",
                    "device_class": "voltage",
                    "state_class": "measurement",
                    "friendly_name": "X708 Tension batterie",
                    "icon": "mdi:flash",
                },
            )
            set_state(
                f"binary_sensor.{SENSOR_PREFIX}_low_battery",
                "on" if percent <= LOW_BATTERY_THRESHOLD else "off",
                {
                    "device_class": "battery",
                    "friendly_name": "X708 Batterie faible",
                },
            )

            if percent <= SHUTDOWN_THRESHOLD and not triggered:
                triggered = True
                mark_shutdown_triggered()
                log.critical(
                    "Seuil critique atteint (%.1f%% <= %.1f%%). "
                    "Arrêt du Raspberry Pi en cours...",
                    percent,
                    SHUTDOWN_THRESHOLD,
                )
                notify(
                    "X708 UPS - Batterie critique",
                    f"Batterie à {percent:.0f}% (seuil : {SHUTDOWN_THRESHOLD:.0f}%). "
                    "Le Raspberry Pi va s'éteindre automatiquement.",
                )
                # Laisse le temps à la notification/aux capteurs de partir
                time.sleep(3)
                gpio_shutdown_pulse()
                trigger_host_shutdown()

        except OSError as exc:
            log.error("Erreur de lecture I2C : %s", exc)
        except Exception as exc:  # noqa: BLE001
            log.error("Erreur inattendue : %s", exc)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
