"""Data model for the lower level inventory of a home, usable for fixtures and evaluations."""

from dataclasses import dataclass, field
import logging
import slugify
from typing import Any

import yaml
from mashumaro.mixins.yaml import DataClassYAMLMixin, EncodedData
from mashumaro.config import BaseConfig


from . import common
from .exceptions import SyntheticHomeError

__all__ = [
    "Inventory",
    "Area",
    "Device",
    "Entity",
]

_LOGGER = logging.getLogger(__name__)

DEFAULT_SEPARATOR = "_"


def _custom_encoder(data: dict[str, Any]) -> EncodedData:
    return yaml.safe_dump(data, sort_keys=False, explicit_start=True)


@dataclass
class Area(DataClassYAMLMixin):
    """Represents an area in a home."""

    name: str
    """The human readable name of the area e.g. 'Living Room'."""

    id: str | None = None
    """The identifier of the area eg. 'living_room', unique within a Home."""

    floor: str | None = None
    """The human readable name of the floor."""

    def __post_init__(self) -> None:
        """Validate the area."""
        if self.id is None:
            self.id = slugify.slugify(self.name, separator=DEFAULT_SEPARATOR)

    class Config(BaseConfig):
        code_generation_options = ["TO_DICT_ADD_OMIT_NONE_FLAG"]
        sort_keys = False


@dataclass
class Device(DataClassYAMLMixin):
    """Represents a devie within a home."""

    name: str
    """The human readable name of the device e.g. 'Left Blind'."""

    id: str | None = None
    """The identifier of the area eg. 'living_room_left_blind', unique within a Home."""

    area: str | None = None
    """The area id of the home. e.g. 'living_room'"""

    info: common.DeviceInfo | None = None
    """Detailed model information about the device."""

    class Config(BaseConfig):
        code_generation_options = ["TO_DICT_ADD_OMIT_NONE_FLAG"]
        sort_keys = False

    def __post_init__(self) -> None:
        """Validate the device."""
        if self.id is None:
            self.id = slugify.slugify(self.name, separator=DEFAULT_SEPARATOR)


@dataclass
class Entity(DataClassYAMLMixin):
    """Represents an entity within a home."""

    name: str | None = None
    """The human readable name of the entity e.g. 'Outside rain sensor'. or omitted to use device naming."""

    id: str | None = None
    """The identifier of the entity e.g. 'sensor.rain_sensor_intensity', unique within a Home."""

    area: str | None = None
    """The area id within the home e.g. 'living_room'."""

    device: str | None = None
    """The device id within the home e.g. 'living_room_left_blind'."""

    state: str | None = None
    """The current state value for the entity."""

    attributes: dict[str, str | int] | None = None
    """The current state attributes for the entity."""

    def __post_init__(self) -> None:
        """Validate the device."""
        if self.id is None:
            raise SyntheticHomeError("Entity {self.name} had no value for 'id'")

    class Config(BaseConfig):
        code_generation_options = ["TO_DICT_ADD_OMIT_NONE_FLAG"]
        sort_keys = False


@dataclass
class Inventory(DataClassYAMLMixin):
    """A fixture defines the entire definition of the home."""

    language: str | None = None
    """The default system language."""

    areas: list[Area] = field(default_factory=list)
    """The list of areas within the home."""

    devices: list[Device] = field(default_factory=list)
    """The list of devices within a home, which may be associated with areas."""

    entities: list[Entity] = field(default_factory=list)
    """The list of entities within a home, which may be associated with areas and devices."""

    def yaml(self) -> str:
        """Render the inventory as yaml."""
        return str(self.to_yaml(omit_none=True, encoder=_custom_encoder))

    class Config(BaseConfig):
        code_generation_options = ["TO_DICT_ADD_OMIT_NONE_FLAG"]
        sort_keys = False
