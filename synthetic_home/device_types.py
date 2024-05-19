"""Data model for home assistant synthetic home."""

from collections.abc import Generator
from dataclasses import dataclass, field
from importlib import resources
from importlib.resources.abc import Traversable
import logging
from typing import Any
import yaml

from mashumaro.codecs.yaml import yaml_decode
from mashumaro.exceptions import MissingField
from mashumaro import field_options, DataClassDictMixin
from mashumaro.types import SerializationStrategy

from .exceptions import SyntheticHomeError

__all__ = [
    "DeviceTypeRegistry",
    "DeviceType",
    "DeviceState",
    "EntityState",
    "EntityEntry",
    "load_device_type_registry",
]


_LOGGER = logging.getLogger(__name__)


DEVICE_TYPES_RESOURCE_PATH = resources.files().joinpath("registry")


class KeyedObjectListStrategy(SerializationStrategy):
    """A predefined entity state parser."""

    def __init__(self, object_strategy: SerializationStrategy) -> None:
        """Initialize KeyedObjectStrategy."""
        self._object_strategy = object_strategy

    def deserialize(self, value: Any) -> list[Any]:
        """Deserialize the object."""
        if not value:
            return []
        if isinstance(value, dict):
            return [
                self._object_strategy.deserialize((key, state))
                for key, state in value.items()
            ]
        raise ValueError(f"Expected 'dict' representing the object list, got: {value}")


@dataclass
class EntityEntry(DataClassDictMixin):
    """Defines an entity type.

    An entity is the lowest level object that maps to a behavior or trait of a device.
    """

    key: str | None = None
    """The entity description key"""

    attributes: dict[str, str] = field(default_factory=dict)
    """Attributes supported by this entity."""


class EntityDictStrategy(SerializationStrategy):
    """A parser of the entity entry dict."""

    def deserialize(
        self, value: dict[str, dict[str, dict[str, str]]]
    ) -> dict[str, list[EntityEntry]]:
        """Deserialize the object."""
        return {
            domain: [
                EntityEntry(key=key, attributes=attributes)
                for key, attributes in values.items()
            ]
            for domain, values in value.items()
        }


@dataclass
class EntityState(DataClassDictMixin):
    """Represents a pre-defined entity state."""

    domain: str
    """The domain of the entity."""

    key: str
    """The entity key identifying the entity."""

    state: Any
    """The values that make up the entity state."""

    @property
    def domain_key(self) -> str:
        """Return the full domain.key."""
        return f"{self.domain}.{self.key}"


class EntityStateStrategy(SerializationStrategy):
    """A predefined entity state parser."""

    def deserialize(self, value: tuple[str, Any]) -> EntityState:
        """Deserialize the object."""
        key = value[0]
        state = value[1]
        parts = key.split(".")
        if len(parts) != 2:
            raise ValueError(f"Expected '<domain>.<entitiy-key>', got {key}")
        return EntityState(domain=parts[0], key=parts[1], state=state)


@dataclass
class DeviceState(DataClassDictMixin):
    """Represents a pre-defined device state.

    This is used to map a pre-defined devie state to the values that should be
    set on individual entities. These are typically "interesting" states of the
    device that can be enumerated during evaluation. For example, instead of
    explicitly specifying specific temperature values, a predefined state could
    implement "warm" and "cool".
    """

    name: str
    """An identifier that names this state."""

    entity_states: list[EntityState]
    """An identifier for this set of attributes used for labeling"""


class DeviceStateStrategy(SerializationStrategy):
    """A predefined device state parser."""

    _child_strategy = KeyedObjectListStrategy(EntityStateStrategy())

    def deserialize(self, value: tuple[str, Any]) -> DeviceState:
        """Deserialize the object."""
        if not isinstance(value, tuple):
            raise ValueError(
                f"Expected 'tuple' representing the DeviceState object, got: {value}"
            )
        return DeviceState(
            name=value[0], entity_states=self._child_strategy.deserialize(value[1])
        )


@dataclass(frozen=True)
class DeviceType(DataClassDictMixin):
    """Defines of device type."""

    device_type: str
    """The identifier for the device e.g. 'smart-lock'"""

    desc: str
    """The human readable description of the device."""

    device_states: list[DeviceState] = field(
        metadata=field_options(
            serialization_strategy=KeyedObjectListStrategy(DeviceStateStrategy())
        ),
        default_factory=list,
    )
    """A series of different attribute values that are most interesting to use during evaluation."""

    entities: dict[str, list[EntityEntry]] = field(
        metadata=field_options(serialization_strategy=EntityDictStrategy()),
        default_factory=dict,
    )
    """Entity platforms and their entity description keys"""

    @property
    def device_states_dict(self) -> dict[str, DeviceState]:
        """Get the predefined state by the specified key."""
        return {state.name: state for state in self.device_states}

    @property
    def entity_dict(self) -> dict[str, EntityEntry]:
        """Get a flat map of all entity entries."""
        return {
            f"{platform}.{entry.key}": entry
            for platform, entries in self.entities.items()
            for entry in entries
        }

    def __post_init__(self) -> None:
        """Validate the DeviceType."""
        entity_dict = self.entity_dict
        for device_state in self.device_states:
            for entity_state in device_state.entity_states:
                print(entity_state.domain_key)
                print(entity_dict)
                if entity_state.domain_key not in entity_dict:
                    raise ValueError(
                        f"Device '{self.device_type}' state '{device_state.name}' references "
                        f"invalid entity '{entity_state.domain_key}' not in {list(entity_dict.keys())}"
                    )


@dataclass
class DeviceTypeRegistry:
    """The registry of all DeviceType objects."""

    device_types: dict[str, DeviceType] = field(default_factory=dict)


def _read_device_types(
    device_types_path: Traversable,
) -> Generator[DeviceType, None, None]:
    """Read device types from the device type directory."""
    _LOGGER.debug("Loading device type registry from %s", device_types_path.absolute())  # type: ignore[attr-defined]

    for device_type_file in device_types_path.iterdir():
        if not device_type_file.name.endswith(".yaml"):
            continue
        _LOGGER.debug("Loading %s", device_type_file)
        try:
            with device_type_file.open("r") as f:
                content = f.read()
        except FileNotFoundError:
            raise SyntheticHomeError(
                f"Configuration file '{device_type_file}' does not exist"
            )

        try:
            device_type: DeviceType = yaml_decode(content, DeviceType)
        except MissingField as err:
            raise SyntheticHomeError(f"Unable to decode file {device_type_file}: {err}")
        except yaml.YAMLError as err:
            raise SyntheticHomeError(f"Unable to decode file {device_type_file}: {err}")
        if device_type_file.name != f"{device_type.device_type}.yaml":
            raise SyntheticHomeError(
                f"Device type '{device_type.device_type}' name does not match filename '{device_type_file.name}'"
            )

        yield device_type


def load_device_type_registry() -> DeviceTypeRegistry:
    """Load device types from the yaml configuration files."""
    device_types = {}
    for device_type in _read_device_types(DEVICE_TYPES_RESOURCE_PATH):
        if device_type.device_type in device_types:
            raise SyntheticHomeError(
                f"Device registry contains duplicate device type '{device_type.device_type}"
            )
        device_types[device_type.device_type] = device_type
    return DeviceTypeRegistry(device_types=device_types)
