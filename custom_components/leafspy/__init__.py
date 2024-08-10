"""Support for Leaf Spy."""
import asyncio
import hmac
import logging

from aiohttp.web import Response
import voluptuous as vol

from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect, async_dispatcher_send

from .config_flow import CONF_SECRET, DOMAIN, URL_LEAFSPY_PATH
from .device_tracker import async_handle_message

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["device_tracker"]


async def async_setup(hass, config):
    """Initialize Leaf Spy component."""
    hass.data[DOMAIN] = {
        'devices': {},
        'unsub': None,
    }
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Leaf Spy entry."""
    secret = entry.data[CONF_SECRET]

    context = LeafSpyContext(hass, secret)

    hass.data[DOMAIN]['context'] = context

    hass.http.register_view(LeafSpyView())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    hass.data[DOMAIN]['unsub'] = \
        async_dispatcher_connect(hass, DOMAIN, async_handle_message)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    hass.data[DOMAIN]["unsub"]()

    return True


class LeafSpyContext:
    """Hold the current Leaf Spy context."""

    def __init__(self, hass, secret):
        """Initialize a Leaf Spy context."""
        self.hass = hass
        self.secret = secret
        self._pending_msg = []

    @callback
    def set_async_see(self, func):
        """Set a new async_see function."""
        self.async_see = func
        for msg in self._pending_msg:
            func(**msg)
        self._pending_msg.clear()

    # pylint: disable=method-hidden
    @callback
    def async_see(self, **data):
        """Send a see message to the device tracker."""
        self._pending_msg.append(data)


class LeafSpyView(HomeAssistantView):
    """Handle incoming Leaf Spy requests."""

    url = URL_LEAFSPY_PATH
    name = "api:leafspy"
    requires_auth = False

    async def get(self, request):
        """Handle leafspy call."""
        hass = request.app['hass']
        context = hass.data[DOMAIN]['context']

        try:
            message = request.query
            if not hmac.compare_digest(message['pass'], context.secret):
                raise Exception("Invalid password")

            async_dispatcher_send(DOMAIN, hass, context, message)

            return Response(status=200, text='"status":"0"')
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error processing leafspy webhook")
            return Response(status=500, text="")
