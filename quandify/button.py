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
from .coordinator import QuandifyDataUpdateCoordinator
from .util import get_device_profile

_LOGGER = logging.getLogger(__name__)

# Define a mapping from the profile key (from util.py) to the button class
PROFILE_TO_CLASS = {
    "cubic_detector": "CubicDetectorButton",
    "water_grip": "WaterGripButton",
    "cubic_secure": "CubicSecureButton",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button entities based on device class."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[ButtonEntity] = []

    for device in coordinator.devices:
        device_name, profile_key = get_device_profile(device)

        class_name = PROFILE_TO_CLASS.get(profile_key)
        if class_name:
            button_class = globals()[class_name]
            entities.append(button_class(coordinator, device, device_name))

    async_add_entities(entities)


class QuandifyButton(CoordinatorEntity[QuandifyDataUpdateCoordinator], ButtonEntity):
    """Base button entity for all Quandify devices."""

    def __init__(
        self,
        coordinator: QuandifyDataUpdateCoordinator,
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
        }

    async def async_press(self) -> None:
        """Handle the button press to acknowledge a leak."""
        _LOGGER.info("Acknowledging leak for device %s", self.device["id"])
        try:
            await self.coordinator.api.acknowledge_leak(self.device["id"])
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to acknowledge leak: %s", err)


class WaterGripButton(QuandifyButton):
    pass


class CubicSecureButton(QuandifyButton):
    pass


class CubicDetectorButton(QuandifyButton):
    pass
