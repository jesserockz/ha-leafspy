[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]](hacs)
![Project Maintenance][maintenance-shield]

[![Discord][discord-shield]][discord]
[![Community Forum][forum-shield]][forum]

_Component to integrate with [leafspy][leafspy]._

**This component will set up the following platforms.**

Platform | Description
-- | --
`device_tracker` | Track a Nissan Leaf using the Leaf Spy app.

![leafspy][leafspyimg]

{% if not installed %}
## Installation

1. Click install.
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "Leaf Spy".

{% endif %}


## Configuration is done in the UI

<!---->

***

[leafspy]: https://play.google.com/store/apps/details?id=com.Turbo3.Leaf_Spy_Pro
[commits-shield]: https://img.shields.io/github/commit-activity/y/jesserockz/ha-leafspy.svg?style=for-the-badge
[commits]: https://github.com/jesserockz/ha-leafspy/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[discord]: https://discord.gg/Qa5fW2R
[discord-shield]: https://img.shields.io/discord/330944238910963714.svg?style=for-the-badge
[leafspyimg]: leafspy.png
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/jesserockz/ha-leafspy.svg?style=for-the-badge
[maintenance-shield]: https://img.shields.io/badge/maintainer-Jesse%20Hills%20%40jesserockz-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/jesserockz/ha-leafspy.svg?style=for-the-badge
[releases]: https://github.com/jesserockz/ha-leafspy/releases
