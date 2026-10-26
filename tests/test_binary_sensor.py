"""Tests for the Leaf Spy power binary sensor."""
import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import State
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import mock_restore_cache

from custom_components.leafspy.const import DOMAIN, URL_LEAFSPY_PATH

from .conftest import BASE_MESSAGE

ENTITY = "binary_sensor.leaf_power"
DEV_ID = "leaf_testvin0000000001"


@pytest.mark.parametrize(("raw", "expected"), [("1", STATE_ON), ("0", STATE_OFF)])
async def test_power_switch(hass, send, raw, expected):
    await send(PwrSw=raw)
    assert hass.states.get(ENTITY).state == expected


async def test_power_follows_uploads(hass, send):
    await send(PwrSw="1")
    await send(PwrSw="0")
    assert hass.states.get(ENTITY).state == STATE_OFF


async def _restart_with(hass, config_entry, restored):
    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, DEV_ID)},
        name="Leaf",
    )
    if restored is not None:
        mock_restore_cache(hass, [State(ENTITY, restored)])
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("restored", [STATE_ON, STATE_OFF])
async def test_power_restored_after_restart(hass, config_entry, restored):
    await _restart_with(hass, config_entry, restored)
    assert hass.states.get(ENTITY).state == restored


async def test_power_unknown_after_restart_with_no_history(hass, config_entry):
    await _restart_with(hass, config_entry, None)
    assert hass.states.get(ENTITY).state == STATE_UNKNOWN


async def test_upload_after_restart_wins_over_restored_state(
    hass, config_entry, hass_client_no_auth
):
    await _restart_with(hass, config_entry, STATE_ON)
    client = await hass_client_no_auth()
    await client.get(URL_LEAFSPY_PATH, params={**BASE_MESSAGE, "PwrSw": "0"})
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == STATE_OFF
