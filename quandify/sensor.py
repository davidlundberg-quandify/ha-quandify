"""Sensor platform for Quandify integration."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QDataUpdateCoordinator
from .util import get_device_profile

# Define a mapping from the profile key (from util.py) to the sensor class
PROFILE_TO_CLASS = {
    "cubic_meter": "CubicMeter",
    "cubic_detector": "CubicDetector",
    "water_grip": "WaterGrip",
    "cubic_secure": "CubicSecure",
}

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities based on device class."""
    coordinator: QDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

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


HOT_COLD_DESCRIPTION = SensorEntityDescription(
    key="sub_type",
    name="Device type",
    icon="mdi:water-thermometer",
)
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
        
        # FIX: Add custom logic for the Hot/Cold sensor
        if self.entity_description.key == "sub_type":
            sub_type_value = device_data.get("sub_type")
            if sub_type_value == "hot":
                self._attr_native_value = "Hot"
            elif sub_type_value == "cold":
                self._attr_native_value = "Cold"
            else:
                self._attr_native_value = None # "Unknown"
        else:
            # Standard logic for all other sensors
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
            name="Total volume",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.WATER,
        ),
        SensorEntityDescription(
            key="status.avg_water_temp",
            name="Water temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
        SensorEntityDescription(
            key="status.wifi_signal_strength",
            name="Signal strength",
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            state_class=SensorStateClass.MEASUREMENT
            ),
        HOT_COLD_DESCRIPTION,
    )


class CubicSecure(QuandifyDevice):
    """Represents sensors for a CubicSecure device."""

    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
        SensorEntityDescription(
            key="status.total_volume",
            name="Total volume",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.WATER,
        ),
        SensorEntityDescription(
            key="status.avg_water_temp",
            name="Water temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
        SensorEntityDescription(
            key="status.wifi_signal_strength",
            name="Signal strength",
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            state_class=SensorStateClass.MEASUREMENT,
            ),
        HOT_COLD_DESCRIPTION,
    )


class CubicMeter(QuandifyDevice):
    """Represents sensors for a CubicMeter device."""

    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
        SensorEntityDescription(
            key="status.total_volume",
            name="Total volume",
            native_unit_of_measurement=UnitOfVolume.LITERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
            device_class=SensorDeviceClass.WATER,
        ),
        SensorEntityDescription(
            key="status.ambient_temp",
            name="Ambient temperature",
            native_unit_of_measurement=UnitOfTemperature.CELSIUS,
            state_class=SensorStateClass.MEASUREMENT,
            device_class=SensorDeviceClass.TEMPERATURE,
        ),
        HOT_COLD_DESCRIPTION,
    )


class CubicDetector(QuandifyDevice):
    """Represents sensors for a CubicDetector device."""
    # FIX: Add the new sensor to this device type
    ENTITY_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
        SensorEntityDescription(
            key="status.rssi",
            name="Signal strength",
            native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            device_class=SensorDeviceClass.SIGNAL_STRENGTH,
            state_class=SensorStateClass.MEASUREMENT
            ),
    )