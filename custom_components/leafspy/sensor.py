"""Sensor platform that adds support for Leaf Spy."""
import logging
from dataclasses import dataclass, field
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

SENSOR_TYPES = [
    LeafSpySensorDescription(
        key="phone battery",
        translation_key="device_battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("DevBat"),
    ),
    LeafSpySensorDescription(
        key="Gids",
        translation_key="gids",
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
        key="sequence",
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
        key="mileage",
        translation_key="odometer",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda data: data.get("Odo"),
        transform_fn=lambda x: int(float(x)) if x is not None else None,
        icon="mdi:counter",
    ),
    LeafSpySensorDescription(
        key="battery level (SOC)",
        translation_key="state_of_charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("SOC"),
        transform_fn=lambda x: round(float(x), 2) if x is not None else None,
        transform_fn=lambda x: float(x) if x is not None else None,
    ),
    LeafSpySensorDescription(
        key="capacity (AHr)",
        translation_key="AHr_capacity",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("AHr"),
        transform_fn=lambda x: float(x) if x is not None else None,
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
        icon="mdi:sun-thermometer",
    ),
    LeafSpySensorDescription(
        key="charge power",
        translation_key="charge_power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("ChrgPwr"),
        icon="mdi:lightning-bolt",
    ),
    LeafSpySensorDescription(
        key="front wiper",
        translation_key="front_wiper_status",
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
        key="plug state",
        translation_key="plug_state",
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
        translation_key="vehicle_identification_number",
        value_fn=lambda data: data.get("VIN"),
        icon="mdi:identifier",
    ),
    LeafSpySensorDescription(
        key="power switch",
        translation_key="power_switch_state",
        value_fn=lambda data: data.get("PwrSw"),
        icon="mdi:power",
    ),
    LeafSpySensorDescription(
        key="temperature units",
        translation_key="temperature_units",
        value_fn=lambda data: data.get("Tunits"),
        icon="mdi:temperature-celsius",
    ),
    LeafSpySensorDescription(
        key="motor rpm",
        translation_key="motor_rpm",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("RPM"),
        icon="mdi:engine",
    ),
    LeafSpySensorDescription(
        key="battery health (SOH)",
        translation_key="state_of_health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("SOH"),
        transform_fn=lambda x: float(x) if x is not None else None,
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="Hx",
        translation_key="hx_value",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("Hx"),
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="speed",
        translation_key="vehicle_speed",
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
            _LOGGER.debug("Incoming message: %s", message)
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
                    if sensor is not None:
                        sensor.update_state(value)
                    else:
                        sensor = LeafSpySensor(dev_id, description, value)
                        hass.data[DOMAIN]['sensors'][sensor_id] = sensor
                        async_add_entities([sensor])

        except Exception as err:
            _LOGGER.error("Error processing Leaf Spy message: %s", err)

    async_dispatcher_connect(hass, DOMAIN, _process_message)
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

    def update_state(self, new_value):
        """Update the sensor state."""
        self._value = new_value
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Restore last known state."""
        await super().async_added_to_hass()
        
        last_state = await self.async_get_last_state()
        if last_state:
            try:
                transform_fn = self.entity_description.transform_fn
                self._value = transform_fn(last_state.state)
            except (ValueError, TypeError):
                _LOGGER.warning(f"Could not restore state for {self.name}")
