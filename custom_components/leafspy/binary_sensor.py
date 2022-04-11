from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import Platform
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .entity import LeafspyEntity
from .models import (
    LeafspyBinarySensorEntityDescription,
    LeafspyMessage,
)
from .const import BINARY_SENSORS, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up leafspy sensors."""

    entities = []
    entity_registry = er.async_get(hass)
    entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

    if entries:
        device_registry = dr.async_get(hass)
        device = device_registry.async_get(entries[0].device_id)

        for identifier in device.identifiers:
            if identifier[0] == DOMAIN:
                vin = identifier[1]

        for entry in entries:
            if entry.domain != Platform.BINARY_SENSOR or entry.disabled_by:
                continue
            for description in BINARY_SENSORS:
                if entry.unique_id.endswith(description.key):
                    entities.append(LeafspyBinarySensor(vin, description))
                    break

        async_add_entities(entities)

    @callback
    def handle_new_device(message: LeafspyMessage):
        vin = message.VIN
        async_add_entities(
            LeafspyBinarySensor(vin, entity_description)
            for entity_description in BINARY_SENSORS
        )

    async_dispatcher_connect(
        hass,
        f"{DOMAIN}_new_device",
        handle_new_device,
    )


class LeafspyBinarySensor(LeafspyEntity, BinarySensorEntity):
    """Represent a leafspy binary sensor."""

    entity_description: LeafspyBinarySensorEntityDescription

    def __init__(
        self, vin: str, entity_description: LeafspyBinarySensorEntityDescription
    ):
        """Initialize the binary sensor."""
        super().__init__(vin, entity_description)
        self.entity_id = f"{Platform.BINARY_SENSOR}.{self._attr_unique_id}"

    @property
    def is_on(self) -> bool:
        return self.leafspy_state
