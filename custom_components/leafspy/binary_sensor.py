"""Binary sensor platform that adds support for Leaf Spy."""
import logging
from dataclasses import dataclass, field
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers import device_registry
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class LeafSpyBinarySensorDescription(BinarySensorEntityDescription):
    """Describes Leaf Spy binary sensor."""
    transform_fn: Callable[[dict], Any] = field(default=lambda x: x)

BINARY_SENSOR_TYPES = [
    LeafSpyBinarySensorDescription(
        key="power",
        translation_key="PwrSw",
        device_class=BinarySensorDeviceClass.POWER,
        transform_fn=lambda x: x == '1',
        icon="mdi:power",
    )
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> bool:
    """Set up Leaf Spy binary sensors based on a config entry."""
    if 'binary_sensors' not in hass.data[DOMAIN]:
        hass.data[DOMAIN]['binary_sensors'] = {}

    async def _process_message(context, message):
        """Process incoming sensor messages."""
        try:
            _LOGGER.debug("Incoming message: %s", message)
            if 'VIN' not in message:
                return

            dev_id = slugify(f'leaf_{message["VIN"]}')

            # Create and update binary sensors for each description
            for description in BINARY_SENSOR_TYPES:
                sensor_id = f"{dev_id}_{description.key}"
                # value = description.value_fn(message)
                value = message.get(description.translation_key, None)
                _LOGGER.debug(f"Binary sensor {description.key}: Initial value={value}")

                if description.transform_fn:
                    value = description.transform_fn(value)
                    _LOGGER.debug(f"Binary sensor {description.key}: Transformed value={value}")

                if value is not None:
                    sensor = hass.data[DOMAIN]['binary_sensors'].get(sensor_id)

                    sensor_description = description

                    if sensor is not None:
                        sensor.entity_description = sensor_description
                        sensor.update_state(value)
                    else:
                        sensor = LeafSpyBinarySensor(dev_id, description, value)
                        hass.data[DOMAIN]['binary_sensors'][sensor_id] = sensor
                        async_add_entities([sensor])

                        _LOGGER.debug(f"Registered sensor: {sensor.name} with initial value: {value}")

        except Exception as err:
            _LOGGER.error("Error processing Leaf Spy message: %s", err)

    async_dispatcher_connect(hass, DOMAIN, _process_message)

    # Restore previously loaded devices
    dev_reg = device_registry.async_get(hass)
    dev_ids = {
        identifier[1]
        for device in dev_reg.devices.values()
        for identifier in device.identifiers
        if identifier[0] == DOMAIN
    }

    if not dev_ids:
        return True

    entities = []
    for dev_id in dev_ids:

        # For each device ID, recreate the sensor entities
        for description in BINARY_SENSOR_TYPES:
            sensor_id = f"{dev_id}_{description.key}"
            sensor = LeafSpyBinarySensor(dev_id, description, False)
            hass.data[DOMAIN]['binary_sensors'][sensor_id] = sensor
            entities.append(sensor)
    async_add_entities(entities)
    return True


class LeafSpyBinarySensor(BinarySensorEntity, RestoreEntity):
    """Representation of a Leaf Spy binary sensor."""

    def __init__(self, device_id: str, description: LeafSpyBinarySensorDescription, initial_value):
        """Initialize the binary sensor."""
        self._device_id = device_id
        self._value = initial_value
        self._attr_has_entity_name = True
        self.entity_description = description

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device_id}_{self.entity_description.key}"

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._value

    @property
    def device_info(self):
        """Return device information."""
        return {
            "name": "Leaf",
            "identifiers": {(DOMAIN, self._device_id)},
        }
    
    @property
    def should_poll(self) -> bool:
        """Disable polling for this sensor."""
        return False


    def update_state(self, new_value):
        """Update the binary sensor state."""
        self._value = new_value
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore last known state."""
        await super().async_added_to_hass()
        
        last_state = await self.async_get_last_state()
        if last_state:
            try:
                self._value = last_state.state
            except (ValueError, TypeError):
                _LOGGER.warning(f"Could not restore state for {self.name}")
        
        # Add this log line to confirm the method is being called
        _LOGGER.debug(f"async_added_to_hass called for {self.name}")
