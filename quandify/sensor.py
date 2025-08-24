"""Sensor platform for Quandify integration."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfVolume
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities based on device class."""
    coordinator: QDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for device in coordinator.devices:
        device_type = device.get("type")
        hardware_version = device.get("hardware_version")
        sensor_class = None
        device_name = "Unknown"

        if device_type == "cubicmeter":
            device_name = "CubicMeter"
            sensor_class = CubicMeter
        elif device_type == "cubicdetector":
            device_name = "CubicDetector"
            sensor_class = CubicDetector
        elif device_type == "waterfuse":
            if hardware_version == 5:
                device_name = "Water Grip"
                sensor_class = WaterGrip
            elif hardware_version == 4:
                device_name = "CubicSecure"
                sensor_class = CubicSecure

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


class QuandifyDevice(CoordinatorEntity[QDataUpdateCoordinator], SensorEntity):
    """Base sensor entity for all Quandify devices."""

    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = ()

    def __init__(
        self,
        coordinator: QDataUpdateCoordinator,
        device: dict[str, Any],
        description: SensorEntityDescription,
        device_name: str,
    ):
        """Initialize the sensor."""
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
        self._attr_native_value = value
        self._attr_available = self.coordinator.last_update_success


class WaterGrip(QuandifyDevice):
    """Represents sensors for a Water Grip device."""

    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
        SensorEntityDescription(
            key="status.total_volume",
            name="Total Volume",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.WATER,
        ),
        SensorEntityDescription(
            key="status.avg_water_temp",
            name="Water Temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
    )


class CubicSecure(QuandifyDevice):
    """Represents sensors for a CubicSecure device."""

    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
        SensorEntityDescription(
            key="status.total_volume",
            name="Total Volume",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.WATER,
        ),
        SensorEntityDescription(
            key="status.avg_water_temp",
            name="Water Temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
    )


class CubicMeter(QuandifyDevice):
    """Represents sensors for a CubicMeter device."""

    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
        SensorEntityDescription(
            key="status.total_volume",
            name="Total Volume",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.WATER,
        ),
        SensorEntityDescription(
            key="status.ambient_temp",
            name="Ambient Temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
    )


class CubicDetector(QuandifyDevice):
    """Represents sensors for a CubicDetector device."""
