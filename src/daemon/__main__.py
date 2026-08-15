"""Allow running: python3 -m src.daemon.heartbeat_scheduler"""
import os

import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN", ""),
    traces_sample_rate=0.2,
    environment="production",
    release=os.getenv("SENTRY_RELEASE", "mekong-cli@6.0.0"),
)

import asyncio  # noqa: E402

from src.daemon.heartbeat_scheduler import main  # noqa: E402

asyncio.run(main())
