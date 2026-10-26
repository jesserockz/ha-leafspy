"""Tests for Leaf Spy sensors."""
import logging

import pytest
from homeassistant.const import UnitOfTemperature
from homeassistant.core import State
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import (
    mock_restore_cache_with_extra_data,
)

from custom_components.leafspy.const import DOMAIN

DEV_ID = "leaf_testvin0000000001"


def state_of(hass, key):
    return hass.states.get(f"sensor.leaf_{key}")


async def test_all_sensors_created_from_one_upload(hass, send):
    await send()
    sensors = [s.entity_id for s in hass.states.async_all("sensor")]
    assert len(sensors) == 21


@pytest.mark.parametrize(
    ("key", "field", "raw", "expected"),
    [
        ("battery_state_of_charge", "SOC", "88.90009999999999", "88.9"),
        ("battery_capacity", "AHr", "164.6517", "164.65"),
        ("battery_conductance_hx", "Hx", "79.03", "79.03"),
        # iOS sometimes sends Hx scaled by 1024 (e.g. 8092.67 = 79.03 * 102.4).
        ("battery_conductance_hx", "Hx", "8092.672", "79.03"),
        ("battery_health", "SOH", "93.34", "93.34"),
        ("battery_state_of_charge_gids", "Gids", "647", "647"),
        ("odometer", "Odo", "33908.88", "33908"),
        ("charge_mode", "ChrgMode", "0", "Not charging"),
        ("charge_mode", "ChrgMode", "2", "Level 2 charging"),
        ("charge_mode", "ChrgMode", "3", "Level 3 quick charging"),
        ("charge_mode", "ChrgMode", "9", "unknown"),
        ("plug_status", "PlugState", "2", "Plugged"),
        ("front_wiper_status", "Wpr", "80", "High"),
        ("front_wiper_status", "Wpr", "0", "unknown"),
        ("phone_battery", "DevBat", "95", "95"),
        ("trip_number", "Trip", "1280", "1280"),
        ("vin", "VIN", "TESTVIN0000000001", "TESTVIN0000000001"),
    ],
)
async def test_values_are_transformed(hass, send, key, field, raw, expected):
    await send(**{field: raw})
    assert state_of(hass, key).state == expected


async def test_values_update_on_next_upload(hass, send):
    await send(SOC="50")
    await send(SOC="51.5")
    assert state_of(hass, "battery_state_of_charge").state == "51.5"


async def test_missing_field_does_not_drop_others(hass, send):
    await send(SOC=None)
    assert state_of(hass, "battery_state_of_charge") is None
    assert state_of(hass, "battery_health").state == "93.34"


async def test_invalid_value_skips_only_that_sensor(hass, send, caplog):
    await send(ChrgMode="0", SOH="90")
    await send(ChrgMode="not-a-number", SOH="91")

    assert state_of(hass, "charge_mode").state == "Not charging"  # unchanged
    assert float(state_of(hass, "battery_health").state) == 91  # still updated
    assert "Ignoring invalid Leaf Spy value for charge_mode" in caplog.text


async def test_odometer_zero_is_ignored(hass, send):
    await send(Odo="1000")
    await send(Odo="0")
    assert state_of(hass, "odometer").state == "1000"


async def test_odometer_zero_on_first_upload_creates_no_reading(hass, send):
    await send(Odo="0")
    assert state_of(hass, "odometer") is None


@pytest.mark.parametrize("units", ["F", "f", " F "])
async def test_fahrenheit_upload_is_read_as_fahrenheit(hass, send, units):
    await send(Tunits=units, BatTemp="60.3")
    state = state_of(hass, "battery_temperature")
    # Test instance uses metric, so HA converts 60.3 °F to °C for display.
    assert state.attributes["unit_of_measurement"] == UnitOfTemperature.CELSIUS
    assert float(state.state) == pytest.approx(15.72, abs=0.01)


@pytest.mark.parametrize("units", ["C", "", None])
async def test_celsius_or_missing_units_read_as_celsius(hass, send, units):
    await send(Tunits=units, BatTemp="15.6")
    assert float(state_of(hass, "battery_temperature").state) == pytest.approx(15.6)


async def test_switching_units_mid_session_stays_consistent(hass, send):
    await send(Tunits="F", BatTemp="60.3")
    first = float(state_of(hass, "battery_temperature").state)
    await send(Tunits="C", BatTemp="15.6")
    second = float(state_of(hass, "battery_temperature").state)
    assert first == pytest.approx(15.72, abs=0.01)
    assert second == pytest.approx(15.6)


async def test_disabled_sensor_is_skipped_without_error(hass, send, caplog):
    from homeassistant.helpers import entity_registry as er

    await send()
    ent_reg = er.async_get(hass)
    ent_reg.async_update_entity(
        "sensor.leaf_battery_health", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.config_entries.async_reload(
        hass.config_entries.async_entries(DOMAIN)[0].entry_id
    )
    await hass.async_block_till_done()

    caplog.set_level(logging.ERROR)
    resp = await send(SOH="80", SOC="70")
    assert resp.status == 200
    assert "Error processing Leaf Spy message" not in caplog.text
    assert float(state_of(hass, "battery_state_of_charge").state) == 70


async def test_sensors_restored_after_restart(hass, config_entry):
    dr.async_get(hass).async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, DEV_ID)},
        name="Leaf",
    )
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State("sensor.leaf_battery_state_of_charge", "88.9"),
                {"native_value": 88.9, "native_unit_of_measurement": "%"},
            ),
            (
                State("sensor.leaf_battery_temperature", "15.72"),
                {"native_value": 60.3, "native_unit_of_measurement": "°F"},
            ),
        ],
    )

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert state_of(hass, "battery_state_of_charge").state == "88.9"
    # The restored reading keeps the unit it was reported in.
    assert float(state_of(hass, "battery_temperature").state) == pytest.approx(
        15.72, abs=0.01
    )
    # Every sensor exists after a restart, even before an upload.
    assert len(hass.states.async_all("sensor")) == 21
