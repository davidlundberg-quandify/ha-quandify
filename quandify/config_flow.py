"""Config flow for Quandify integration."""
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import QuandifyAPI
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

_LOGGER = logging.getLogger(__name__)


class QuandifyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Quandify."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> dict[str, Any]:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            # FIX: The constructor call now matches the updated QuandifyAPI class.
            api = QuandifyAPI(session, {})

            try:
                auth_data = await api.login(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
            except aiohttp.ClientResponseError as err:
                if err.status in (401, 404):
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
                self._abort_if_unique_id_configured()

                entry_data = {**user_input, **auth_data}
                entry_data.pop(CONF_PASSWORD)

                return self.async_create_entry(
                    title=user_input[CONF_EMAIL],
                    data=entry_data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )
