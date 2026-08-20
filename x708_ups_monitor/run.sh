#!/usr/bin/with-contenv bashio
# ==============================================================================
# Démarrage de l'addon X708 UPS Monitor
# ==============================================================================

I2C_BUS=$(bashio::config 'i2c_bus')
I2C_ADDRESS=$(bashio::config 'i2c_address')
POLL_INTERVAL=$(bashio::config 'poll_interval')
LOW_BATTERY_THRESHOLD=$(bashio::config 'low_battery_threshold')
SHUTDOWN_THRESHOLD=$(bashio::config 'shutdown_threshold')
GPIO_CHIP=$(bashio::config 'gpio_chip')
GPIO_PIN=$(bashio::config 'gpio_shutdown_pin')
ENABLE_GPIO_SHUTDOWN_PULSE=$(bashio::config 'enable_gpio_shutdown_pulse')
SENSOR_PREFIX=$(bashio::config 'sensor_prefix')

export I2C_BUS
export I2C_ADDRESS
export POLL_INTERVAL
export LOW_BATTERY_THRESHOLD
export SHUTDOWN_THRESHOLD
export GPIO_CHIP
export GPIO_PIN
export ENABLE_GPIO_SHUTDOWN_PULSE
export SENSOR_PREFIX
export SUPERVISOR_TOKEN

bashio::log.info "Bus I2C          : ${I2C_BUS}"
bashio::log.info "Adresse I2C       : ${I2C_ADDRESS}"
bashio::log.info "Intervalle (s)    : ${POLL_INTERVAL}"
bashio::log.info "Seuil batt. faible: ${LOW_BATTERY_THRESHOLD}%"
bashio::log.info "Seuil arrêt       : ${SHUTDOWN_THRESHOLD}%"
bashio::log.info "Démarrage du monitoring de la batterie X708..."

exec python3 /x708_monitor.py
