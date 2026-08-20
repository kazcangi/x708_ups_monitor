# Changelog

## 1.0.0
- Version initiale : lecture batterie X708 (MAX17040) via I2C
- Publication des capteurs `sensor.x708_battery_level`, `sensor.x708_battery_voltage`
  et `binary_sensor.x708_low_battery` dans Home Assistant
- Notification persistante et arrêt automatique du Raspberry Pi à 15% de batterie
- Impulsion GPIO optionnelle imitant `xSoft.sh` pour couper le X708
