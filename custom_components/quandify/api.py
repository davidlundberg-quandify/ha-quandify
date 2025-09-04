"""Quandify API client."""
import json
import logging
from typing import Any

import aiohttp
from homeassistant.exceptions import ConfigEntryAuthFailed

from .const import API_BASE_URL, AUTH_BASE_URL, CONF_ID_TOKEN, CONF_REFRESH_TOKEN
from .const import CONF_ACCOUNT_ID
from .const import CONF_ORGANISATION_ID

_LOGGER = logging.getLogger(__name__)


# Constants for the Google Firebase Authentication flow.
FIREBASE_API_KEY = "AIzaSyBtg2_5IGRECOthW5RUwc1AYVrRZErGM18"
FIREBASE_AUTH_BASE_URL = "https://identitytoolkit.googleapis.com/v1"
FIREBASE_TOKEN_URL = f"https://securetoken.googleapis.com/v1/token?key={FIREBASE_API_KEY}"
class QuandifyAPIError(Exception):
    """Generic Quandify API exception."""

class QuandifyAPI:
    """A class for interacting with the Quandify API."""

    def __init__(self, session: aiohttp.ClientSession, config: dict[str, Any]):
        """Initialize the API client."""
        self.session = session
        self._config = config
        self._api_header: str = self._set_api_header()

    def _set_api_header(self) -> None:
        """Set the API headers from the current config."""
        id_token = self._config.get(CONF_ID_TOKEN)
        self._api_header = {"Authorization": f"Bearer {id_token}"} if id_token else {}
        _LOGGER.info("Successfully refreshed authentication token")

    async def _firebase_auth(self, email: str, password: str) -> dict[str, Any]:
        """Perform the full Firebase authentication flow to get all necessary IDs."""
        try:
            # Step 1: Sign in to Firebase to get the initial tokens.
            signin_url = f"{FIREBASE_AUTH_BASE_URL}/accounts:signInWithPassword?key={FIREBASE_API_KEY}"
            signin_payload = {"email": email, "password": password, "returnSecureToken": True}
            _LOGGER.debug("Step 1/2: Attempting Firebase sign-in for %s", email)
            response = await self.session.post(signin_url, json=signin_payload)
            response.raise_for_status()
            signin_data = await response.json()
            firebase_id_token = signin_data["idToken"]

            # Step 2: Look up the full account info using the token from Step 1.
            lookup_url = f"{FIREBASE_AUTH_BASE_URL}/accounts:lookup?key={FIREBASE_API_KEY}"
            lookup_payload = {"idToken": firebase_id_token}
            _LOGGER.debug("Step 2/2: Looking up Firebase account to find custom attributes")
            response = await self.session.post(lookup_url, json=lookup_payload)
            response.raise_for_status()
            lookup_data = await response.json()

            # Step 3: Extract the Quandify accountId from the customAttributes string.
            user_info = lookup_data.get("users", [{}])[0]
            custom_attributes_str = user_info.get("customAttributes", "{}")
            custom_attributes = json.loads(custom_attributes_str)
            account_id = custom_attributes.get("accountId")

            if not account_id:
                raise ConfigEntryAuthFailed("Could not find Quandify accountId in user profile")
                
            return {
                "account_id": account_id,
                "id_token": firebase_id_token,
                "refresh_token": signin_data["refreshToken"],
            }
        
        except aiohttp.ClientError as err:
            _LOGGER.error("A connection error occurred during authentication: %s", err)
            raise QuandifyAPIError(f"Connection error: {err}") from err
        
        except (KeyError, json.JSONDecodeError) as err:
            _LOGGER.error("Received an unexpected response from the authentication API: %s", err)
            raise QuandifyAPIError("Unexpected API response during login.") from err

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Log in to the Quandify API, performing the full authentication flow."""
        try:
            if not self._config.get(CONF_ACCOUNT_ID):
                f_base = await self._firebase_auth(email, password)
                self._config[CONF_ACCOUNT_ID] = f_base["account_id"]

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to authenticate via Firebase: %s", err)
            raise QuandifyAPIError("Failed to authenticate via Firebase") from err
        
        try:
            if not self._config.get(CONF_ID_TOKEN):
                auth_data = await self.auth(f_base["account_id"], password)
                self._config[CONF_REFRESH_TOKEN] = auth_data["refresh_token"]
                self._config[CONF_ID_TOKEN] = auth_data["id_token"]
                self._set_api_header()
  
        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to authenticate to Quandify API: %s", err)
            raise QuandifyAPIError("Failed to authenticate to Quandify API") from err
        
        try:
            if not self._config.get(CONF_ORGANISATION_ID):
                organization_id = await self.get_organization_id()
                self._config[CONF_ORGANISATION_ID] = organization_id

        except (aiohttp.ClientError, ValueError) as err:
            _LOGGER.error("Failed to get account info after login: %s", err)
            raise QuandifyAPIError("Failed to get account info after login") from err

        return self._config
    

    async def _refresh(self) -> bool:
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
            self._set_api_header()

        return True

    async def _request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Make a request, handling token refresh on 401 errors."""
        try:
            response = await self.session.request(method, url, headers=self._api_header, **kwargs)
            response.raise_for_status()
            return await response.json() if response.content_type == "application/json" else await response.text()
        except QuandifyAPIError as err:
            raise QuandifyAPIError("Unexpected API response during login.") from err

    
    async def auth(self, account_id: str, password: str) -> dict[str, Any]:
        """Authenticate to the Quandify API."""
        url = f"{AUTH_BASE_URL}/"
        payload = {"account_id": account_id, "password": password}
        _LOGGER.debug("Attempting to authenticate to %s", url)
        response = await self.session.post(url, json=payload)
        response.raise_for_status()
        return await response.json()

    async def get_organization_id(self) -> None:
        """Fetch account details to get the organizationId."""
        account_id = self._config.get(CONF_ACCOUNT_ID)
        url = f"{AUTH_BASE_URL}/accounts/{account_id}"
        response = await self._request("get", url)
        return response.get("organizationId")

    async def get_devices(self) -> list[dict[str, Any]]:
        """Fetch the list of devices."""
        organization_id = self._config.get(CONF_ORGANISATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/"
        response = await self._request("get", url)
        return response.get("data", [])

    async def get_device_info(self, device_id: str) -> dict[str, Any]:
        """Get all info for a single device."""
        organization_id = self._config.get(CONF_ORGANISATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/{device_id}"
        return await self._request("get", url)

    async def acknowledge_leak(self, device_id: str) -> None:
        """Acknowledge a leak."""
        organization_id = self._config.get(CONF_ORGANISATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/{device_id}/commands/acknowledge-alarm"
        await self._request("post", url)

    async def open_valve(self, device_id: str) -> None:
        """Open the valve on a device."""
        organization_id = self._config.get(CONF_ORGANISATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/{device_id}/commands/open-valve"
        await self._request("post", url)

    async def close_valve(self, device_id: str) -> None:
        """Close the valve on a device."""
        organization_id = self._config.get(CONF_ORGANISATION_ID)
        url = f"{API_BASE_URL}/organization/{organization_id}/devices/{device_id}/commands/close-valve"
        await self._request("post", url)
