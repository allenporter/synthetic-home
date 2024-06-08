"""Test for synthetic_home."""

import pathlib

import pytest
from syrupy import SnapshotAssertion

from synthetic_home import synthetic_home, device_types, inventory


TEST_HOMES = pathlib.Path("tests/homes")
TEST_FIXTURES = pathlib.Path("tests/fixtures")
HOME1 = TEST_HOMES / "home1.yaml"


def test_load_synthetic_home() -> None:
    """Test loading the device type registry."""

    home = synthetic_home.load_synthetic_home(HOME1)
    assert home
    area = home.devices.get("Backyard")
    assert area
    assert len(area) == 1
    device = area[0]
    assert device.name == "Outdoor Camera"
    assert device.device_info
    assert device.device_info.model == "Spotlight Cam Battery"
    assert device.device_info.manufacturer == "Ring"
    assert device.device_info.sw_version == "2.4.1"


@pytest.mark.parametrize(
    ("home_filename"),
    list(TEST_HOMES.glob("*.yaml")),
    ids=[str(filename) for filename in TEST_HOMES.glob("*.yaml")],
)
def test_inventory(home_filename: pathlib.Path, snapshot: SnapshotAssertion) -> None:
    """Test converting the home into an inventory yaml file."""

    # Load the inventory fixture
    inventory_filename = TEST_FIXTURES / home_filename.name
    inventory_content = inventory_filename.read_text().strip()

    # Generate the inventory fixture from the synthetic home device state
    home = synthetic_home.load_synthetic_home(home_filename)
    inventory = synthetic_home.build_inventory(home)
    generated_yaml = inventory.yaml().strip()

    assert generated_yaml.split("\n") == inventory_content.split("\n")


@pytest.mark.parametrize(
    ("filename"),
    list(TEST_HOMES.glob("*.yaml")),
    ids=[str(filename) for filename in TEST_HOMES.glob("*.yaml")],
)
def test_device_state_to_entity_state(
    filename: pathlib.Path, snapshot: SnapshotAssertion
) -> None:
    """Test loading the device states and how they correspond to entity states."""
    home = synthetic_home.load_synthetic_home(filename)
    device_registry = device_types.load_device_type_registry()
    for devices in home.devices.values():
        for device in devices:
            assert device.device_type
            device_type = device_registry.device_types[device.device_type]
            assert device_type
            for device_state in device_type.device_states:
                assert device_state
                device.device_state = device_state
                device = synthetic_home.build_device_state(device, device_registry)

                inv = inventory.Inventory()
                inv.entities = synthetic_home.build_entities(None, device)
                assert inv.yaml() == snapshot
