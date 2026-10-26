"""Tests for the iOS Leaf Spy BatVolts/BatAmps swap workaround."""
import logging

import pytest


def state_of(hass, key):
    return hass.states.get(f"sensor.leaf_{key}")


def volts(hass):
    return float(state_of(hass, "battery_voltage").state)


def amps(hass):
    return float(state_of(hass, "battery_current").state)


async def test_swapped_upload_is_corrected(hass, send):
    await send(BatVolts="-0.00", BatAmps="392.00")
    assert volts(hass) == 392.0
    assert amps(hass) == 0.0


async def test_swapped_upload_with_positive_zero_volts_is_corrected(hass, send):
    await send(BatVolts="0.00", BatAmps="389.00")
    assert volts(hass) == 389.0
    assert amps(hass) == 0.0


async def test_correct_upload_while_driving_is_unchanged(hass, send):
    await send(BatVolts="380.00", BatAmps="-2.50")
    assert volts(hass) == 380.0
    assert amps(hass) == -2.5


@pytest.mark.parametrize(
    ("bat_volts", "bat_amps"),
    [
        ("355.0", "-250.0"),  # hard acceleration
        ("370.0", "180.0"),  # hard regen
        ("300.0", "-390.0"),  # peak acceleration, sagging pack
    ],
)
async def test_correct_upload_with_large_current_is_unchanged(
    hass, send, bat_volts, bat_amps
):
    await send(BatVolts=bat_volts, BatAmps=bat_amps)
    assert volts(hass) == float(bat_volts)
    assert amps(hass) == float(bat_amps)


async def test_car_fully_off_with_zero_values_is_unchanged(hass, send):
    await send(BatVolts="0", BatAmps="0")
    assert volts(hass) == 0.0
    assert amps(hass) == 0.0


@pytest.mark.parametrize("bat_amps", ["-392.00", "-250.0"])
async def test_negative_current_is_never_treated_as_voltage(hass, send, bat_amps):
    await send(BatVolts="0.00", BatAmps=bat_amps)
    assert volts(hass) == 0.0
    assert amps(hass) == float(bat_amps)


async def test_small_current_with_zero_volts_is_unchanged(hass, send):
    await send(BatVolts="0.00", BatAmps="12.00")
    assert volts(hass) == 0.0
    assert amps(hass) == 12.0


async def test_missing_current_is_not_swapped(hass, send):
    await send(BatVolts="-0.00", BatAmps=None)
    assert volts(hass) == 0.0
    assert state_of(hass, "battery_current") is None
    assert state_of(hass, "battery_state_of_charge").state == "88.9"


async def test_missing_voltage_is_not_swapped(hass, send):
    await send(BatVolts=None, BatAmps="392.00")
    assert state_of(hass, "battery_voltage") is None
    assert amps(hass) == 392.0
    assert state_of(hass, "battery_state_of_charge").state == "88.9"


async def test_unparseable_voltage_is_not_swapped_and_does_not_error(
    hass, send, caplog
):
    with caplog.at_level(logging.ERROR):
        await send(BatVolts="abc", BatAmps="392.00")
    assert amps(hass) == 392.0
    assert state_of(hass, "battery_state_of_charge").state == "88.9"
    assert "Error processing Leaf Spy message" not in caplog.text


async def test_unparseable_current_is_not_swapped_and_does_not_error(
    hass, send, caplog
):
    with caplog.at_level(logging.ERROR):
        await send(BatVolts="-0.00", BatAmps="abc")
    assert volts(hass) == 0.0
    assert state_of(hass, "battery_state_of_charge").state == "88.9"
    assert "Error processing Leaf Spy message" not in caplog.text


async def test_swap_does_not_stick_to_the_next_upload(hass, send):
    await send(BatVolts="-0.00", BatAmps="392.00")
    await send(BatVolts="381.00", BatAmps="-3.00")
    assert volts(hass) == 381.0
    assert amps(hass) == -3.0


async def test_correct_upload_followed_by_swapped_one(hass, send):
    await send(BatVolts="381.00", BatAmps="-3.00")
    await send(BatVolts="-0.00", BatAmps="392.00")
    assert volts(hass) == 392.0
    assert amps(hass) == 0.0


async def test_other_fields_are_untouched_by_a_swap(hass, send):
    await send(BatVolts="-0.00", BatAmps="392.00")
    assert state_of(hass, "battery_state_of_charge").state == "88.9"
    assert state_of(hass, "battery_capacity").state == "164.65"
    assert state_of(hass, "battery_health").state == "93.34"
    assert state_of(hass, "battery_temperature").state == "15.6"
    assert state_of(hass, "vin").state == "TESTVIN0000000001"


async def test_swap_is_logged_without_identifying_fields(hass, send, caplog):
    with caplog.at_level(logging.DEBUG, logger="custom_components.leafspy.sensor"):
        await send(BatVolts="-0.00", BatAmps="392.00")
    swap_lines = [r.getMessage() for r in caplog.records if "swapped" in r.getMessage()]
    assert len(swap_lines) == 1
    assert "TESTVIN0000000001" not in swap_lines[0]


async def test_no_swap_log_for_a_correct_upload(hass, send, caplog):
    with caplog.at_level(logging.DEBUG, logger="custom_components.leafspy.sensor"):
        await send(BatVolts="380.00", BatAmps="-2.50")
    assert not [r for r in caplog.records if "swapped" in r.getMessage()]
