"""Tests for setting up, unloading, and reloading Leaf Spy."""
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.leafspy.const import DOMAIN

DEV_ID = "leaf_testvin0000000001"


async def test_setup_with_no_devices_creates_no_entities(hass, setup_integration):
    assert setup_integration.state is ConfigEntryState.LOADED
    assert [s for s in hass.states.async_all() if s.domain != "zone"] == []


async def test_one_device_for_all_entities(hass, send):
    await send()
    devices = dr.async_entries_for_config_entry(
        dr.async_get(hass), hass.config_entries.async_entries(DOMAIN)[0].entry_id
    )
    assert len(devices) == 1
    assert devices[0].name == "Leaf"
    assert devices[0].identifiers == {(DOMAIN, DEV_ID)}


async def test_unload(hass, send):
    await send()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED


async def test_reload_keeps_entities_and_accepts_uploads(hass, send):
    await send(SOC="50")
    entry = hass.config_entries.async_entries(DOMAIN)[0]

    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert len(hass.states.async_all("sensor")) == 21

    resp = await send(SOC="60", PwrSw="1", Lat="40.5", Long="-75.25")
    assert resp.status == 200
    assert float(hass.states.get("sensor.leaf_battery_state_of_charge").state) == 60
    assert hass.states.get("binary_sensor.leaf_power").state == "on"
    assert hass.states.get("device_tracker.leaf").attributes["latitude"] == 40.5


async def test_reload_twice(hass, send):
    await send()
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert await hass.config_entries.async_reload(entry.entry_id)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    resp = await send(SOC="61")
    assert resp.status == 200
    assert float(hass.states.get("sensor.leaf_battery_state_of_charge").state) == 61


async def test_only_this_entrys_devices_are_restored(hass, config_entry):
    """A Leaf Spy device left on some other config entry isn't picked up."""
    other = MockConfigEntry(domain="other_integration")
    other.add_to_hass(hass)
    reg = dr.async_get(hass)
    reg.async_get_or_create(
        config_entry_id=config_entry.entry_id, identifiers={(DOMAIN, DEV_ID)}
    )
    reg.async_get_or_create(
        config_entry_id=other.entry_id, identifiers={(DOMAIN, "leaf_othercar")}
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.leaf_power") is not None
    unique_ids = {
        e.unique_id
        for e in hass.data["entity_registry"].entities.values()
        if e.platform == DOMAIN
    }
    assert not any(u.startswith("leaf_othercar") for u in unique_ids)


async def test_no_device_registry_deprecation_warning(hass, config_entry, caplog):
    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id, identifiers={(DOMAIN, DEV_ID)}
    )
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert "device_registry.devices" not in caplog.text
