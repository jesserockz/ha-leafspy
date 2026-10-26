"""Tests for the Leaf Spy upload endpoint."""
import logging

from custom_components.leafspy.const import URL_LEAFSPY_PATH

from .conftest import BASE_MESSAGE, SECRET, VIN


async def test_valid_upload_returns_ok(send):
    resp = await send()
    assert resp.status == 200
    assert await resp.text() == '"status":"0"'


async def test_wrong_password_is_rejected(hass, send):
    resp = await send(**{"pass": "wrong-password"})
    assert resp.status == 401
    assert hass.states.get("sensor.leaf_battery_state_of_charge") is None


async def test_missing_password_is_rejected(hass, send):
    resp = await send(**{"pass": None})
    assert resp.status == 401
    assert hass.states.get("sensor.leaf_battery_state_of_charge") is None


async def test_rejection_warns_once_until_a_success(send, caplog):
    caplog.set_level(logging.DEBUG, logger="custom_components.leafspy")

    def warnings():
        return [
            r for r in caplog.records
            if r.levelno == logging.WARNING and "invalid password" in r.getMessage()
        ]

    await send(**{"pass": "wrong-password"})
    await send(**{"pass": "wrong-password"})
    await send(**{"pass": "wrong-password"})
    assert len(warnings()) == 1

    await send()  # a good upload resets the warning
    await send(**{"pass": "wrong-password"})
    assert len(warnings()) == 2


async def test_logs_never_contain_identifying_fields(send, caplog):
    caplog.set_level(logging.DEBUG, logger="custom_components.leafspy")
    await send(Lat="40.123456", Long="-75.654321", user="private-user")

    # Only the integration's own loggers; aiohttp's access log (off by default
    # in Home Assistant) records the raw query string Leaf Spy sends.
    text = "\n".join(
        r.getMessage() for r in caplog.records
        if r.name.startswith("custom_components.leafspy")
    )
    assert "Incoming message" in text  # debug logging did run
    for secret_value in (VIN, SECRET, "40.123456", "-75.654321", "private-user"):
        assert secret_value not in text


async def test_get_without_query_is_rejected(hass, hass_client_no_auth, setup_integration):
    client = await hass_client_no_auth()
    resp = await client.get(URL_LEAFSPY_PATH)
    assert resp.status == 401


async def test_upload_does_not_require_ha_auth(hass, hass_client_no_auth, setup_integration):
    """Leaf Spy can't send an HA token; the shared secret is the only auth."""
    client = await hass_client_no_auth()
    resp = await client.get(URL_LEAFSPY_PATH, params=BASE_MESSAGE)
    assert resp.status == 200
