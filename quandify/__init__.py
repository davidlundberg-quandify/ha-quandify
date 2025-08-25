"""The Quandify integration."""
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import QuandifyAPI
from .const import DOMAIN
from .coordinator import QuandifyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Quandify devices from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)

    api = QuandifyAPI(hass, session, dict(entry.data))

    try:
        devices = await api.get_devices()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady(f"Failed to get devices: {err}") from err

    coordinator = QuandifyDataUpdateCoordinator(hass, api, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
