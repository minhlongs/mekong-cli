"""Settings: env vars, defaults, secret enforcement."""

from __future__ import annotations

import pytest


def test_from_env_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("FOREST_TESTING", "1")
    monkeypatch.setenv("FOREST_OUTPUTS", str(tmp_path / "out"))
    from agent_forest.config import ForestSettings

    s = ForestSettings.from_env()
    assert s.redis_url == "redis://localhost:6379"
    assert s.jwt_algorithm == "HS256"
    assert s.rate_limit_per_minute == 60
    assert s.outputs_dir.exists()


def test_from_env_requires_secret_when_not_testing(monkeypatch, tmp_path):
    monkeypatch.delenv("FOREST_TESTING", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.setenv("FOREST_OUTPUTS", str(tmp_path / "out"))
    from agent_forest.config import ForestSettings

    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        ForestSettings.from_env()


def test_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("FOREST_TESTING", "1")
    monkeypatch.setenv("REDIS_URL", "redis://other:1234")
    monkeypatch.setenv("FOREST_RATE_LIMIT_PER_MINUTE", "7")
    monkeypatch.setenv("FOREST_OUTPUTS", str(tmp_path / "out"))
    from agent_forest.config import ForestSettings

    s = ForestSettings.from_env()
    assert s.redis_url == "redis://other:1234"
    assert s.rate_limit_per_minute == 7
