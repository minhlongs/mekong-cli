"""Sentry error tracking initialization."""
import os
import sentry_sdk


def init_sentry() -> None:
    """Initialize Sentry if DSN is configured."""
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        return
    sentry_sdk.init(
        dsn=dsn,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "development"),
        release=os.getenv("APP_VERSION", "0.0.0"),
    )
