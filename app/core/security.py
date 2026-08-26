from __future__ import annotations

from typing import Any

from app.core.config import Settings
from app.core.exceptions import ConfigurationError

SENSITIVE_KEYS: set[str] = {"key", "secret", "password", "token", "api_key", "authorization"}


def redact_sensitive(data: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive values from a dictionary.
    
    Returns a copy of the dictionary with sensitive values replaced by "***REDACTED***".
    Key matching is case-insensitive.
    
    Args:
        data: The dictionary to redact.
        
    Returns:
        A new dictionary with redacted values.
    """
    redacted_data = data.copy()
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in SENSITIVE_KEYS):
            redacted_data[key] = "***REDACTED***"
        elif isinstance(value, dict):
            redacted_data[key] = redact_sensitive(value)
    return redacted_data


def validate_production_config(settings: Settings) -> None:
    """Validate configuration for production environment.
    
    Ensures that SQLite is not used in production.
    
    Args:
        settings: The application settings.
        
    Raises:
        ConfigurationError: If the configuration is invalid for production.
    """
    if settings.APP_ENV.lower() == "production":
        if settings.DATABASE_URL.startswith("sqlite"):
            raise ConfigurationError(
                message="SQLite is not allowed in production environment.",
                details={"DATABASE_URL": "***REDACTED***"}
            )
