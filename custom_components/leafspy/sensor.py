"""Sensor platform that adds support for Leaf Spy."""
import logging
from homeassistant.components.sensor import SensorEntity, SensorStateClass, SensorDeviceClass
from homeassistant.const import PERCENTAGE, UnitOfLength
from homeassistant.util import slugify
from .const import DOMAIN as LS_DOMAIN
from homeassistant.helpers.dispatcher import async_dispatcher_connect

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Leaf Spy sensors based on a config entry."""
    if 'sensors' not in hass.data[LS_DOMAIN]:
        hass.data[LS_DOMAIN]['sensors'] = {}

    async def _process_message(context, message):
        """Process the message."""
        try:
            if 'VIN' not in message:
                return

            dev_id = slugify(f'leaf_{message["VIN"]}')

            # Battery Health (SOH) Sensor
            if 'SOH' in message:
                soh_entity = hass.data[LS_DOMAIN]['sensors'].get(f"{dev_id}_soh")
                if soh_entity is not None:
                    soh_entity.update_state(float(message['SOH']))
                else:
                    soh_entity = LeafSpyBatteryHealthSensor(dev_id, float(message['SOH']))
                    hass.data[LS_DOMAIN]['sensors'][f"{dev_id}_soh"] = soh_entity
                    async_add_entities([soh_entity])

            # Battery Level (SOC) Sensor
            if 'SOC' in message:
                soc_entity = hass.data[LS_DOMAIN]['sensors'].get(f"{dev_id}_soc")
                if soc_entity is not None:
                    soc_entity.update_state(round(float(message['SOC']), 1))
                else:
                    soc_entity = LeafSpyBatteryLevelSensor(dev_id, round(float(message['SOC']), 1))
                    hass.data[LS_DOMAIN]['sensors'][f"{dev_id}_soc"] = soc_entity
                    async_add_entities([soc_entity])

            # Mileage Sensor
            if 'Odo' in message:
                mileage_entity = hass.data[LS_DOMAIN]['sensors'].get(f"{dev_id}_mileage")
                if mileage_entity is not None:
                    mileage_entity.update_state(int(float(message['Odo'])))
                else:
                    mileage_entity = LeafSpyMileageSensor(dev_id, int(float(message['Odo'])))
                    hass.data[LS_DOMAIN]['sensors'][f"{dev_id}_mileage"] = mileage_entity
                    async_add_entities([mileage_entity])

        except Exception as err:
            _LOGGER.error("Error processing message for Leaf Spy sensors: %s", err)

    async_dispatcher_connect(hass, LS_DOMAIN, _process_message)
    return True


class LeafSpyBatteryHealthSensor(SensorEntity):
    """Representation of the Battery Health (SOH) sensor."""

    def __init__(self, device_id, soh):
        """Initialize the sensor."""
        self._device_id = device_id
        self._soh = soh
        self._attr_icon = "mdi:battery-heart"
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._device_id}_battery_health"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Leaf battery health (SOH)"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._soh

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(LS_DOMAIN, self._device_id)},
        }

    def update_state(self, new_soh):
        """Update the sensor state."""
        self._soh = new_soh
        self.async_write_ha_state()


class LeafSpyBatteryLevelSensor(SensorEntity):
    """Representation of the Battery Level (SOC) sensor."""

    def __init__(self, device_id, soc):
        """Initialize the sensor."""
        self._device_id = device_id
        self._soc = soc
        self._attr_device_class = SensorDeviceClass.BATTERY
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = PERCENTAGE

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._device_id}_battery_level"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Leaf battery level (SOC)"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._soc

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(LS_DOMAIN, self._device_id)},
        }

    def update_state(self, new_soc):
        """Update the sensor state."""
        self._soc = new_soc
        self.async_write_ha_state()


class LeafSpyMileageSensor(SensorEntity):
    """Representation of the Mileage sensor."""

    def __init__(self, device_id, mileage):
        """Initialize the sensor."""
        self._device_id = device_id
        self._mileage = mileage
        self._attr_device_class = SensorDeviceClass.DISTANCE
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
        self._attr_icon = "mdi:counter"

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return f"{self._device_id}_mileage"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Leaf mileage"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._mileage

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(LS_DOMAIN, self._device_id)},
        }

    def update_state(self, new_mileage):
        """Update the sensor state."""
        self._mileage = new_mileage
        self.async_write_ha_state()
