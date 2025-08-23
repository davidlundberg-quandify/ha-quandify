"""DataUpdateCoordinator for the Quandify integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp.web
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import QuandifyWaterGripAPI
from .const import DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class WaterGripDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: QuandifyWaterGripAPI,
        devices: list[dict[str, Any]],
    ):
        """Initialize."""
        self.api = api
        self.devices = devices
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library by polling."""
        try:
            async with asyncio.timeout(30):
                if not self.api.organization_id:
                    await self.api.get_account_info()

                data = {}
                for device in self.devices:
                    device_id = device["id"]
                    device_info = await self.api.get_device_info(device_id)
                    data[device_id] = device_info
                return data
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}") from exception

    async def handle_webhook(self, hass: HomeAssistant, webhook_id: str, request: aiohttp.web.Request) -> None:
        """Handle incoming webhook with real-time device data."""
        _LOGGER.debug("Received webhook: %s", webhook_id)
        try:
            data = await request.json()
            _LOGGER.debug("Webhook payload: %s", data)
        except ValueError:
            _LOGGER.warning("Received invalid JSON in webhook")
            return

        # Assuming the webhook payload contains the full device info structure
        device_id = data.get("id")
        if not device_id:
            _LOGGER.warning("Webhook payload missing device ID")
            return

        # Create a copy of the current data and update it with the new payload
        updated_data = self.data.copy()
        updated_data[device_id] = data
        
        # Push the new data to all listeners (entities)
        self.async_set_updated_data(updated_data)