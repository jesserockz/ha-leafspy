"""Support for Leaf Spy."""
import asyncio
import hmac
import logging

from aiohttp.web import Response, Request

from homeassistant.components.http.view import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .models import LeafspyMessage
from .config_flow import CONF_SECRET, DOMAIN, URL_LEAFSPY_PATH

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    # Platform.DEVICE_TRACKER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Leaf Spy entry."""
    secret = entry.data[CONF_SECRET]

    device_registry = dr.async_get(hass)

    hass.http.register_view(LeafSpyView(hass, secret, entry, device_registry))

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    # hass.data[DOMAIN]["unsub"] = hass.helpers.dispatcher.async_dispatcher_connect(
    #     DOMAIN, async_handle_message
    # )

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
    # if unload_ok:
    #     hass.data[DOMAIN].pop(entry.entry_id)

    # hass.data[DOMAIN]["unsub"]()

    return True


class LeafSpyView(HomeAssistantView):
    """Handle incoming Leaf Spy requests."""

    name = "api:leafspy"
    requires_auth = False

    def __init__(
        self,
        hass: HomeAssistant,
        secret: str,
        entry: ConfigEntry,
        device_registry: dr.DeviceRegistry,
    ):
        """Initialize the Leaf Spy view."""
        self.hass = hass
        self.secret = secret
        self.entry = entry
        self.device_registry = device_registry
        self.url = f"{URL_LEAFSPY_PATH}{self.entry.data[CONF_SECRET]}"

    async def get(self, request: Request):
        """Handle leafspy call."""
        try:
            message = request.query
            message = dict(message)
            if not hmac.compare_digest(message.pop("pass"), self.secret):
                raise Exception("Invalid password")

            message = LeafspyMessage(**message)
            device = self.device_registry.async_get_or_create(
                config_entry_id=self.entry.entry_id,
                identifiers={(DOMAIN, message.VIN)},
                manufacturer="Nissan",
                name=message.user,
                model=message.VIN.split("-")[0],
            )

            entity_registry = er.async_get(self.hass)
            entities = er.async_entries_for_device(entity_registry, device.id)

            if entities:
                async_dispatcher_send(self.hass, f"{DOMAIN}_update_device", message)
            else:
                async_dispatcher_send(self.hass, f"{DOMAIN}_new_device", message)
                async_dispatcher_send(self.hass, f"{DOMAIN}_update_device", message)

            return Response(status=200, text='"status":"0"')
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error processing leafspy webhook")
            return Response(status=500, text="")
