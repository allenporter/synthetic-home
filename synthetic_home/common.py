"""Common data model objects used across this library.

These are typically small objects reusable in different contexts.
"""

from dataclasses import dataclass

from mashumaro.mixins.yaml import DataClassYAMLMixin
from mashumaro.config import BaseConfig


__all__ = ["DeviceInfo"]


@dataclass
class DeviceInfo(DataClassYAMLMixin):
    """Device model information."""

    model: str | None = None
    """The model name of the device e.g. 'Learning Thermostat'."""

    manufacturer: str | None = None
    """The manufacturer of the device e.g. 'Nest'."""

    sw_version: str | None = None
    """The firmware version string of the device e.g. '1.0.2'."""

    class Config(BaseConfig):
        code_generation_options = ["TO_DICT_ADD_OMIT_NONE_FLAG"]
        sort_keys = False
