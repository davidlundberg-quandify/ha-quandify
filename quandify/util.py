"""Utilities for the Quandify integration."""
from typing import Any

def get_device_profile(device: dict[str, Any]) -> tuple[str, str]:

    device_type = device.get("type")
    hardware_version = device.get("hardware_version")

    if device_type == "cubicmeter":
        return "CubicMeter", "cubic_meter"
    if device_type == "cubicdetector":
        return "CubicDetector", "cubic_detector"
    if device_type == "waterfuse":
        if hardware_version == 5:
            return "Water Grip", "water_grip"
        if hardware_version == 4:
            return "CubicSecure", "cubic_secure"
    
    return "Unknown Device", "unknown"