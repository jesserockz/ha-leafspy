"""Constants for Leaf Spy integration."""
from .models import (
    LeafspyBinarySensorEntityDescription,
    LeafspySensorEntityDescription,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)


DOMAIN = "leafspy"
URL_LEAFSPY_PATH = "/api/leafspy/"
CONF_SECRET = "secret"


PLUG_STATES = ["Not Plugged In", "Partially Plugged In", "Plugged In"]

CHARGE_MODES = [
    "Not Charging",
    "Level 1 Charging (100-120 Volts)",
    "Level 2 Charging (200-240 Volts)",
    "Level 3 Quick Charging",
]

SENSORS: tuple[LeafspySensorEntityDescription, ...] = (
    LeafspySensorEntityDescription(
        key="state_of_charge",
        name="State of Charge",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        state=lambda data: data.SOC,
    ),
    LeafspySensorEntityDescription(
        key="amp_hours",
        name="Amp Hours",
        native_unit_of_measurement="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        state=lambda data: data.AHr,
    ),
    LeafspySensorEntityDescription(
        key="odometer",
        name="Odometer",
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement="km",
        icon="mdi:road-variant",
        state=lambda data: data.Odo,
    ),
    LeafspySensorEntityDescription(
        key="battery_temperature",
        name="Battery Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        state=lambda data: data.BatTemp,
    ),
    LeafspySensorEntityDescription(
        key="ambient_temperature",
        name="Ambient Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        state=lambda data: data.Amb,
    ),
    LeafspySensorEntityDescription(
        key="plug_state",
        name="Plug State",
        entity_registry_enabled_default=False,
        state=lambda data: PLUG_STATES[data.PlugState],
    ),
    LeafspySensorEntityDescription(
        key="charge_mode",
        name="Charge Mode",
        entity_registry_enabled_default=False,
        state=lambda data: CHARGE_MODES[data.ChrgMode],
    ),
    LeafspySensorEntityDescription(
        key="charge_power",
        name="Charge Power",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        state=lambda data: data.ChrgPwr,
    ),
    LeafspySensorEntityDescription(
        key="device_battery",
        name="Device Battery",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        state=lambda data: data.DevBat,
    ),
    LeafspySensorEntityDescription(
        key="rpm",
        name="RPM",
        native_unit_of_measurement="rpm",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        state=lambda data: data.RPM,
    ),
    LeafspySensorEntityDescription(
        key="gids",
        name="GIDs",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        state=lambda data: data.Gids,
    ),
)

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    LeafspyBinarySensorEntityDescription(
        key="power_switch",
        name="Power Switch",
        device_class=BinarySensorDeviceClass.POWER,
        state=lambda data: data.PwrSw == 1,
    ),
)
