"""Test for synthetic_home."""

import pathlib

from synthetic_home import synthetic_home


HOME1 = pathlib.Path("tests/testdata/home1.yaml")


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
