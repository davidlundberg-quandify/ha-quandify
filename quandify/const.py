"""Constants for the Quandify integration."""

from typing import Final

DOMAIN: Final = "quandify"

# API Endpoints
AUTH_BASE_URL: Final = "https://auth.quandify.com"
API_BASE_URL: Final = "https://api.prod.quandify.com"

# Configuration Constants
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_ID_TOKEN: Final = "id_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"

# Data Update Coordinator
UPDATE_INTERVAL_MINUTES: Final = 10