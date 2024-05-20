"""Data model for home assistant synthetic home."""

import itertools
from dataclasses import dataclass, field
import pathlib
import logging

from mashumaro.codecs.yaml import yaml_decode

from synthetic_home.exceptions import SyntheticHomeError
from synthetic_home.device_types import (
    DeviceTypeRegistry,
    DeviceStateStrategy,
    DeviceState,
    EntityEntry,
    merge_entity_state_attributes,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class SyntheticDeviceInfo:
    """Device model information."""

    model: str | None = None
    """The model name of the device e.g. 'Learning Thermostat'."""

    manufacturer: str | None = None
    """The manufacturer of the device e.g. 'Nest'."""

    sw_version: str | None = None
    """The firmware version string of the device e.g. '1.0.2'."""


@dataclass
class Device:
    """A synthetic device."""

    name: str
    """A human readable name for the device."""

    device_type: str | None = None
    """The type of the device in the device registry that determines how it maps to entities."""

    device_info: SyntheticDeviceInfo | None = None
    """Device make and model information."""

    device_state: str | DeviceState | None = None
    """A list of pre-canned RestorableStateAttributes specified by the key.

    These are used for restoring a device into a specific state supported by the
    device type. This is used to use a label rather than specifying low level
    entity details. This is an alternative to specifying low level attributes above.

    Restorable attributes overwrite normal attributes since they can be reloaded
    at runtime.
    """

    entity_entries: dict[str, list[EntityEntry]] = field(default_factory=dict)
    """The validated set of entity entries"""

    def merge(
        self,
        device_state: DeviceState | None = None,
        entity_entries: dict[str, list[EntityEntry]] | None = None,
    ) -> "Device":
        """Merge the existing device with a new device state."""
        return Device(
            name=self.name,
            device_type=self.device_type,
            device_info=self.device_info,
            device_state=device_state or self.device_state,
            entity_entries=entity_entries or self.entity_entries,
        )


def build_device_state(device: Device, registry: DeviceTypeRegistry) -> Device:
    """Validate the device and return a new instance."""
    if (device_type := registry.device_types.get(device.device_type or "")) is None:
        raise SyntheticHomeError(
            f"Device {device} has device_type {device.device_type} not found in: {registry.device_types}"
        )

    if device.device_state is not None:
        if (
            isinstance(device.device_state, str)
            and device.device_state not in device_type.device_states_dict
        ):
            raise SyntheticHomeError(
                f"Device {device} has state '{device.device_state}' not in: {device_type.device_states_dict}"
            )
        if isinstance(device.device_state, dict):
            _LOGGER.debug(
                "Parsing device state from dictionary: %s", device.device_state
            )
            strategy = DeviceStateStrategy()
            device = device.merge(
                device_state=strategy.deserialize(("custom", device.device_state))
            )
            _LOGGER.debug("Parsed=%s", device)

    device_state: DeviceState | None = None
    _LOGGER.debug("Checking device state: %s", device.device_state)
    if (
        device.device_state is None or isinstance(device.device_state, DeviceState)
    ) and device_type.device_states:
        # Pick the first device state as the default
        device_state = device_type.device_states[0]
        if isinstance(device.device_state, DeviceState):
            device_state = device_state.merge(device.device_state)
            _LOGGER.debug("1 device_state=%s", device_state)
    elif device.device_state is not None and isinstance(device.device_state, str):
        device_state = device_type.device_states_dict[device.device_state]
        _LOGGER.debug("2 device_state=%s", device_state)
    else:
        raise SyntheticHomeError(f"Device did not declare a device state: {device}")
    _LOGGER.debug("Merging entity attributes for device state: %s", device_state)
    entity_entries = {
        platform: [
            merge_entity_state_attributes(
                platform, entity_entry, device_state.entity_states
            )
            for entity_entry in entity_entries
        ]
        for platform, entity_entries in device_type.entities.items()
    }
    return device.merge(device_state=device_state, entity_entries=entity_entries)


@dataclass
class SyntheticHome:
    """Data about a synthetic home."""

    # Devices by area
    devices: dict[str, list[Device]] = field(default_factory=dict)

    # Services for the home not for a specific area
    services: list[Device] = field(default_factory=list)

    # Device types supported by the home.
    device_type_registry: DeviceTypeRegistry | None = None

    def build(self) -> "SyntheticHome":
        """Validate and build the complete SyntheticHome device state."""
        if self.device_type_registry is None:
            return self
        return SyntheticHome(
            devices={
                key: [
                    build_device_state(device, self.device_type_registry)
                    for device in devices
                ]
                for key, devices in self.devices.items()
            },
            services=[
                build_device_state(device, self.device_type_registry)
                for device in self.services
            ],
            device_type_registry=self.device_type_registry,
        )

    def find_devices_by_name(
        self, area_name: str | None, device_name: str
    ) -> Device | None:
        """Find devices by optional area and device name."""
        devices = list(
            itertools.chain.from_iterable(
                [
                    area_devices
                    for area, area_devices in self.devices.items()
                    if area_name is None or area == area_name
                ]
            )
        )
        if area_name is not None and not devices:
            raise SyntheticHomeError(f"Area name '{area_name}' matched no devices")
        found_devices = [device for device in devices if device.name == device_name]
        if len(found_devices) == 0:
            raise SyntheticHomeError(f"Device name '{device_name}' matched no devices")
        if len(found_devices) > 1:
            raise SyntheticHomeError(
                f"Device name '{device_name}' matched multiple devices, must specify an area"
            )
        return found_devices[0]


def read_config_content(config_file: pathlib.Path) -> str:
    """Create configuration file content, exposed for patching."""
    with config_file.open("r") as f:
        return f.read()


def load_synthetic_home(config_file: pathlib.Path) -> SyntheticHome:
    """Load synthetic home configuration from disk."""
    try:
        content = read_config_content(config_file)
    except FileNotFoundError:
        raise SyntheticHomeError(f"Configuration file '{config_file}' does not exist")
    try:
        return yaml_decode(content, SyntheticHome)
    except ValueError as err:
        raise SyntheticHomeError(f"Could not parse config file '{config_file}': {err}")
