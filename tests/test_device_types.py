"""Test for device_types."""

from synthetic_home import device_types


def test_load_device_type_registry() -> None:
    """Test loading the device type registry."""

    reg = device_types.load_device_type_registry()
    for name, device_type in reg.device_types.items():
        assert name
        assert device_type.device_type
        assert device_type.desc
        assert isinstance(device_type.device_states_dict, dict)
        assert device_type.entities, "Device must have at least one entity"
        for domain, entity_entries in device_type.entities.items():
            assert domain
            assert entity_entries, "Domain must have at least one entity entry"
            for entry in entity_entries:
                assert entry.key
                assert entry.attributes, f"Entity for device {name} has no attributes"


def test_camera_device() -> None:
    """Test the camera entry in the device registry."""

    reg = device_types.load_device_type_registry()
    assert reg.device_types
    assert "camera" in reg.device_types
    camera = reg.device_types["camera"]
    assert camera
    assert (
        camera.desc == "A video camera that supports motion detection and other events."
    )
    assert list(camera.device_states_dict.keys()) == [
        "idle",
        "motion-detected",
        "person-detected",
        "sound-detected",
    ]
    assert [
        (entry.key, entry.attributes)
        for entry in camera.entities.get("binary_sensor", [])
    ] == [
        (
            "motion",
            {"device_class": "binary_sensor.BinarySensorDeviceClass.MOTION"},
        ),
        (
            "person",
            {"device_class": "binary_sensor.BinarySensorDeviceClass.OCCUPANCY"},
        ),
        (
            "sound",
            {"device_class": "binary_sensor.BinarySensorDeviceClass.SOUND"},
        ),
    ]
