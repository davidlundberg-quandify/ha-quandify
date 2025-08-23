"""The Quandify Water Grip integration."""

import logging

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import QuandifyWaterGripAPI
from .const import CONF_WEBHOOK_ID, DOMAIN
from .coordinator import WaterGripDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Quandify Water Grip from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)

    # Pass the full entry data to the API class
    api = QuandifyWaterGripAPI(hass, session, dict(entry.data))

    try:
        # The API class now handles getting account info and org ID internally
        devices = await api.get_devices()
    # FIX: Catch a specific, expected exception instead of the generic 'Exception'.
    except aiohttp.ClientError as err:
        # This will cause Home Assistant to retry the setup later.
        raise ConfigEntryNotReady(f"Failed to get devices: {err}") from err

    coordinator = WaterGripDataUpdateCoordinator(hass, api, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Webhook setup
    try:
        webhook_id = f"watergrip_{entry.entry_id}"
        hass.components.webhook.async_register(
            DOMAIN, "Quandify Water Grip", webhook_id, coordinator.handle_webhook
        )
        webhook_url = hass.components.webhook.async_generate_url(webhook_id)
        registered_webhook_id = await api.register_webhook(webhook_url)

        if registered_webhook_id:
            new_data = {**entry.data, CONF_WEBHOOK_ID: registered_webhook_id}
            hass.config_entries.async_update_entry(entry, data=new_data)

    # FIX: Catch a specific, expected exception.
    except aiohttp.ClientError as err:
        _LOGGER.warning("Could not register webhook, falling back to polling: %s", err)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    if webhook_id := entry.data.get(CONF_WEBHOOK_ID):
        try:
            hass.components.webhook.async_unregister(f"watergrip_{entry.entry_id}")
            session = async_get_clientsession(hass)
            api = QuandifyWaterGripAPI(hass, session, dict(entry.data))
            await api.delete_webhook(webhook_id)
        # FIX: Catch a specific, expected exception.
        except aiohttp.ClientError as err:
            _LOGGER.warning("Failed to unregister webhook: %s", err)

    return unload_ok
