"""Leaf Spy can send an outside temperature no weather could produce.

After it reconnects with the car off it repeats a stale value (e.g. 188.6), and
a mismatched Convert Outside Temperature setting can convert it twice (e.g.
162.5 °F on a 72 °F day). Such readings are dropped so the sensor keeps its
last value. Plausible limits: -50..70 °C, or -58..158 °F.
"""
import logging

import pytest

AMBIENT = "sensor.leaf_ambient_temperature"


def ambient(hass):
    state = hass.states.get(AMBIENT)
    return None if state is None else float(state.state)


@pytest.mark.parametrize(
    ("units", "good", "good_c", "bad"),
    [
        ("C", "20.0", 20.0, "188.6"),  # stale value after reconnect, °C mode
        ("C", "20.0", 20.0, "70.5"),
        ("C", "20.0", 20.0, "-51"),
        ("F", "72.5", 22.5, "162.5"),  # converted twice, °F mode
        ("F", "72.5", 22.5, "371.5"),
        ("F", "72.5", 22.5, "158.5"),
        ("F", "72.5", 22.5, "159.3"),  # converted twice on a cooler day
        ("F", "72.5", 22.5, "-60"),
    ],
)
async def test_impossible_reading_keeps_last_value(hass, send, units, good, good_c, bad):
    await send(Tunits=units, Amb=good)
    await send(Tunits=units, Amb=bad)
    assert ambient(hass) == pytest.approx(good_c, abs=0.01)


@pytest.mark.parametrize(
    ("units", "value", "expected_c"),
    [
        ("C", "70", 70.0),
        ("C", "65", 65.0),  # heat-soaked bumper sensor in sun
        ("C", "-50", -50.0),
        ("C", "-12.5", -12.5),
        ("F", "158", 70.0),
        ("F", "-58", -50.0),
        ("F", "5", -15.0),
    ],
)
async def test_extreme_but_possible_readings_are_kept(hass, send, units, value, expected_c):
    await send(Tunits=units, Amb=value)
    assert ambient(hass) == pytest.approx(expected_c, abs=0.01)


async def test_impossible_reading_on_first_upload_creates_no_reading(hass, send):
    await send(Tunits="C", Amb="188.6")
    assert hass.states.get(AMBIENT) is None


async def test_missing_units_are_treated_as_celsius(hass, send):
    await send(Tunits=None, Amb="20")
    await send(Tunits=None, Amb="100")  # possible in °F, not in °C
    assert ambient(hass) == pytest.approx(20.0)


async def test_unparseable_reading_is_ignored_without_error(hass, send, caplog):
    await send(Amb="20")
    caplog.set_level(logging.ERROR)
    await send(Amb="abc", SOC="70")
    assert ambient(hass) == pytest.approx(20.0)
    assert float(hass.states.get("sensor.leaf_battery_state_of_charge").state) == 70
    assert "Error processing Leaf Spy message" not in caplog.text


async def test_other_fields_still_update(hass, send):
    await send(Tunits="C", Amb="20", BatTemp="15")
    await send(Tunits="C", Amb="188.6", BatTemp="16")
    assert float(hass.states.get("sensor.leaf_battery_temperature").state) == 16
    assert ambient(hass) == pytest.approx(20.0)


async def test_next_plausible_reading_is_used(hass, send):
    await send(Tunits="C", Amb="20")
    await send(Tunits="C", Amb="188.6")
    await send(Tunits="C", Amb="21")
    assert ambient(hass) == pytest.approx(21.0)
