"""DataUpdateCoordinator for the Quandify Water Grip integration."""

import asyncio
from datetime import timedelta
import logging
from typing import Any

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
        """Update data via library."""
        try:
            # FIX (TID251): Use the built-in asyncio.timeout instead of async_timeout.
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
            raise UpdateFailed(
                f"Error communicating with API: {exception}"
            ) from exception
