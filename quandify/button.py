"""Button platform for Quandify integration."""

import logging
from typing import Any

import aiohttp

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import QDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button entities based on device class."""
    coordinator: QDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []

    for device in coordinator.devices:
        device_type = device.get("type")
        hardware_version = device.get("hardware_version")
        button_class = None
        device_name = "Unknown"

        if device_type == "cubicmeter":
            device_name = "CubicMeter"
        elif device_type == "cubicdetector":
            device_name = "CubicDetector"
            button_class = CubicDetectorButton
        elif device_type == "waterfuse":
            if hardware_version == 5:
                device_name = "Water Grip"
                button_class = WaterGripButton
            elif hardware_version == 4:
                device_name = "CubicSecure"
                button_class = CubicSecureButton

        if button_class:
            entities.append(button_class(coordinator, device, device_name))

    async_add_entities(entities)


class QuandifyButton(CoordinatorEntity[QDataUpdateCoordinator], ButtonEntity):
    """Base button entity for all Quandify devices."""

    def __init__(
        self,
        coordinator: QDataUpdateCoordinator,
        device: dict[str, Any],
        device_name: str,
    ):
        """Initialize the button."""
        super().__init__(coordinator)
        self.device = device
        self._attr_unique_id = f"{device['id']}_acknowledge_leak"
        self._attr_name = f"{device_name} Acknowledge Leak"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:bell-cancel"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, device["id"])},
            "name": device_name,
            "manufacturer": "Quandify",
            "model": device_name,
            "serial_number": device.get("serial"),
            "sw_version": device.get("firmware_version"),
            "hw_version": device.get("hardware_version"),
        }

    async def async_press(self) -> None:
        """Handle the button press to acknowledge a leak."""
        _LOGGER.info("Acknowledging leak for device %s", self.device["id"])
        try:
            await self.coordinator.api.acknowledge_leak(self.device["id"])
        # FIX (BLE001): Catch a specific, expected exception instead of 'Exception'.
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to acknowledge leak: %s", err)


class WaterGripButton(QuandifyButton):
    """Represents the acknowledge leak button for a Water Grip device."""


class CubicSecureButton(QuandifyButton):
    """Represents the acknowledge leak button for a CubicSecure device."""


class CubicDetectorButton(QuandifyButton):
    """Represents the acknowledge leak button for a CubicDetector device."""
