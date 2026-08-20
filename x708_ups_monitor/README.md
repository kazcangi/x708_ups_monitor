# X708 UPS Monitor — Addon Home Assistant

Addon pour Home Assistant OS / Supervisor qui surveille la batterie du HAT
d'alimentation **Geekworm X708** (UPS pour Raspberry Pi) et éteint
automatiquement le Raspberry Pi lorsque le niveau de batterie devient
critique.

## Fonctionnalités

- Lecture de la tension et du pourcentage de charge via la puce de jauge
  de batterie **MAX17040/MAX17041** (I2C, adresse `0x36`), la même puce
  que celle utilisée par les scripts officiels Geekworm.
- Publication automatique de 3 entités dans Home Assistant :
  - `sensor.x708_battery_level` (%)
  - `sensor.x708_battery_voltage` (V)
  - `binary_sensor.x708_low_battery` (on/off sous un seuil configurable)
- Notification persistante Home Assistant quand le seuil critique est atteint.
- Arrêt automatique et propre du Raspberry Pi via l'API Supervisor
  (`/host/shutdown`) lorsque la batterie descend au seuil configuré
  (**15% par défaut**).
- Impulsion GPIO optionnelle (GPIO 13 par défaut) qui reproduit le
  comportement du script officiel `xSoft.sh`, pour aider à couper
  complètement l'alimentation du X708 après l'arrêt de l'OS.

## Installation

1. Copiez le dossier `x708_addon` dans `/addons/x708_ups_monitor` sur votre
   installation Home Assistant (via l'add-on **Samba** / **SSH & Terminal**,
   ou en le poussant vers un dépôt Git personnel ajouté dans
   *Paramètres → Modules complémentaires → Boutique des modules → dépôts*).
2. Dans Home Assistant : **Paramètres → Modules complémentaires → Boutique
   des modules**, cliquez sur les trois points en haut à droite puis
   **Actualiser**. L'addon "X708 UPS Monitor" doit apparaître dans la
   section "Local add-ons".
3. Ouvrez l'addon, cliquez sur **Installer**, puis configurez les options
   (onglet **Configuration**) selon vos besoins.
4. Démarrez l'addon. Vérifiez les journaux (**Logs**) : vous devriez voir
   la tension et le pourcentage de batterie relevés toutes les
   `poll_interval` secondes.

## Options de configuration

| Option | Défaut | Description |
|---|---|---|
| `i2c_bus` | `1` | Numéro du bus I2C (`/dev/i2c-1` sur la plupart des Raspberry Pi) |
| `i2c_address` | `"0x36"` | Adresse I2C de la puce de jauge de batterie |
| `poll_interval` | `30` | Intervalle de lecture en secondes |
| `low_battery_threshold` | `25` | Seuil (%) sous lequel `binary_sensor.x708_low_battery` passe à `on` |
| `shutdown_threshold` | `15` | Seuil (%) déclenchant l'arrêt automatique du Raspberry Pi |
| `gpio_chip` | `"gpiochip0"` | Puce GPIO utilisée pour l'impulsion d'extinction |
| `gpio_shutdown_pin` | `13` | Broche GPIO utilisée par le X708 pour l'arrêt logiciel |
| `enable_gpio_shutdown_pulse` | `true` | Active/désactive l'impulsion GPIO lors de l'arrêt |
| `sensor_prefix` | `"x708"` | Préfixe des entités créées dans Home Assistant |

## Prérequis matériels

- I2C doit être activé sur l'hôte (Raspberry Pi OS / HAOS) :
  **Paramètres → Système → Matériel → activer l'I2C**, ou via
  `raspi-config` si vous utilisez Raspberry Pi OS avec Supervisor.
- Le X708 doit être correctement connecté et alimenté (vérifiable avec
  `i2cdetect -y 1`, l'adresse `36` doit apparaître).

## ⚠️ Important — coupure complète de l'alimentation

L'API Supervisor `/host/shutdown` arrête proprement le système
d'exploitation du Raspberry Pi (halt). L'impulsion GPIO intégrée à cet
addon tente de reproduire le comportement du script officiel `xSoft.sh`
pour couper aussi l'alimentation du X708 lui-même. Cependant, le minutage
exact utilisé par Geekworm dans son service systemd natif
(`x708-pwr.service`, exécuté directement sur l'hôte, hors conteneur) est
plus fiable pour garantir une coupure complète de la carte UPS après
l'extinction totale de l'OS.

**Recommandation** : pour une coupure garantie à 100%, installez en
complément le script officiel sur l'hôte (en dehors de Home Assistant) :

```bash
git clone https://github.com/geekworm-com/x708-script
cd x708-script
chmod +x *.sh
sudo cp -f ./xPWR.sh /usr/local/bin/
sudo cp -f x708-pwr.service /lib/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable x708-pwr
sudo systemctl start x708-pwr
```

Cet addon reste utile même dans ce cas, car il apporte la **visibilité de
la batterie dans Home Assistant** (capteurs, automatisations, dashboard,
notifications) que le script natif n'offre pas.

## Automatisations possibles

Une fois les capteurs disponibles, vous pouvez par exemple créer une
automatisation Home Assistant qui vous envoie une notification mobile
quand `binary_sensor.x708_low_battery` passe à `on`, en complément de
l'arrêt automatique déjà géré par l'addon.

## Dépannage

- **Aucune donnée / erreurs I2C** : vérifiez que `/dev/i2c-1` est bien
  listé dans `devices` du addon et que l'I2C est activé sur l'hôte.
- **`SUPERVISOR_TOKEN absent`** : assurez-vous que `hassio_api: true` et
  `homeassistant_api: true` sont bien présents dans `config.yaml` et que
  l'addon a été réinstallé après modification.
- **L'arrêt ne se déclenche qu'une fois** : c'est voulu. Un fichier témoin
  est créé dans `/data/shutdown_triggered` pour éviter de redemander un
  arrêt en boucle. Supprimez-le (via l'onglet Terminal de l'addon, ou
  en désinstallant/réinstallant l'addon) pour réarmer la surveillance.
