"""Shared pytest fixtures for agent-forest."""

from __future__ import annotations

import os
from pathlib import Path

import fakeredis
import pytest

os.environ["FOREST_TESTING"] = "1"
os.environ.setdefault("JWT_SECRET=REDACTED_KEY", "unit-test-key")
# Keep worker tests off the network unless a test opts in by removing this var.
os.environ.setdefault("FOREST_SIGNALS_ENABLED", "0")


@pytest.fixture
def tmp_outputs(tmp_path: Path, monkeypatch) -> Path:
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    monkeypatch.setenv("FOREST_OUTPUTS", str(outputs))
    monkeypatch.setenv("FOREST_ALLOW_HTTP_WEBHOOKS", "1")
    return outputs


@pytest.fixture
def fake_redis() -> fakeredis.FakeRedis:
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def settings(tmp_outputs: Path, monkeypatch):
    from agent_forest.config import ForestSettings
    from agent_forest.gateway import deps

    monkeypatch.setenv("JWT_SECRET=REDACTED_KEY", "unit-test-key")
    deps.reset_caches()
    return ForestSettings.from_env()


@pytest.fixture
def client(fake_redis, settings, monkeypatch):
    """FastAPI TestClient wired to fakeredis + in-memory user store."""
    from fastapi.testclient import TestClient

    from agent_forest.gateway import deps
    from agent_forest.gateway.app import create_app

    deps.reset_caches()
    app = create_app()
    app.dependency_overrides[deps.get_redis_client] = lambda: fake_redis
    app.dependency_overrides[deps.get_settings] = lambda: settings
    return TestClient(app)
