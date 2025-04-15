"""Data model for home assistant synthetic home."""

from dataclasses import dataclass, field
import pathlib
import logging
import slugify
from typing import Any

from mashumaro.codecs.yaml import yaml_decode

from synthetic_home.exceptions import SyntheticHomeError
from synthetic_home.device_types import (
    DeviceTypeRegistry,
    DeviceStateStrategy,
    DeviceState,
    EntityEntry,
    merge_entity_state_attributes,
)
from . import common, inventory
from .inventory import DEFAULT_SEPARATOR
from .device_types import load_device_type_registry

__all__ = [
    "SyntheticHome",
    "Device",
    "build_device_state",
    "load_synthetic_home",
    "read_config_content",
]


_LOGGER = logging.getLogger(__name__)


@dataclass
class Device:
    """A synthetic device."""

    name: str
    """A human readable name for the device."""

    device_type: str | None = None
    """The type of the device in the device registry that determines how it maps to entities."""

    device_info: common.DeviceInfo | None = None
    """Device make and model information."""

    device_state: str | dict | DeviceState | None = None
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
        # Lookup a device state and merge it into the current state
        if (
            isinstance(device.device_state, str)
            and device.device_state not in device_type.device_states_dict
        ):
            raise SyntheticHomeError(
                f"Device {device}\nhas state '{device.device_state}'\n not in: {device_type.device_states_dict}"
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
    elif device.device_state is not None and isinstance(device.device_state, str):
        device_state = device_type.device_states_dict[device.device_state]
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

    name: str
    """A human readable name for the home."""

    # Devices by area
    devices: dict[str, list[Device]] = field(default_factory=dict)

    # Services for the home not for a specific area
    services: list[Device] = field(default_factory=list)

    # Device types supported by the home.
    device_type_registry: DeviceTypeRegistry | None = None

    def __post_init__(self) -> None:
        """Build the complete device state."""
        if self.device_type_registry is None:
            self.device_type_registry = load_device_type_registry()
        self.devices = {
            key: [
                build_device_state(device, self.device_type_registry)
                for device in devices
            ]
            for key, devices in self.devices.items()
        }
        self.services = [
            build_device_state(device, self.device_type_registry)
            for device in self.services
        ]


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


def yaml_state_value(v: Any) -> Any:
    """Convert a entity state value to yaml."""
    if isinstance(v, bool) or isinstance(v, float) or isinstance(v, list):
        return v
    return str(v)


def build_entities(area_id: str | None, device_entry: Device) -> list[inventory.Entity]:
    """Build the set of entities for the device entry."""
    entities = []
    device_name = device_entry.name.replace("_", " ").title()
    device_id = slugify.slugify(device_entry.name, separator=DEFAULT_SEPARATOR)

    for platform, entity_entries in device_entry.entity_entries.items():
        for entity_entry in entity_entries:
            # Each entity in this platform needs a unique name, but
            # if the key is in the name it's the primary to avoid "Motion motion"
            entity_name = device_name
            if platform == "sensor" or (
                platform == "binary_sensor"
                and entity_entry.key not in device_entry.name.lower()
            ):
                entity_name = f"{device_name} {entity_entry.key.capitalize()}"
            entity_id = f"{platform}.{slugify.slugify(entity_name, separator=DEFAULT_SEPARATOR)}"
            entity = inventory.Entity(
                name=entity_name,
                id=entity_id,
                device=device_id,
            )
            if area_id:
                entity.area = area_id
            attributes: common.NamedAttributes = {}
            if entity_entry.attributes:
                attributes.update(entity_entry.attributes)
            state = attributes.pop("state", None)
            if state is not None:
                entity.state = yaml_state_value(state)
            if attributes:
                entity.attributes = attributes
            entities.append(entity)
    return entities


def build_inventory(home: SyntheticHome) -> inventory.Inventory:
    """Build a home inventory from the synthetic home definition.

    This is a flattened set of areas, entities, and devices.
    """

    inv = inventory.Inventory()
    pairs: list[tuple[str | None, list[Device]]] = [*home.devices.items()]
    if home.services:
        pairs.append((None, home.services))

    device_ids: set[str] = set()
    entities = []
    for area_name, devices in pairs:
        if area_name:
            area_id = slugify.slugify(area_name, separator=DEFAULT_SEPARATOR)
            inv.areas.append(inventory.Area(name=area_name, id=area_id))
        else:
            area_id = None

        for device_entry in devices:
            # Make computer generated device names more friendly
            device_name = device_entry.name.replace("_", " ").title()
            device_id = slugify.slugify(device_entry.name, separator=DEFAULT_SEPARATOR)
            if device_id in device_ids:
                device_entry.name = f"{area_name}_{device_entry.name}"
                device_name = device_entry.name.replace("_", " ").title()
                device_id = slugify.slugify(device_name, separator=DEFAULT_SEPARATOR)
            device_ids.add(device_id)
            device = inventory.Device(
                name=device_name,
                id=device_id,
                info=device_entry.device_info,
            )
            if area_id:
                device.area = area_id
            inv.devices.append(device)
            entities.extend(build_entities(area_id, device_entry))
    if entities:
        inv.entities = entities
    return inv
