"""The Quandify Water Grip integration."""
import logging

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components import webhook

from .api import QuandifyWaterGripAPI
from .const import DOMAIN, CONF_WEBHOOK_ID
from .coordinator import WaterGripDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Quandify Water Grip from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    session = async_get_clientsession(hass)
    
    api = QuandifyWaterGripAPI(hass, session, dict(entry.data))

    try:
        devices = await api.get_devices()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady(f"Failed to get devices: {err}") from err

    coordinator = WaterGripDataUpdateCoordinator(hass, api, devices)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Webhook setup
    try:
        webhook_id = f"quandify_{entry.entry_id}"
        webhook.async_register(
            hass, DOMAIN, "Quandify", webhook_id, coordinator.handle_webhook
        )
        webhook_url = webhook.async_generate_url(hass, webhook_id)
        registered_webhook_id = await api.register_webhook(webhook_url)

        if registered_webhook_id:
            new_data = {**entry.data, CONF_WEBHOOK_ID: registered_webhook_id}
            hass.config_entries.async_update_entry(entry, data=new_data)

    # FIX: Removed the non-existent 'WebhookException'.
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
            webhook.async_unregister(hass, f"quandify_{entry.entry_id}")
            session = async_get_clientsession(hass)
            api = QuandifyWaterGripAPI(hass, session, dict(entry.data))
            await api.delete_webhook(webhook_id)
        except aiohttp.ClientError as err:
            _LOGGER.warning("Failed to unregister webhook: %s", err)

    return unload_ok