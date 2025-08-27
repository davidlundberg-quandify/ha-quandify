"""Quandify API client."""
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import API_BASE_URL, AUTH_BASE_URL, CONF_ID_TOKEN, CONF_REFRESH_TOKEN

_LOGGER = logging.getLogger(__name__)


class QuandifyAPI:
    """A class for interacting with the Quandify API."""

    # FIX: Removed the unnecessary 'hass' argument from the constructor.
    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]):
        """Initialize the API client."""
        self.session = session
        self._config = config
        self._api_headers = {
            "Authorization": f"Bearer {self._config.get(CONF_ID_TOKEN)}"}
        self.account_id: str | None = self._config.get("email")
        self.organization_id: str | None = None

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate to the Quandify API."""
        url = f"{AUTH_BASE_URL}/"
        payload = {"account_id": email, "password": password}
        _LOGGER.debug("Attempting to authenticate to %s", url)
        response = await self.session.post(url, json=payload)
        response.raise_for_status()
        self.account_id = email
        return await response.json()

    async def refresh_token(self) -> bool:
        """Refresh the authentication token."""
        url = f"{AUTH_BASE_URL}/refresh"
        payload = {"refresh_token": self._config.get(CONF_REFRESH_TOKEN)}
        _LOGGER.debug("Attempting to refresh token")

        try:
            response = await self.session.post(url, json=payload)
            response.raise_for_status()
            data: dict[str, Any] = await response.json()

        except aiohttp.ClientError as err:
            _LOGGER.error("Failed to refresh token: %s", err)
            raise ConfigEntryAuthFailed("Failed to refresh token") from err

        else:
            self._config[CONF_ID_TOKEN] = data["id_token"]
            self._config[CONF_REFRESH_TOKEN] = data["refresh_token"]
            self._api_headers["Authorization"] = f"Bearer {self._config[CONF_ID_TOKEN]}"
            _LOGGER.info("Successfully refreshed authentication token")

            return True

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make a request, handling token refresh on 401 errors."""
        try:
            response = await self.session.request(method, url, headers=self._api_headers, **kwargs)
            response.raise_for_status()
            return await response.json() if response.content_type == "application/json" else await response.text()
        except aiohttp.ClientResponseError as err:
            if err.status == 401:
                _LOGGER.info("Token expired or invalid, attempting refresh")
                if await self.refresh_token():
                    _LOGGER.info("Token refreshed, retrying the request")
                    # After a successful refresh, retry the original request
                    response = await self.session.request(
                        method,
                        url,
                        headers=self._api_headers,
                        **kwargs
                    )
                    response.raise_for_status()
                    return await response.json() if response.content_type == "application/json" else await response.text()
            raise

    async def get_account_info(self) -> None:
        """Fetch account details to get the organizationId."""
        if not self.account_id:
            raise ValueError("Cannot get account info, account ID is missing.")
        url = f"{AUTH_BASE_URL}/accounts/{self.account_id}"
        _LOGGER.debug("Getting account info from %s", url)
        account_data = await self._request("get", url)
        self.organization_id = account_data.get("organizationId")
        if not self.organization_id:
            raise ValueError(
                "Failed to retrieve organizationId from account info.")

        _LOGGER.info("Found organizationId: %s", self.organization_id)

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch the list of devices."""
        if not self.organization_id:
            await self.get_account_info()
        url = f"{API_BASE_URL}/organization/{self.organization_id}/devices/"
        _LOGGER.debug("Getting devices from URL: %s", url)
        response = await self._request("get", url)
        return response.get("data", [])

    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get all info for a single device."""
        url = f"{API_BASE_URL}/organization/{self.organization_id}/devices/{device_id}"
        return await self._request("get", url)

    async def acknowledge_leak(self, device_id: str) -> None:
        """Acknowledge a leak."""
        url = f"{API_BASE_URL}/organization/{self.organization_id}/devices/{device_id}/commands/acknowledge-alarm"
        await self._request("post", url)

    async def open_valve(self, device_id: str) -> None:
        """Open the valve on a device."""
        url = f"{API_BASE_URL}/organization/{self.organization_id}/devices/{device_id}/commands/open-valve"
        await self._request("post", url)

    async def close_valve(self, device_id: str) -> None:
        """Close the valve on a device."""
        url = f"{API_BASE_URL}/organization/{self.organization_id}/devices/{device_id}/commands/close-valve"
        await self._request("post", url)
