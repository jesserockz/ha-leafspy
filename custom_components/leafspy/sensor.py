"""Sensor platform that adds support for Leaf Spy."""
import logging
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    RestoreSensor,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfLength,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import device_registry
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class LeafSpySensorDescription(SensorEntityDescription):
    """Describes Leaf Spy sensor."""
    transform_fn: Callable[[dict], Any] = field(default=lambda x: x)

def _safe_round(x, digits=2):
    try:
        x = float(x)
        if digits==0:
            return int(x)
        else:
            return round(x, digits)
    except (ValueError, TypeError):
        return None
    
def _transform_hx(x):
    # if x > 100, divide by 102.4, otherwise return
    # takes care of iOS LeafSpy bug until patched
    x = float(x)
    if x > 100:
        return x / 102.4
    else:
        return x


SENSOR_TYPES = [
    LeafSpySensorDescription(
        key="phone_battery",
        translation_key="DevBat",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="battery_gids",
        translation_key="Gids",
        native_unit_of_measurement="Gids",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    LeafSpySensorDescription(
        key="elevation",
        translation_key="Elv",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
        icon="mdi:elevation-rise",
    ),
    LeafSpySensorDescription(
        key="sequence_number",
        translation_key="Seq",
        icon="mdi:numeric",
    ),
    LeafSpySensorDescription(
        key="trip_number",
        translation_key="Trip",
        icon="mdi:road-variant",
    ),
    LeafSpySensorDescription(
        key="odometer",
        translation_key="Odo",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        transform_fn=lambda x: _safe_round(x, 0),
        icon="mdi:counter",
    ),
    LeafSpySensorDescription(
        key="battery_state_of_charge",
        translation_key="SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
    ),
    LeafSpySensorDescription(
        key="battery_capacity",
        translation_key="Ahr",
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
        native_unit_of_measurement="Ah",
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery_temperature",
        translation_key="BatTemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="ambient_temperature",
        translation_key="Amb",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sun-thermometer",
    ),
    LeafSpySensorDescription(
        key="charge_power",
        translation_key="ChrgPwr",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="front_wiper",
        translation_key="Wpr",
        device_class=SensorDeviceClass.ENUM,
        transform_fn=lambda x: {
            80: "High",
            40: "Low",
            20: "Switch",
            10: "Intermittent",
            8: "Stopped"
        }.get(int(x), "unknown"),
        icon="mdi:wiper",
        options=[
            "High",
            "Low",
            "Switch",
            "Intermittent",
            "Stopped",
            "unknown"
        ]
    ),
    LeafSpySensorDescription(
        key="plug_state",
        translation_key="PlugState",
        device_class=SensorDeviceClass.ENUM,
        transform_fn=lambda x: {
            0: "Not plugged",
            1: "Partial plugged",
            2: "Plugged"
        }.get(int(x), "unknown"),
        icon="mdi:power-plug",
        options=[
            "Not plugged",
            "Partial plugged",
            "Plugged",
            "unknown"
        ]
    ),
    LeafSpySensorDescription(
        key="charge_mode",
        translation_key="ChrgMode",
        device_class=SensorDeviceClass.ENUM,
        transform_fn=lambda x: {
            0: "Not charging",
            1: "Level 1 charging",
            2: "Level 2 charging",
            3: "Level 3 quick charging"
        }.get(int(x), "unknown"),
        icon="mdi:ev-station",
        options=[
            "Not charging",
            "Level 1 charging",
            "Level 2 charging", 
            "Level 3 quick charging",
            "unknown"
        ]
    ),
    LeafSpySensorDescription(
        key="VIN",
        translation_key="VIN",
        icon="mdi:identifier",
    ),
    LeafSpySensorDescription(
        key="motor_speed",
        translation_key="RPM",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:engine",
    ),
    LeafSpySensorDescription(
        key="battery_health",
        translation_key="SOH",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery_conductance",
        translation_key="Hx",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(_transform_hx(x), 2),
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="speed",
        translation_key="Speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="battery_voltage",
        translation_key="BatVolts",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
    ),
    LeafSpySensorDescription(
        key="battery_current",
        translation_key="BatAmps",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
]

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> bool:
    """Set up Leaf Spy sensors based on a config entry."""
    if 'sensors' not in hass.data[DOMAIN]:
        hass.data[DOMAIN]['sensors'] = {}

    async def _process_message(context, message):
        """Process incoming sensor messages."""
        try:
            if 'VIN' not in message:
                return

            dev_id = slugify(f'leaf_{message["VIN"]}')

            _LOGGER.debug(f"Incoming message: {message}")

            # Create and update sensors for each description
            for description in SENSOR_TYPES:
                sensor_id = f"{dev_id}_{description.key}"
                value = message.get(description.translation_key, None)

                _LOGGER.debug(f"Sensor {description.key}: Initial value={value}")

                if description.transform_fn:
                    value = description.transform_fn(value)
                    _LOGGER.debug(f"Sensor {description.key}: Transformed value={value}")

                if value is not None:
                    sensor = hass.data[DOMAIN]['sensors'].get(sensor_id)
                    
                    sensor_description = description

                    if sensor is not None:
                        # Update existing sensor
                        sensor.entity_description = sensor_description
                        sensor.update_state(value)
                    else:
                        # Add a new sensor
                        sensor = LeafSpySensor(dev_id, sensor_description, value)
                        hass.data[DOMAIN]['sensors'][sensor_id] = sensor
                        async_add_entities([sensor])

                        # Add a log to confirm the sensor is being registered
                        _LOGGER.debug(f"Registered sensor: {sensor.name} with initial value: {value}")

        except Exception as err:
            _LOGGER.error("Error processing Leaf Spy message: %s", err)
            _LOGGER.exception("Full traceback")

    async_dispatcher_connect(hass, DOMAIN, _process_message)
    
    # Restore previously loaded sensors
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
        for description in SENSOR_TYPES:
            sensor_id = f"{dev_id}_{description.key}"
            sensor = LeafSpySensor(dev_id, description, None)  # Initializing with None
            hass.data[DOMAIN]['sensors'][sensor_id] = sensor
            entities.append(sensor)

    async_add_entities(entities)
    return True



class LeafSpySensor(RestoreSensor):
    """Representation of a Leaf Spy sensor."""

    def __init__(self, device_id: str, description: LeafSpySensorDescription, initial_value):
        """Initialize the sensor."""
        self._device_id = device_id
        self._value = initial_value
        self._attr_has_entity_name = True
        self.entity_description = description

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device_id}_{self.entity_description.key}"


    @property
    def translation_key(self):
        """Return the translation key."""
        return self.entity_description.translation_key
    
    @property
    def native_value(self):
        """Return the sensor's value."""
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
        """Update the sensor state."""
        self._value = new_value
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore last known state."""
        await super().async_added_to_hass()

        _LOGGER.debug(f"async_added_to_hass called for {self.name}")

        # Retrieve the last known state
        last_state = await self.async_get_last_sensor_data()
        if last_state:
            # Log the restored state before transforming
            _LOGGER.debug(f"Restored state for {self.name}: {last_state.native_value}")

            try:
                self._value = last_state.native_value
                self.async_write_ha_state()  # Make sure the restored state is written
            except (ValueError, TypeError):
                _LOGGER.warning(f"Could not restore state for {self.name}")
