"""Sensor platform that adds support for Leaf Spy."""
import logging
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
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
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers import device_registry
from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class LeafSpySensorDescription(SensorEntityDescription):
    """Describes Leaf Spy sensor."""
    value_fn: Callable[[dict], Any] = field(default=lambda data: None)
    transform_fn: Callable[[Any], Any] = field(default=lambda x: x)
    unit_fn: Callable[[dict], str] = field(default=lambda data: None)

def _get_temperature_unit(data):
    """Determine the temperature unit based on Tunits."""
    tunits = data.get("Tunits", "").lower()
    if tunits == "f":
        return UnitOfTemperature.FAHRENHEIT
    return UnitOfTemperature.CELSIUS

SENSOR_TYPES = [
    LeafSpySensorDescription(
        key="phone battery",
        translation_key="phone_battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("DevBat"),
    ),
    LeafSpySensorDescription(
        key="battery gids",
        translation_key="battery_gids",
        native_unit_of_measurement="Gids",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Gids"),
        icon="mdi:battery",
    ),
    LeafSpySensorDescription(
        key="elevation",
        translation_key="elevation",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Elv"),
        transform_fn=lambda x: int(round(float(x), 0)) if x is not None else None,
        icon="mdi:elevation-rise",
    ),
    LeafSpySensorDescription(
        key="sequence number",
        translation_key="sequence_number",
        value_fn=lambda data: data.get("Seq"),
        icon="mdi:numeric",
    ),
    LeafSpySensorDescription(
        key="trip number",
        translation_key="trip_number",
        value_fn=lambda data: data.get("Trip"),
        icon="mdi:road-variant",
    ),
    LeafSpySensorDescription(
        key="odometer",
        translation_key="odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("Odo"),
        transform_fn=lambda x: int(float(x)) if x is not None else None,
        icon="mdi:counter",
    ),
    LeafSpySensorDescription(
        key="battery state of charge",
        translation_key="state_of_charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("SOC"),
        transform_fn=lambda x: int(round(float(x), 0)) if x is not None else None,
    ),
    LeafSpySensorDescription(
        key="battery capacity",
        translation_key="battery_capacity",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("AHr"),
        transform_fn=lambda x: float(x) if x is not None else None,
        native_unit_of_measurement="Ah",
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery temperature",
        translation_key="battery_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("BatTemp"),
        transform_fn=lambda x: float(x) if x is not None else None,
        unit_fn=_get_temperature_unit,
        icon="mdi:thermometer",
    ),
    LeafSpySensorDescription(
        key="ambient temperature",
        translation_key="ambient_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Amb"),
        transform_fn=lambda x: float(x) if x is not None else None,
        unit_fn=_get_temperature_unit,
        icon="mdi:sun-thermometer",
    ),
    LeafSpySensorDescription(
        key="charge power",
        translation_key="charge_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("ChrgPwr"),
    ),
    LeafSpySensorDescription(
        key="front wiper",
        translation_key="front_wiper",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda data: {
            80: "High",
            40: "Low",
            20: "Switch",
            10: "Intermittent",
            8: "Stopped"
        }.get(int(data.get("Wpr")), "unknown"),
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
        key="plug",
        translation_key="plug",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda data: {
            0: "Not plugged",
            1: "Partial plugged",
            2: "Plugged"
        }.get(int(data.get("PlugState")), "unknown"),
        icon="mdi:power-plug",
        options=[
            "Not plugged",
            "Partial plugged",
            "Plugged",
            "unknown"
        ]
    ),
    LeafSpySensorDescription(
        key="charge mode",
        translation_key="charge_mode",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda data: {
            0: "Not charging",
            1: "Level 1 charging",
            2: "Level 2 charging",
            3: "Level 3 quick charging"
        }.get(int(data.get("ChrgMode")), "unknown"),
        icon="mdi:battery-charging-wireless",
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
        value_fn=lambda data: data.get("VIN"),
        icon="mdi:identifier",
    ),
    LeafSpySensorDescription(
        key="temperature units",
        translation_key="temperature_units",
        value_fn=lambda data: data.get("Tunits"),
        icon="mdi:temperature-celsius",
    ),
    LeafSpySensorDescription(
        key="motor speed",
        translation_key="motor_speed",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("RPM"),
        icon="mdi:engine",
    ),
    LeafSpySensorDescription(
        key="battery health",
        translation_key="battery_health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("SOH"),
        transform_fn=lambda x: float(x) if x is not None else None,
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery conductance",
        translation_key="battery_conductance",
        native_unit_of_measurement='Hx',
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Hx"),
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="speed",
        translation_key="speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Speed"),
    ),
    LeafSpySensorDescription(
        key="battery voltage",
        translation_key="battery_voltage",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("BatVolts"),
    ),
    LeafSpySensorDescription(
        key="battery current",
        translation_key="battery_current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("BatAmps"),
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

            # Create and update sensors for each description
            for description in SENSOR_TYPES:
                sensor_id = f"{dev_id}_{description.key}"
                value = description.value_fn(message)
                _LOGGER.debug("Sensor '%s': Raw data=%s, Parsed value=%s", description.key, message, value)

                value = description.transform_fn(value)
                _LOGGER.debug("Sensor '%s': Transformed value=%s", description.key, value)

                if value is not None:
                    sensor = hass.data[DOMAIN]['sensors'].get(sensor_id)
                    
                    # Dynamically update temperature unit if applicable
                    sensor_description = description
                    if description.unit_fn:
                        unit = description.unit_fn(message)
                        if unit:
                            sensor_description = replace(description, 
                                native_unit_of_measurement=unit)

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



class LeafSpySensor(SensorEntity, RestoreEntity):
    """Representation of a Leaf Spy sensor."""

    def __init__(self, device_id: str, description: LeafSpySensorDescription, initial_value):
        """Initialize the sensor."""
        self._device_id = device_id
        self._value = initial_value
        self.entity_description = description

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device_id}_{self.entity_description.key}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Leaf {self.entity_description.key}"

    @property
    def native_value(self):
        """Return the sensor's value."""
        return self._value

    @property
    def device_info(self):
        """Return device information."""
        return {
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

        # Add this log line to confirm the method is being called
        _LOGGER.debug(f"async_added_to_hass called for {self.name}")

        # Retrieve the last known state
        last_state = await self.async_get_last_state()
        if last_state:
            # Log the restored state before transforming
            _LOGGER.debug(f"Restored state for {self.name}: {last_state.state}")

            try:
                transform_fn = self.entity_description.transform_fn
                self._value = transform_fn(last_state.state)
                self.async_write_ha_state()  # Make sure the restored state is written
            except (ValueError, TypeError):
                _LOGGER.warning(f"Could not restore state for {self.name}")
