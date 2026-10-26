"""Helpers for Leaf Spy."""
from homeassistant.helpers.redact import REDACTED, async_redact_data

# Fields that identify the user, the car or its location. Never log them.
REDACT_KEYS = {"user", "pass", "VIN", "Lat", "Long"}


def redact_message(message):
    """Return a copy of a Leaf Spy message that is safe to log."""
    return async_redact_data(dict(message), REDACT_KEYS)


def loggable_value(leafspy_key, value):
    """Return a field value that is safe to log."""
    return REDACTED if leafspy_key in REDACT_KEYS else value
