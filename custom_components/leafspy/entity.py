from email import message
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.typing import StateType

from .models import (
    LeafspyEntityDescription,
    LeafspyMessage,
)
from .const import DOMAIN


class LeafspyEntity(RestoreEntity):
    """Representation of a leafspy entity."""

    entity_description: LeafspyEntityDescription
    leafspy_state: StateType

    def __init__(self, vin: str, entity_description: LeafspyEntityDescription) -> None:
        self.entity_description = entity_description
        self._vin = vin
        self._attr_unique_id = f"{vin}_{entity_description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, vin)},
            manufacturer="Nissan",
            model=vin.split("-")[0],
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, f"{DOMAIN}_update_device", self._handle_update
            )
        )

        if (state := await self.async_get_last_state()) is not None:
            self.leafspy_state = state.state

    @callback
    def _handle_update(self, data: LeafspyMessage):
        """Handle incoming message."""
        if data.VIN != self._vin:
            return

        self.leafspy_state = self.entity_description.state(data)
        self.async_write_ha_state()
