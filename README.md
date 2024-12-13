# LeafSpy integration for Home Assistant

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

<p align="center"><img src="leafspy.png" width="64"></p>

This Home Assistant component integrates with the LeafSpy [Android](https://play.google.com/store/apps/details?id=com.Turbo3.Leaf_Spy_Pro&hl=en_US) and [iOS](https://apps.apple.com/us/app/leafspy-pro/id967376861). Plug a Bluetooth OBD2 adapter (like [this one](https://www.amazon.com/gp/product/B0755N61PW/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)) into your Nissan Leaf. Open up LeafSpy and pair your phone with the adapter. It will then read information from your car. This integration will allow your phone to submit that info to Home Assistant.

## Installation and configuration

1. [Install HACS](https://www.hacs.xyz/docs/use/configuration/basic/).
2. Add this to HACS as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/) by pressing this button.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jesserockz&repository=ha-leafspy&category=integration)

3. Restart Home Assistant
4. In the UI go to "Configuration" -> "Integrations" click "+" and search for "Leaf Spy"
5. Configure your Leaf Spy app using the information that the integration displays on screen. If you don't have the app in front of you, copy down the on-screen information; the generated password will only be shown this once. If you don't copy it down, you'll have to uninstall the integration, restart, and reinstall.

## Entities
_See [LeafSpy manual](https://leafspy.com/wp-content/uploads/2024/04/LeafSpy-Help-1.5.0.pdf#page=70) for more details on the entities it sends._

### Device tracker
| Entity ID | Entity Name | Description |
| :-- | :-: | :-- |
| device_tracker.leaf | Leaf | Tracks latitude, longitude, GPS accuracy, and battery level |

### Binary sensor
| Entity ID | Entity Name | Description |
| :-- | :-: | :-- |
| binary_sensor.leaf_power | Leaf power | Indicates whether car is turned on |

### Sensors
| Entity ID | Entity Name | Description |
| :-- | :-: | :-- |
| sensor.leaf_ambient_temperature | Leaf ambient temperature | Indicates temperature outside of car |
| sensor.leaf_battery_capacity | Leaf battery capacity | Indicates battery capacity (Ah) |
| ... | ... | ... |

[commits-shield]: https://img.shields.io/github/commit-activity/y/jesserockz/ha-leafspy.svg?style=for-the-badge
[commits]: https://github.com/jesserockz/ha-leafspy/commits/main
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/jesserockz/ha-leafspy.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Will%20Adler%20%40wtadler-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jesserockz/ha-leafspy.svg?style=for-the-badge
[releases]: https://github.com/jesserockz/ha-leafspy/releases
