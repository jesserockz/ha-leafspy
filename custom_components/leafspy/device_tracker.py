"""Device tracker platform that adds support for Leaf Spy."""
import logging

from homeassistant.core import callback
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
)
from homeassistant.components.device_tracker import SourceType, TrackerEntity
from homeassistant.util import slugify
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers import device_registry
from .const import DOMAIN as LS_DOMAIN
from .util import redact_message

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Leaf Spy based off an entry."""
    async def _receive_data(dev_id, **data):
        """Receive set location."""
        entity = hass.data[LS_DOMAIN]['devices'].get(dev_id)

        if entity is not None:
            entity.update_data(data)
            return

        entity = hass.data[LS_DOMAIN]['devices'][dev_id] = LeafSpyDeviceTracker(
            dev_id, data
        )
        async_add_entities([entity])

    hass.data[LS_DOMAIN]['context'].set_async_see(_receive_data)

    # Restore previously loaded devices
    dev_reg = device_registry.async_get(hass)
    dev_ids = {
        identifier[1]
        for device in device_registry.async_entries_for_config_entry(
            dev_reg, entry.entry_id
        )
        for identifier in device.identifiers
        if identifier[0] == LS_DOMAIN
    }

    if not dev_ids:
        return

    entities = []
    for dev_id in dev_ids:
        entity = hass.data[LS_DOMAIN]['devices'][dev_id] = LeafSpyDeviceTracker(
            dev_id
        )
        entities.append(entity)

    async_add_entities(entities)


class LeafSpyDeviceTracker(TrackerEntity, RestoreEntity):
    """Represent a tracked car."""

    def __init__(self, dev_id, data=None):
        """Set up LeafSpy entity."""
        self._dev_id = dev_id
        self._data = data or {}

    @property
    def unique_id(self):
        """Return the unique ID."""
        return self._dev_id

    @property
    def icon(self):
        """Return the icon for the device."""
        return 'mdi:car'

    @property
    def latitude(self):
        """Return latitude value of the car."""
        return self._data.get('latitude')

    @property
    def longitude(self):
        """Return longitude value of the car."""
        return self._data.get('longitude')

    @property
    def name(self):
        """Return the name of the car."""
        return 'Leaf'

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def source_type(self):
        """Return the source type of the car."""
        return SourceType.GPS

    @property
    def device_info(self):
        """Return the device info."""
        return {
            'name': 'Leaf',
            'identifiers': {(LS_DOMAIN, self._dev_id)},
        }

    async def async_added_to_hass(self):
        """Call when entity about to be added to Home Assistant."""
        await super().async_added_to_hass()

        # Don't restore if we got set up with data.
        if self._data:
            return

        state = await self.async_get_last_state()

        if state is None:
            return

        attr = state.attributes
        latitude = attr.get(ATTR_LATITUDE)
        longitude = attr.get(ATTR_LONGITUDE)
        if not latitude and not longitude:
            # Saved before 0,0 was treated as "no location".
            latitude = longitude = None
        self._data = {
            'device_name': state.name,
            'latitude': latitude,
            'longitude': longitude,
        }

    @callback
    def update_data(self, data):
        """Mark the device as seen."""
        if data.get('latitude') is None or data.get('longitude') is None:
            # No GPS fix in this message: keep the last known location.
            data = {
                **data,
                'latitude': self._data.get('latitude'),
                'longitude': self._data.get('longitude'),
            }
        self._data = data
        self.async_write_ha_state()


def _parse_see_args(message):
    """Parse the Leaf Spy parameters, into the format see expects."""
    dev_id = slugify('leaf_{}'.format(message['VIN']))

    latitude = _to_float(message.get('Lat'))
    longitude = _to_float(message.get('Long'))
    # Leaf Spy sends 0,0 when the phone has no GPS fix or location is
    # disabled. Treat that as "no location" rather than a real position.
    if not latitude and not longitude:
        latitude = longitude = None

    args = {
        'dev_id': dev_id,
        'latitude': latitude,
        'longitude': longitude,
    }

    return args


def _to_float(value):
    """Convert a Leaf Spy value to float, or None if missing/invalid."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def async_handle_message(context, message):
    """Handle an Leaf Spy message."""
    _LOGGER.debug("Received %s", redact_message(message))

    args = _parse_see_args(message)
    await context.async_see(**args)
