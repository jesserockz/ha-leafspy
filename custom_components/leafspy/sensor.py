from homeassistant.components.sensor import SensorEntity
from homeassistant.const import Platform
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers import entity_registry as er, device_registry as dr

from .entity import LeafspyEntity
from .models import LeafspyMessage, LeafspySensorEntityDescription
from .const import SENSORS, DOMAIN


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
            if entry.domain != Platform.SENSOR or entry.disabled_by:
                continue
            for description in SENSORS:
                if entry.unique_id.endswith(description.key):
                    entities.append(LeafspySensor(vin, description))
                    break

        async_add_entities(entities)

    @callback
    def handle_new_device(message: LeafspyMessage):
        vin = message.VIN
        print(f"Adding for vin: {vin}")
        entities = []
        for description in SENSORS:
            if (
                entity_registry.async_get(f"{Platform.SENSOR}.{vin}_{description.key}")
                is None
            ):
                LeafspySensor(vin, description)
        async_add_entities(entities)

    async_dispatcher_connect(
        hass,
        f"{DOMAIN}_new_device",
        handle_new_device,
    )


class LeafspySensor(LeafspyEntity, SensorEntity):
    """Represent a leafspy sensor."""

    entity_description: LeafspySensorEntityDescription

    def __init__(self, vin: str, entity_description: LeafspySensorEntityDescription):
        """Initialize the sensor."""
        super().__init__(vin, entity_description)
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"

    @property
    def native_value(self) -> StateType:
        return self.leafspy_state
