# Skip all integration tests if required dependencies are not installed.
# Integration tests require: pydantic-settings, pytest-asyncio, sentry-sdk, falkordb
import pytest

pydantic_settings = pytest.importorskip(
    "pydantic_settings",
    reason="pydantic-settings not installed, skipping integration tests",
)
