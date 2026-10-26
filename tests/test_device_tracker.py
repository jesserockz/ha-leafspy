"""Tests for the Leaf Spy device tracker."""
import pytest
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import State
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.leafspy.const import DOMAIN

ENTITY = "device_tracker.leaf"
DEV_ID = "leaf_testvin0000000001"


def location(hass):
    attrs = hass.states.get(ENTITY).attributes
    return attrs.get(ATTR_LATITUDE), attrs.get(ATTR_LONGITUDE)


async def test_location_from_upload(hass, send):
    await send(Lat="40.5", Long="-75.25")
    assert location(hass) == (40.5, -75.25)


async def test_location_updates(hass, send):
    await send(Lat="40.5", Long="-75.25")
    await send(Lat="41.0", Long="-76.0")
    assert location(hass) == (41.0, -76.0)


@pytest.mark.parametrize(
    ("lat", "lon"),
    [("0", "0"), ("0.0", "0.0"), ("", ""), (None, None), ("abc", "def")],
)
async def test_no_gps_fix_keeps_last_location(hass, send, lat, lon):
    await send(Lat="40.5", Long="-75.25")
    await send(Lat=lat, Long=lon)
    assert location(hass) == (40.5, -75.25)


async def test_no_gps_fix_on_first_upload_has_no_location(hass, send):
    await send(Lat="0", Long="0")
    assert location(hass) == (None, None)


async def test_no_battery_level_attribute(hass, send):
    await send(SOC="88.9")
    assert "battery_level" not in hass.states.get(ENTITY).attributes


async def _restart_with(hass, config_entry, attrs):
    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, DEV_ID)},
        name="Leaf",
    )
    mock_restore_cache(hass, [State(ENTITY, "not_home", attrs)])
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_location_restored_after_restart(hass, config_entry):
    await _restart_with(
        hass, config_entry, {ATTR_LATITUDE: 40.5, ATTR_LONGITUDE: -75.25}
    )
    assert location(hass) == (40.5, -75.25)


async def test_null_island_saved_before_fix_is_not_restored(hass, config_entry):
    await _restart_with(hass, config_entry, {ATTR_LATITUDE: 0, ATTR_LONGITUDE: 0})
    assert location(hass) == (None, None)
