# Skip all backend tests if required dependencies are not installed.
# Backend tests require: pydantic-settings, redis, python-jose, cryptography, supabase
import pytest

pydantic_settings = pytest.importorskip(
    "pydantic_settings",
    reason="pydantic-settings not installed, skipping backend tests",
)
