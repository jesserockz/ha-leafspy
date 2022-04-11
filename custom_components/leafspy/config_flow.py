"""Config flow for Leaf Spy."""
import re
import secrets
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.network import get_url

from .const import URL_LEAFSPY_PATH, CONF_SECRET, DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_NAME): str})


class LeafSpyFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up Leaf Spy."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle a user initiated set up flow to create Leaf Spy webhook."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=DATA_SCHEMA,
            )

        await self.async_set_unique_id(user_input[CONF_NAME])
        self._abort_if_unique_id_configured()

        secret = secrets.token_hex(8)

        url = get_url(self.hass, prefer_external=True, prefer_cloud=True)
        url = f"{url}{URL_LEAFSPY_PATH}{secret}"
        url = re.sub(r"https?://", "", url)

        return self.async_create_entry(
            title=user_input[CONF_NAME],
            data={CONF_SECRET: secret},
            description_placeholders={
                "name": user_input[CONF_NAME],
                "secret": secret,
                "url": url,
                "docs_url": "https://github.com/jesserockz/ha-leafspy/",
            },
        )
