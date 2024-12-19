# LeafSpy integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<p align="center"><img src="leafspy.png" width="64"></p>

This Home Assistant component enables you to get information from your Nissan Leaf car into Home Assistant by integrating with the LeafSpy [Android](https://play.google.com/store/apps/details?id=com.Turbo3.Leaf_Spy_Pro&hl=en_US) or [iOS](https://apps.apple.com/us/app/leafspy-pro/id967376861) apps.

Plug a Bluetooth OBD2 adapter (like [this one](https://www.amazon.com/gp/product/B0755N61PW/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)) into your Nissan Leaf. Open up LeafSpy and pair your phone with the adapter. It will then read information from your car. This integration will allow your phone to submit that info to Home Assistant.

## Installation and configuration

1. [Install HACS](https://www.hacs.xyz/docs/use/configuration/basic/).
2. Add this to HACS as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) by pressing this button and pressing "Download" in the bottom right.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jesserockz&repository=ha-leafspy&category=integration)

3. Restart Home Assistant
4. Add the Leaf Spy integration by pressing this button.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=leafspy)
  
5. Configure your LeafSpy app settings using the information below, which will also be displayed on screen. If you don't have the app in front of you, copy down the password. The generated password will only be shown this once; if you don't copy it down, you'll have to uninstall the integration, restart, and reinstall. Open the LeafSpy app, go to `Menu` -> `Settings`.
- In the **Units** section:
  - Choose `°C`
  - `Convert Outside Temperature`: `On`
  - `CAN Odometer in Miles`: `On` (if you see the option and if your car odometer displays in miles)
- In the **Server** section:
  - `Enable`: `On`
  - `Send Interval`: Whatever frequency you prefer
  - `PW`: `<Generated and displayed during setup>`
  - `Http://` or `Https://`: Depends on your Home Assistant installation
  - `URL`: `<Displayed during setup>`
    - (**Do not** include the http or https prefix in the URL field.)

## Entities
_See [LeafSpy manual](https://leafspy.com/wp-content/uploads/2024/04/LeafSpy-Help-1.5.0.pdf#page=70) for more details on the data that the app sends._

### Device tracker
| Entity ID | Note |
| :-- | :-- |
| device_tracker.leaf | Tracks latitude, longitude, GPS accuracy, and battery level |

### Binary sensor
| Entity ID |
| :-- |
| binary_sensor.leaf_power |

### Sensors
| Entity ID | Unit reported by LeafSpy | Note |
| :-- | :-- | :-- |
| sensor.leaf_ambient_temperature | °C (You must set this in the LeafSpy app; see instructions above.) | Unit adjustable in HA UI. |
| sensor.leaf_battery_capacity | Ah | |
| sensor.leaf_battery_conductance | % | Referred to as Hx in the LeafSpy manual. |
| sensor.leaf_battery_current | A | |
| sensor.leaf_battery_health | % | | 
| sensor.leaf_battery_state_of_charge | % | |
| sensor.leaf_battery_stat_of_charge_gids |  Gids | |
| sensor.leaf_battery_temperature | °C (You must set this in the LeafSpy app; see instructions above.) | Unit adjustable in HA UI. |
| sensor.leaf_battery_voltage | V | |
| sensor.leaf_charge_mode | --- | |
| sensor.leaf_charge_power | W | Not very accurate. For example, when charging via level 2 charging, it just guesses 6,000 W. |
| sensor.leaf_elevation | m | Unit adjustable in HA UI |
| sensor.leaf_front_wiper_status | --- | To get this information you may need to make a custom screen in LeafSpy to read wiper status. |
| sensor.leaf_motor_speed | RPM | |
| sensor.leaf_odometer | km (You must indicate in LeafSpy if your displayed car odometer is in mi; see instructions above.) | Unit later adjustable in HA UI. |
| sensor.leaf_phone_battery | % | |
| sensor.leaf_plug_status | --- | Reports "Not plugged", "Partial Plugged", or "Plugged." |
| sensor.leaf_sequence_number | --- | A number that increments with each report from LeafSpy. |
| sensor.leaf_speed | km/h | Unit adjustable in HA UI. |
| sensor.leaf_trip_number | --- | Tracks total number of trips taken. |
| sensor.leaf_vin | ---  | Car unique identifier. | 


[commits-shield]: https://img.shields.io/github/commit-activity/y/jesserockz/ha-leafspy.svg?style=for-the-badge
[commits]: https://github.com/jesserockz/ha-leafspy/commits/main
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/jesserockz/ha-leafspy.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Will%20Adler%20%40wtadler-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jesserockz/ha-leafspy.svg?style=for-the-badge
[releases]: https://github.com/jesserockz/ha-leafspy/releases
