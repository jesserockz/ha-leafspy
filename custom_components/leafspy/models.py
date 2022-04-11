"""Models for the Leafspy integration."""
from collections.abc import Callable

from dataclasses import dataclass, fields
from homeassistant.components.binary_sensor import BinarySensorEntityDescription

from homeassistant.components.sensor import SensorEntityDescription
from homeassistant.helpers.typing import StateType


@dataclass
class LeafspyMessage:
    """A message from the Leafspy webhook."""

    user: str
    Lat: float
    Long: float
    SOC: float
    AHr: float
    Trip: int
    Odo: int
    BatTemp: float
    Amb: float
    PlugState: int
    ChrgMode: int
    ChrgPwr: int
    VIN: str
    PwrSw: int
    DevBat: int
    RPM: int
    Gids: int
    Elv: float
    Seq: int

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, field.type):
                setattr(self, field.name, field.type(value))


@dataclass
class LeafspyEntityDescription:
    """Describes a Leafspy Entity."""

    key: str
    state: Callable[[LeafspyMessage], StateType]


@dataclass
class LeafspySensorEntityDescription(SensorEntityDescription, LeafspyEntityDescription):
    """Describes a Leafspy Sensor."""


@dataclass
class LeafspyBinarySensorEntityDescription(
    BinarySensorEntityDescription, LeafspyEntityDescription
):
    """Describes a Leafspy Sensor."""
