"""Fixtures for Leaf Spy tests."""
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.leafspy.const import CONF_SECRET, DOMAIN, URL_LEAFSPY_PATH

SECRET = "test-secret"
VIN = "TESTVIN0000000001"

# A message shaped like a real Leaf Spy upload (iOS, parked, Fahrenheit off).
BASE_MESSAGE = {
    "user": "test-user",
    "pass": SECRET,
    "DevBat": "95",
    "Gids": "647",
    "Lat": "40.0",
    "Long": "-75.0",
    "Elv": "76.1",
    "Seq": "12",
    "Trip": "1280",
    "Odo": "33908.88",
    "SOC": "88.90009999999999",
    "AHr": "164.6517",
    "BatTemp": "15.6",
    "Amb": "12.0",
    "Wpr": "0",
    "PlugState": "0",
    "ChrgMode": "0",
    "ChrgPwr": "0",
    "VIN": VIN,
    "PwrSw": "0",
    "Tunits": "C",
    "RPM": "0",
    "SOH": "93.34",
    "Hx": "79.03",
    "Speed": "0.0",
    "BatVolts": "380.00",
    "BatAmps": "-2.50",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    yield


@pytest.fixture
def config_entry(hass):
    """Return a Leaf Spy config entry added to hass (not set up)."""
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_SECRET: SECRET}, title="Leaf Spy")
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
async def setup_integration(hass, config_entry):
    """Set up the integration and return its config entry."""
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    return config_entry


@pytest.fixture
async def send(hass, hass_client_no_auth, setup_integration):
    """Return a helper that sends one Leaf Spy upload and returns the response."""
    client = await hass_client_no_auth()

    async def _send(**overrides):
        params = {**BASE_MESSAGE, **overrides}
        params = {k: v for k, v in params.items() if v is not None}
        resp = await client.get(URL_LEAFSPY_PATH, params=params)
        await hass.async_block_till_done()
        return resp

    return _send
