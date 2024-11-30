# leafspy

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]
![Project Maintenance][maintenance-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Component to integrate with [leafspy][leafspy]._

**This component will set up the following platforms.**

Platform | Description
-- | --
`device_tracker` | Track a Nissan Leaf using the Leaf Spy app. 
`sensor` | All data about the vehicle sent from Leaf Spy is displayed as independent sensors. They won't appear in Home Assistant until data is received.

![leafspy][leafspyimg]

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jesserockz&repository=ha-leafspy&category=integration)

1. Using the tool of choice open the directory (folder) for your HA configuration (where you find `configuration.yaml`).
2. If you do not have a `custom_components` directory (folder) there, you need to create it.
3. In the `custom_components` directory (folder) create a new folder called `leafspy`.
4. Download _all_ the files from the `custom_components/leafspy/` directory (folder) in this repository.
5. Place the files you downloaded in the new directory (folder) you created.
6. Restart Home Assistant
7. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Leaf Spy"

Using your HA configuration directory (folder) as a starting point you should now also have this:

```text
custom_components/leafspy/translations/en.json
custom_components/leafspy/__init__.py
custom_components/leafspy/config_flow.py
custom_components/leafspy/const.py
custom_components/leafspy/device_tracker.py
custom_components/leafspy/sensor.py
custom_components/leafspy/manifest.json
custom_components/leafspy/strings.json
```

## Configuration is done in the UI

### Android/iOS app configuration

Open the Leaf Spy app, go to `Menu` -> `Settings` and scroll down to `Server`. 
Change the following settings:
- `Enable`: Yes
- `Send Interval` can be whatever you prefer.
- `ID`: `<Car Name>`
- `PW`: secret generated when the integration was installed
- `Http` or `Https` depending on the access to your Home Assistant install.
- `URL`: webhook url generated when the integration was installed 
  - Note: **Do not** add http or https to the URL.

<!---->

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

***

[leafspy]: https://play.google.com/store/apps/details?id=com.Turbo3.Leaf_Spy_Pro
[commits-shield]: https://img.shields.io/github/commit-activity/y/jesserockz/ha-leafspy.svg?style=for-the-badge
[commits]: https://github.com/jesserockz/ha-leafspy/commits/main
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[leafspyimg]: leafspy.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jesserockz/ha-leafspy.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Will%20Adler%20%40wtadler-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jesserockz/ha-leafspy.svg?style=for-the-badge
[releases]: https://github.com/jesserockz/ha-leafspy/releases
