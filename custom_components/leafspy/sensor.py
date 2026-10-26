"""Sensor platform that adds support for Leaf Spy."""
import logging
from dataclasses import dataclass, field
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
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import slugify

from .const import DOMAIN
from .util import loggable_value, redact_message

_LOGGER = logging.getLogger(__name__)

@dataclass(frozen=True)
class LeafSpySensorDescription(SensorEntityDescription):
    """Describes Leaf Spy sensor."""
    transform_fn: Callable[[dict], Any] = field(default=lambda x: x)
    leafspy_key: str = field(default=None)

def _safe_round(x, digits=2):
    try:
        x = float(x)
        if digits==0:
            return int(x)
        else:
            return round(x, digits)
    except (ValueError, TypeError):
        return None
    
def _temperature_unit(message):
    """Return the temperature unit Leaf Spy used for this message."""
    if str(message.get("Tunits", "")).strip().upper() == "F":
        return UnitOfTemperature.FAHRENHEIT
    return UnitOfTemperature.CELSIUS

def _transform_hx(x):
    # if x > 100, divide by 102.4, otherwise return
    # takes care of iOS LeafSpy bug until patched
    x = float(x)
    if x > 100:
        return x / 102.4
    else:
        return x

def _correct_swapped_battery_values(message):
    """Return the message with BatVolts and BatAmps swapped back if they arrived swapped."""
    # The iOS app sometimes sends BatVolts and BatAmps swapped while the car is
    # off (e.g. BatVolts=-0.00, BatAmps=392.00), until patched. Swap them back
    # only when the values themselves look swapped, so correct senders are
    # untouched. A Leaf pack never reads below ~200 V once it reports, and
    # current stays within about -400..+200 A, so a "voltage" under 200 V next
    # to a "current" of 200-450 can only be a swap. Negative or small currents
    # and two zeros are never swapped; a missing or unparseable field means no swap.
    volts = _safe_round(message.get("BatVolts"))
    amps = _safe_round(message.get("BatAmps"))
    if volts is None or amps is None:
        return message
    if volts < 200 and 200 <= amps <= 450:
        _LOGGER.debug("Battery voltage and current arrived swapped; correcting")
        message = dict(message)
        message["BatVolts"], message["BatAmps"] = message["BatAmps"], message["BatVolts"]
    return message

def _drop_impossible_ambient(message):
    """Return the message without Amb if it isn't a plausible outside temperature."""
    # After reconnecting with the car off, Leaf Spy can repeat a stale outside
    # temperature (e.g. 188.6), and a mismatched Convert Outside Temperature
    # setting can convert it twice (e.g. 162.5 °F on a 72 °F day). Drop values
    # no weather produces, so the sensor keeps its last reading.
    amb = message.get("Amb")
    if amb is None:
        return message
    value = _safe_round(amb)
    if _temperature_unit(message) == UnitOfTemperature.FAHRENHEIT:
        low, high = -58, 140
    else:
        low, high = -50, 60
    if value is not None and low <= value <= high:
        return message
    _LOGGER.debug("Ignoring implausible outside temperature: %s", amb)
    message = dict(message)
    del message["Amb"]
    return message

def _transform_odometer(x):
    # Leaf Spy sends Odo=0 when it can't read the odometer (e.g. while the
    # car is off or charging). Treat that as "no reading": a drop to 0 on a
    # TOTAL_INCREASING sensor would be recorded as a meter reset.
    value = _safe_round(x, 0)
    if value is None or value <= 0:
        return None
    return value

def _nonzero(value):
    # Once the car has been off a while, Leaf Spy sends 0 for battery fields it
    # can no longer read (SOH, Gids, AHr, Hx). A real pack never reports 0
    # there, so treat it as "no reading" and keep the last value.
    if value is None or value == 0:
        return None
    return value


