"""Leaf Spy sends zeros for some battery fields once the car has been off a while.

A Leaf pack can't really report 0% health, 0 Gids, 0 Ah, or 0 Hx, so a zero
there means "no reading": the sensor keeps its last value (like the odometer).
"""
import pytest

FIELDS = [
    # (sensor key, Leaf Spy field, good value, its state, zero as sent)
    ("battery_health", "SOH", "93.34", "93.34", "0.00"),
    ("battery_state_of_charge_gids", "Gids", "633", "633", "0"),
    ("battery_capacity", "AHr", "164.6517", "164.65", "0.0000"),
    ("battery_conductance_hx", "Hx", "78.95", "78.95", "0.00"),
]


def state_of(hass, key):
    return hass.states.get(f"sensor.leaf_{key}")


@pytest.mark.parametrize(("key", "field", "good", "good_state", "zero"), FIELDS)
async def test_zero_keeps_last_reading(hass, send, key, field, good, good_state, zero):
    await send(**{field: good})
    await send(**{field: zero})
    assert state_of(hass, key).state == good_state


@pytest.mark.parametrize(("key", "field", "good", "good_state", "zero"), FIELDS)
async def test_plain_zero_also_ignored(hass, send, key, field, good, good_state, zero):
    await send(**{field: good})
    await send(**{field: "0"})
    assert state_of(hass, key).state == good_state


@pytest.mark.parametrize(("key", "field", "good", "good_state", "zero"), FIELDS)
async def test_zero_on_first_upload_creates_no_reading(
    hass, send, key, field, good, good_state, zero
):
    await send(**{field: zero})
    assert state_of(hass, key) is None


@pytest.mark.parametrize(("key", "field", "good", "good_state", "zero"), FIELDS)
async def test_next_real_reading_after_zero_is_used(
    hass, send, key, field, good, good_state, zero
):
    await send(**{field: good})
    await send(**{field: zero})
    await send(**{field: "12"})
    assert float(state_of(hass, key).state) == 12


async def test_car_off_upload_with_all_zeros(hass, send):
    """The real shape: several fields zero at once, the rest still valid."""
    await send(SOH="93.34", Gids="633", AHr="164.6517", Hx="78.95", Odo="33913.71", SOC="87.0001")
    await send(SOH="0.00", Gids="0", AHr="0.0000", Hx="0.00", Odo="0", SOC="87.0001", Elv="75.3")

    assert state_of(hass, "battery_health").state == "93.34"
    assert state_of(hass, "battery_state_of_charge_gids").state == "633"
    assert state_of(hass, "battery_capacity").state == "164.65"
    assert state_of(hass, "battery_conductance_hx").state == "78.95"
    assert state_of(hass, "odometer").state == "33913"
    # Fields that weren't zeroed still update.
    assert float(state_of(hass, "battery_state_of_charge").state) == 87.0
    assert float(state_of(hass, "elevation").state) == 75.3


async def test_small_nonzero_values_are_kept(hass, send):
    await send(Gids="5", SOH="1.5")
    assert state_of(hass, "battery_state_of_charge_gids").state == "5"
    assert state_of(hass, "battery_health").state == "1.5"


async def test_hx_scaled_by_ios_still_corrected(hass, send):
    await send(Hx="8092.672")
    assert state_of(hass, "battery_conductance_hx").state == "79.03"
