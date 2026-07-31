"""License secret loading and fallback warning policy."""

from __future__ import annotations

import base64
import os

from src.core.logging_config import get_logger

logger = get_logger(__name__)


def load_license_secret() -> tuple[str, bool]:
    """Load HMAC license secret and report whether dev fallback is active."""
    secret = os.getenv("LICENSE_SECRET", os.getenv("DEV_LICENSE_FALLBACK", ""))
    if secret:
        return secret, False

    fallback = base64.b64decode("ZGV2LXNlY3JldC1rZXktbm90LWZvci1wcm9kdWN0aW9u").decode()
    return fallback, True


def should_warn_missing_secret(using_dev_fallback: bool) -> bool:
    """Return true when fallback license secret should be visible to operators."""
    return (
        using_dev_fallback
        and os.getenv("TESTING", "").lower() != "true"
        and os.getenv("CI", "").lower() != "true"
    )


def warn_missing_secret_if_needed(using_dev_fallback: bool) -> None:
    """Warn operators when production-grade license secret is absent."""
    if not should_warn_missing_secret(using_dev_fallback):
        return
    logger.warning(
        "license_generator.missing_secret: %s",
        "LICENSE_SECRET not set. Using dev key. "
        "Set LICENSE_SECRET env var in production.",
    )


__all__ = ["load_license_secret", "should_warn_missing_secret", "warn_missing_secret_if_needed"]
