"""Tests for the Leaf Spy config flow."""
from unittest.mock import patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.network import NoURLAvailableError

from custom_components.leafspy.const import CONF_SECRET, DOMAIN

GET_URL = "custom_components.leafspy.config_flow.get_url"


async def _start_and_confirm(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(result["flow_id"], {})


async def test_creates_entry_with_secret_and_url(hass):
    with patch(GET_URL, return_value="https://ha.example.com:8123"):
        result = await _start_and_confirm(hass)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Leaf Spy"
    secret = result["data"][CONF_SECRET]
    assert len(secret) == 16
    int(secret, 16)  # hex
    placeholders = result["description_placeholders"]
    assert placeholders["secret"] == secret
    # Leaf Spy has its own http/https toggle, so the scheme is stripped.
    assert placeholders["url"] == "ha.example.com:8123/api/leafspy/update"


async def test_each_setup_gets_a_new_secret(hass):
    with patch(GET_URL, return_value="http://ha.local:8123"):
        first = await _start_and_confirm(hass)
    await hass.config_entries.async_remove(first["result"].entry_id)
    with patch(GET_URL, return_value="http://ha.local:8123"):
        second = await _start_and_confirm(hass)
    assert first["data"][CONF_SECRET] != second["data"][CONF_SECRET]


async def test_no_url_configured_shows_placeholder(hass):
    with patch(GET_URL, side_effect=NoURLAvailableError):
        result = await _start_and_confirm(hass)

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert (
        result["description_placeholders"]["url"]
        == "<your-home-assistant-address>:8123/api/leafspy/update"
    )


async def test_only_one_instance(hass, config_entry):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "one_instance_allowed"
