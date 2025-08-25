"""Button platform for Quandify integration."""
import logging
from typing import Any

import aiohttp
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator
from .entity import QuandifyEntity
from .models import QuandifyDevice

_LOGGER = logging.getLogger(__name__)

# List of device models that support the acknowledge leak button
BUTTON_SUPPORTING_DEVICES = ["Water Grip", "CubicSecure", "CubicDetector"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the button entities."""
    coordinator: QuandifyDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[QuandifyAcknowledgeLeakButton] = []
    for device in coordinator.devices:
        if device.model in BUTTON_SUPPORTING_DEVICES:
            entities.append(QuandifyAcknowledgeLeakButton(coordinator, device))
    async_add_entities(entities)


class QuandifyAcknowledgeLeakButton(QuandifyEntity, ButtonEntity):
    """Implementation of the Acknowledge Leak button."""

    _attr_name = "Acknowledge leak"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:bell-cancel"

    def __init__(self, coordinator: QuandifyDataUpdateCoordinator, device: QuandifyDevice):
        """Initialize the button."""
        super().__init__(coordinator, device)
        self._attr_unique_id = f"{self.device.id}_acknowledge_leak"

    async def async_press(self) -> None:
        """Handle the button press to acknowledge a leak."""
        _LOGGER.info("Acknowledging leak for device %s", self.device.id)
        try:
            await self.coordinator.api.acknowledge_leak(self.device.id)
        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to acknowledge leak: %s", err)
