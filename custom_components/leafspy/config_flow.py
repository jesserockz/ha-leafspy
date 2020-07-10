"""Config flow for Leaf Spy."""
import re
import secrets

from homeassistant import config_entries
from homeassistant.helpers.network import get_url

from .const import URL_LEAFSPY_PATH, CONF_SECRET, DOMAIN


class LeafSpyFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Set up Leaf Spy."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle a user initiated set up flow to create Leaf Spy webhook."""
        if self._async_current_entries():
            return self.async_abort(reason='one_instance_allowed')

        if user_input is None:
            return self.async_show_form(
                step_id='user',
            )

        secret = secrets.token_hex(8)

        url = get_url(self.hass, prefer_external = True, prefer_cloud = True)
        url = "{}{}".format(url, URL_LEAFSPY_PATH)
        url = re.sub(r"https?://", "", url)

        return self.async_create_entry(
            title="Leaf Spy",
            data={
                CONF_SECRET: secret
            },
            description_placeholders={
                'secret': secret,
                'url': url,
                'docs_url': 'https://www.home-assistant.io/components/leafspy/'
            }
        )