SENSOR_TYPES = [
    LeafSpySensorDescription(
        key="ambient_temperature",
        leafspy_key="Amb",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sun-thermometer",
    ),
    LeafSpySensorDescription(
        key="battery_capacity",
        leafspy_key="AHr",
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _nonzero(_safe_round(x, 2)),
        native_unit_of_measurement="Ah",
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery_conductance",
        leafspy_key="Hx",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _nonzero(_safe_round(_transform_hx(x), 2)),
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery_current",
        leafspy_key="BatAmps",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="battery_health",
        leafspy_key="SOH",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _nonzero(_safe_round(x, 2)),
        icon="mdi:battery-heart-variant",
    ),
    LeafSpySensorDescription(
        key="battery_state_of_charge",
        leafspy_key="SOC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
    ),
    LeafSpySensorDescription(
        key="battery_gids",
        leafspy_key="Gids",
        native_unit_of_measurement="Gids",
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _nonzero(_safe_round(x, 0)),
        icon="mdi:battery",
    ),
    LeafSpySensorDescription(
        key="battery_temperature",
        leafspy_key="BatTemp",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="battery_voltage",
        leafspy_key="BatVolts",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
    ),
    LeafSpySensorDescription(
        key="charge_mode",
        leafspy_key="ChrgMode",
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
        key="charge_power",
        leafspy_key="ChrgPwr",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="elevation",
        leafspy_key="Elv",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        transform_fn=lambda x: _safe_round(x, 2),
        icon="mdi:elevation-rise",
    ),
    LeafSpySensorDescription(
        key="front_wiper",
        leafspy_key="Wpr",
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
        key="motor_speed",
        leafspy_key="RPM",
        native_unit_of_measurement="RPM",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:engine",
    ),
    LeafSpySensorDescription(
        key="odometer",
        leafspy_key="Odo",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.TOTAL_INCREASING,
        transform_fn=_transform_odometer,
        icon="mdi:counter",
    ),
    LeafSpySensorDescription(
        key="phone_battery",
        leafspy_key="DevBat",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="plug_state",
        leafspy_key="PlugState",
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
        key="sequence_number",
        leafspy_key="Seq",
        icon="mdi:numeric",
    ),
    LeafSpySensorDescription(
        key="speed",
        leafspy_key="Speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    LeafSpySensorDescription(
        key="trip_number",
        leafspy_key="Trip",
        icon="mdi:road-variant",
    ),
    LeafSpySensorDescription(
        key="vin",
        leafspy_key="VIN",
        icon="mdi:identifier",
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

            message = _correct_swapped_battery_values(message)
            message = _drop_impossible_ambient(message)

            _LOGGER.debug("Incoming message: %s", redact_message(message))

            # Create and update sensors for each description
            for description in SENSOR_TYPES:
                sensor_id = f"{dev_id}_{description.key}"
                value = message.get(description.leafspy_key, None)

                _LOGGER.debug("Sensor %s: Initial value=%s", description.key, loggable_value(description.leafspy_key, value))

                if value is not None and description.transform_fn:
                    try:
                        value = description.transform_fn(value)
                    except (ValueError, TypeError) as err:
                        # Skip only this sensor; keep processing the others.
                        _LOGGER.warning(
                            "Ignoring invalid Leaf Spy value for %s: %s",
                            description.key, err,
                        )
                        continue
                    _LOGGER.debug("Sensor %s: Transformed value=%s", description.key, loggable_value(description.leafspy_key, value))

                if value is not None:
                    sensor = hass.data[DOMAIN]['sensors'].get(sensor_id)
                    
                    sensor_description = description

                    # Leaf Spy sends temperatures in the unit selected in the
                    # app, reported in the "Tunits" field.
                    unit = None
                    if description.device_class == SensorDeviceClass.TEMPERATURE:
                        unit = _temperature_unit(message)

                    if sensor is not None:
                        if sensor.hass is None:
                            # Entity is disabled or not yet added to Home
                            # Assistant; writing state would raise.
                            continue
                        # Update existing sensor
                        sensor.entity_description = sensor_description
                        if unit is not None:
                            sensor.set_native_unit(unit)
                        sensor.update_state(value)
                    else:
                        # Add a new sensor
                        sensor = LeafSpySensor(dev_id, sensor_description, value)
                        if unit is not None:
                            sensor.set_native_unit(unit)
                        hass.data[DOMAIN]['sensors'][sensor_id] = sensor
                        async_add_entities([sensor])

                        # Add a log to confirm the sensor is being registered
                        _LOGGER.debug("Registered sensor: %s with initial value: %s", sensor.name, loggable_value(description.leafspy_key, value))

        except Exception as err:
            _LOGGER.error("Error processing Leaf Spy message: %s", err)
            _LOGGER.exception("Full traceback")

    entry.async_on_unload(
        async_dispatcher_connect(hass, DOMAIN, _process_message)
    )
    
    # Restore previously loaded sensors
    dev_reg = device_registry.async_get(hass)
    dev_ids = {
        identifier[1]
        for device in device_registry.async_entries_for_config_entry(
            dev_reg, entry.entry_id
        )
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
        return self.entity_description.key
    
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

    def set_native_unit(self, unit):
        """Set the native unit of measurement.

        Uses the _attr_ attribute so Home Assistant's cached unit property
        is invalidated; replacing entity_description would not be.
        """
        self._attr_native_unit_of_measurement = unit

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
            _LOGGER.debug("Restored state for %s: %s", self.name, loggable_value(self.entity_description.leafspy_key, last_state.native_value))

            try:
                # Restore the unit the value was reported in (e.g. Fahrenheit)
                if (
                    self.entity_description.device_class == SensorDeviceClass.TEMPERATURE
                    and last_state.native_unit_of_measurement
                ):
                    self.set_native_unit(last_state.native_unit_of_measurement)
                self._value = last_state.native_value
                self.async_write_ha_state()  # Make sure the restored state is written
            except (ValueError, TypeError):
                _LOGGER.warning(f"Could not restore state for {self.name}")
