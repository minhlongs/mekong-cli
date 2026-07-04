"""
Environment Validator — Startup env check for required secrets.

Validates required environment variables at application startup.
Fail-fast behavior: raises EnvironmentError with clear message if
required vars are missing or too short.

Usage:
    from src.auth.env_validator import validate_startup_env
    validate_startup_env()  # call once at FastAPI startup

    # Or validate individual vars:
    from src.auth.env_validator import require_env
    secret = require_env("JWT_SECRET", min_bytes=32)
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


def require_env(name: str, min_bytes: int = 0) -> str:
    """Return env var value, raising EnvironmentError if missing or too short.

    Args:
        name: Environment variable name.
        min_bytes: Minimum byte length required (default 0 = no minimum).

    Returns:
        The environment variable value.

    Raises:
        EnvironmentError: If the var is missing or shorter than min_bytes.

    Note:
        Does NOT log the value — only logs the var name for security.
    """
    value = os.getenv(name)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{name}' is not set. "
            f"See .env.example for setup instructions."
        )
    if min_bytes > 0 and len(value.encode()) < min_bytes:
        raise EnvironmentError(
            f"Environment variable '{name}' is too short: "
            f"got {len(value.encode())} bytes, need at least {min_bytes}. "
            f"Generate a secure value with: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
        )
    return value


def _is_test_or_ci() -> bool:
    """Return True if running in test or CI context."""
    return bool(
        os.getenv("CI") == "true"
        or os.getenv("PYTEST_CURRENT_TEST")
        or os.getenv("TESTING")
    )


def validate_startup_env() -> None:
    """Validate required environment variables at application startup.

    In development (AUTH_ENVIRONMENT=dev or unset), missing JWT_SECRET
    emits a WARNING but does not exit — session_manager provides a CI-safe
    fallback that is NOT used in production.

    In staging/production, missing or short JWT_SECRET raises EnvironmentError
    which should be caught by the FastAPI startup handler to exit(1).

    Raises:
        EnvironmentError: In staging/production if JWT_SECRET missing or < 32 bytes.
    """
    auth_env = os.getenv("AUTH_ENVIRONMENT", "dev").lower()
    is_production_grade = auth_env in ("staging", "production")

    jwt_secret = os.getenv("JWT_SECRET")

    if is_production_grade:
        # Hard requirement in staging/production
        require_env("JWT_SECRET", min_bytes=32)
        logger.info("JWT_SECRET validated for %s environment.", auth_env)
    elif not jwt_secret:
        if _is_test_or_ci():
            logger.debug("JWT_SECRET not set — using CI test fallback.")
        else:
            logger.warning(
                "JWT_SECRET not set. A random secret is used for this dev session "
                "and will change on restart. Set JWT_SECRET in .env for stable local dev. "
                "NEVER run without JWT_SECRET in production."
            )
    elif len(jwt_secret.encode()) < 32:
        logger.warning(
            "JWT_SECRET is set but shorter than 32 bytes (%d bytes). "
            "Acceptable in dev; REQUIRED to be ≥32 bytes in production.",
            len(jwt_secret.encode()),
        )
    else:
        logger.debug("JWT_SECRET validated.")
