"""Binary sensor platform for Quandify integration."""

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .util import get_device_profile

# Define a mapping from the profile key (from util.py) to the binary sensor class
PROFILE_TO_CLASS = {
    "cubic_meter": "CubicMeterBinarySensor",
    "cubic_detector": "CubicDetectorBinarySensor",
    "water_grip": "WaterGripBinarySensor",
    "cubic_secure": "CubicSecureBinarySensor",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor entities based on device class."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    for device in coordinator.devices:
        device_name, profile_key = get_device_profile(device)

        class_name = PROFILE_TO_CLASS.get(profile_key)
        if class_name:
            sensor_class = globals()[class_name]
            entities.extend(
                [
                    sensor_class(coordinator, device, description, device_name)
                    for description in sensor_class.ENTITY_DESCRIPTIONS
                ]
            )

    async_add_entities(entities)


class QuandifyBinarySensor(
    CoordinatorEntity[QuandifyDataUpdateCoordinator], BinarySensorEntity
):
    """Base binary sensor entity for all Quandify devices."""

    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = ()

    def __init__(
        self,
        coordinator: QuandifyDataUpdateCoordinator,
        device: dict[str, Any],
        description: BinarySensorEntityDescription,
        device_name: str,
    ):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device = device
        self.entity_description = description
        self._attr_unique_id = f"{device['id']}_{description.key}"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device["id"])},
            "name": device_name,
            "manufacturer": "Quandify",
            "model": device_name,
            "serial_number": device.get("serial"),
            "sw_version": device.get("firmware_version"),
        }
        self._update_attr()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attr()
        self.async_write_ha_state()

    def _update_attr(self) -> None:
        """Update the state and attributes of the entity."""
        device_data = self.coordinator.data.get(self.device["id"], {})
        value = device_data
        try:
            for key_part in self.entity_description.key.split("."):
                if value is None:
                    break
                value = value.get(key_part)
        except AttributeError:
            value = None

        self._attr_is_on = value is True
        self._attr_available = self.coordinator.last_update_success


class WaterGripBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a Water Grip device."""

    # FIX: Removed the 'is_offline' (Connectivity) sensor.
    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="leak_status.is_leak",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    )


class CubicSecureBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a CubicSecure device."""

    # FIX: Removed the 'is_offline' (Connectivity) sensor.
    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="leak_status.is_leak",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    )


class CubicMeterBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a CubicMeter device."""

    # FIX: This device has no binary sensors, so its descriptions are empty.
    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = ()


class CubicDetectorBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a CubicDetector device."""

    # FIX: Removed the 'is_offline' (Connectivity) sensor.
    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="leak_status.is_leak",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    )
