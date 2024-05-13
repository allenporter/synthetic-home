"""Test for devife_types."""

from synthetic_home import device_types

def test_load_device_type_registry() -> None:
    """Test loading the device type registry."""

    reg = device_types.load_device_type_registry()
    assert reg.device_types
    assert "camera" in reg.device_types
    camera = reg.device_types["camera"]
    assert camera
    assert camera.desc == "A video camera that supports motion detection and other events."
    assert camera.supported_state_attributes == [
        "motion_detected",
        "person_detected",
        "sound_detected"
    ]
