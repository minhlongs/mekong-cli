# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Auth Configuration - Environment-aware authentication settings."""

import os
import secrets
from pathlib import Path
from typing import Any, Dict

from src.auth.config_template import (
    ENV_VARS,
    AuthEnvironment,
    OAuthProviderConfig,
    get_env_template,
)


class AuthConfig:
    """Environment-aware authentication configuration."""

    ENVIRONMENT = AuthEnvironment(os.getenv("AUTH_ENVIRONMENT", "dev"))
    AUTH_DISABLED = ENVIRONMENT == AuthEnvironment.DEV

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    if not JWT_SECRET_KEY:
        if os.environ.get("AUTH_ENVIRONMENT", "dev") != "dev":
            raise ValueError(
                "JWT_SECRET_KEY environment variable is required for staging/production. "
                "Generate a secure random string (min 32 characters) and set it."
            )
        _secret_file = Path.home() / ".mekong" / ".jwt_secret"
        try:
            _secret_file.parent.mkdir(parents=True, exist_ok=True)
            if _secret_file.exists():
                JWT_SECRET_KEY = _secret_file.read_text().strip()
            else:
                JWT_SECRET_KEY = secrets.token_urlsafe(32)
                _secret_file.write_text(JWT_SECRET_KEY)
                os.chmod(_secret_file, 0o600)
        except OSError:
            JWT_SECRET_KEY = secrets.token_urlsafe(32)
    JWT_ALGORITHM = "HS256"
    JWT_KEY_ID = "mekong-key-1"
    JWT_ACCESS_EXPIRY_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRY_MINUTES", "30"))
    JWT_REFRESH_EXPIRY_DAYS = int(os.getenv("JWT_REFRESH_EXPIRY_DAYS", "7"))

    SESSION_COOKIE_NAME = "session_token"
    SESSION_COOKIE_SECURE = ENVIRONMENT == AuthEnvironment.PRODUCTION
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "lax" if ENVIRONMENT != AuthEnvironment.PRODUCTION else "none"
    SESSION_MAX_AGE = int(os.getenv("SESSION_MAX_AGE_SECONDS", "604800"))

    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv(
        "GOOGLE_REDIRECT_URI",
        "http://localhost:8080/auth/google/callback",
    )

    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
    GITHUB_REDIRECT_URI = os.getenv(
        "GITHUB_REDIRECT_URI",
        "http://localhost:8080/auth/github/callback",
    )

    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_IDS = os.getenv("STRIPE_PRICE_IDS", "{}")

    @classmethod
    def _current_environment(cls) -> AuthEnvironment:
        """Get current environment, reading from env at call time."""
        return AuthEnvironment(os.getenv("AUTH_ENVIRONMENT", cls.ENVIRONMENT.value))

    @classmethod
    def is_dev_mode(cls) -> bool:
        """Check if running in development mode."""
        return cls._current_environment() == AuthEnvironment.DEV

    @classmethod
    def is_staging_mode(cls) -> bool:
        """Check if running in staging mode."""
        return cls._current_environment() == AuthEnvironment.STAGING

    @classmethod
    def is_production_mode(cls) -> bool:
        """Check if running in production mode."""
        return cls._current_environment() == AuthEnvironment.PRODUCTION

    @classmethod
    def require_auth(cls) -> bool:
        """Check if authentication is required."""
        return not cls.is_dev_mode()

    @classmethod
    def auth_enabled(cls) -> bool:
        """Alias for require_auth()."""
        return cls.require_auth()

    @classmethod
    def is_production(cls) -> bool:
        """Check if environment is production."""
        return cls.is_production_mode()

    @classmethod
    def get_oauth_config(cls) -> Dict[str, OAuthProviderConfig]:
        """Get OAuth provider configurations."""
        return {
            "google": OAuthProviderConfig(
                client_id=cls.GOOGLE_CLIENT_ID,
                client_secret=cls.GOOGLE_CLIENT_SECRET,
                redirect_uri=cls.GOOGLE_REDIRECT_URI,
                enabled=bool(cls.GOOGLE_CLIENT_ID and cls.GOOGLE_CLIENT_SECRET),
            ),
            "github": OAuthProviderConfig(
                client_id=cls.GITHUB_CLIENT_ID,
                client_secret=cls.GITHUB_CLIENT_SECRET,
                redirect_uri=cls.GITHUB_REDIRECT_URI,
                enabled=bool(cls.GITHUB_CLIENT_ID and cls.GITHUB_CLIENT_SECRET),
            ),
        }

    @classmethod
    def validate_production_config(cls) -> tuple[bool, list[str]]:
        """Validate that required secrets are set for production."""
        warnings = []
        if cls.is_production_mode():
            if not cls.JWT_SECRET_KEY or len(cls.JWT_SECRET_KEY) < 32:
                warnings.append(
                    "JWT_SECRET_KEY is not set or too short (< 32 characters). "
                    "Use a secure random string for production."
                )
            if not cls.GOOGLE_CLIENT_ID or not cls.GOOGLE_CLIENT_SECRET:
                warnings.append("Google OAuth credentials not configured")
            if not cls.GITHUB_CLIENT_ID or not cls.GITHUB_CLIENT_SECRET:
                warnings.append("GitHub OAuth credentials not configured")
            if not cls.STRIPE_SECRET_KEY:
                warnings.append("STRIPE_SECRET_KEY not configured")

        return len(warnings) == 0, warnings

    @classmethod
    def get_config_summary(cls) -> Dict[str, Any]:
        """Get human-readable config summary."""
        is_valid, warnings = cls.validate_production_config()
        oauth_config = cls.get_oauth_config()
        return {
            "environment": cls.ENVIRONMENT.value,
            "auth_enabled": cls.require_auth(),
            "is_production": cls.is_production_mode(),
            "cookie_secure": cls.SESSION_COOKIE_SECURE,
            "oauth_providers": {
                name: {
                    "enabled": config.enabled,
                    "configured": bool(config.client_id and config.client_secret),
                }
                for name, config in oauth_config.items()
            },
            "config_valid": is_valid,
            "warnings": warnings,
        }


__all__ = [
    "AuthConfig",
    "AuthEnvironment",
    "ENV_VARS",
    "OAuthProviderConfig",
    "get_env_template",
]
