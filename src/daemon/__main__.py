# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

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
