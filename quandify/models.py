"""Models for the Quandify integration."""
from dataclasses import dataclass
from typing import Any

@dataclass
class QuandifyDevice:
    """A class representing a Quandify device."""

    id: str
    name: str
    model: str
    serial: str | None
    firmware_version: str | None
    hardware_version: int | None
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> "QuandifyDevice":
        """Create a device object from the API response."""
        device_type = data.get("type")
        hardware_version = data.get("hardware_version")
        
        # Determine the proper device name and model
        model = "Unknown"
        name = data.get("name", "Unknown Device") # Use API name if available

        if device_type == "cubicmeter":
            model = "CubicMeter"
        elif device_type == "cubicdetector":
            model = "CubicDetector"
        elif device_type == "waterfuse":
            if hardware_version == 5:
                model = "Water Grip"
            elif hardware_version == 4:
                model = "CubicSecure"
        
        # If the device has no specific name, use its model as the name
        if name == "Unknown Device":
            name = model

        return cls(
            id=data["id"],
            name=name,
            model=model,
            serial=data.get("serial"),
            firmware_version=data.get("firmware_version"),
            hardware_version=hardware_version,
        )