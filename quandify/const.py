"""Constants for the Quandify Water Grip integration."""

from typing import Final

DOMAIN: Final = "watergrip"
ATTRIBUTION: Final = "Data provided by Quandify"

# API Endpoints
AUTH_BASE_URL: Final = "https://auth.quandify.com"
API_BASE_URL: Final = "https://api.prod.quandify.com"

# Configuration Constants
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_CLIENT_ID: Final = "client_id"
CONF_CLIENT_SECRET: Final = "client_secret"
CONF_ID_TOKEN: Final = "id_token"
CONF_REFRESH_TOKEN: Final = "refresh_token"
CONF_EXP: Final = "exp"
CONF_WEBHOOK_ID: Final = "webhook_id"

# Data Update Coordinator
UPDATE_INTERVAL_MINUTES: Final = 10
