"""Binary sensor platform for Quandify Water Grip."""

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
from .coordinator import WaterGripDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor entities based on device class."""
    coordinator: WaterGripDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    for device in coordinator.devices:
        device_type = device.get("type")
        hardware_version = device.get("hardware_version")
        sensor_class = None
        device_name = "Unknown"

        if device_type == "cubicmeter":
            device_name = "CubicMeter"
            sensor_class = CubicMeterBinarySensor
        elif device_type == "cubicdetector":
            device_name = "CubicDetector"
            sensor_class = CubicDetectorBinarySensor
        elif device_type == "waterfuse":
            if hardware_version == 5:
                device_name = "Water Grip"
                sensor_class = WaterGripBinarySensor
            elif hardware_version == 4:
                device_name = "CubicSecure"
                sensor_class = CubicSecureBinarySensor

        # FIX (PERF401): Replaced the for-loop with a more performant
        # list comprehension and the extend method.
        if sensor_class:
            entities.extend(
                [
                    sensor_class(coordinator, device, description, device_name)
                    for description in sensor_class.ENTITY_DESCRIPTIONS
                ]
            )

    async_add_entities(entities)


class QuandifyBinarySensor(
    CoordinatorEntity[WaterGripDataUpdateCoordinator], BinarySensorEntity
):
    """Base binary sensor entity for all Quandify devices."""

    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = ()

    def __init__(
        self,
        coordinator: WaterGripDataUpdateCoordinator,
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
            "hw_version": device.get("hardware_version"),
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

        if self.entity_description.key == "is_offline":
            self._attr_is_on = value is False
        else:
            self._attr_is_on = value is True

        self._attr_available = self.coordinator.last_update_success


class WaterGripBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a Water Grip device."""

    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="is_offline",
            name="Connectivity",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ),
        BinarySensorEntityDescription(
            key="leak_status.is_leak",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    )


class CubicSecureBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a CubicSecure device."""

    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="is_offline",
            name="Connectivity",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ),
        BinarySensorEntityDescription(
            key="leak_status.is_leak",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    )


class CubicMeterBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a CubicMeter device."""

    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="is_offline",
            name="Connectivity",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ),
    )


class CubicDetectorBinarySensor(QuandifyBinarySensor):
    """Represents binary sensors for a CubicDetector device."""

    ENTITY_DESCRIPTIONS: tuple[BinarySensorEntityDescription, ...] = (
        BinarySensorEntityDescription(
            key="is_offline",
            name="Connectivity",
            device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ),
        BinarySensorEntityDescription(
            key="leak_status.is_leak",
            name="Leak",
            device_class=BinarySensorDeviceClass.MOISTURE,
        ),
    )
