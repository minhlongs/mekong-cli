"""Tests for mekongd.config."""

from __future__ import annotations

from pathlib import Path

import pytest

from mekongd.config import MekongdConfig, PolicyConfig, load_config


def test_defaults():
    cfg = MekongdConfig()
    assert cfg.api_host == "127.0.0.1"
    assert cfg.api_port == 8765
    assert cfg.model_name.startswith("Qwen/")
    assert cfg.anthropic_fallback_url == "https://api.anthropic.com"
    assert cfg.policy.default_destination == "local"
    assert len(cfg.policy.local_patterns) > 0
    assert len(cfg.policy.cloud_patterns) > 0


def test_env_override(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("MEKONGD_API_PORT", "9999")
    monkeypatch.setenv("MEKONGD_ANTHROPIC_API_KEY", "sk-test")
    cfg = MekongdConfig()
    assert cfg.api_port == 9999
    assert cfg.anthropic_api_key == "sk-test"


def test_load_config_missing_file(tmp_path: Path):
    """Missing TOML file → fall back to defaults."""
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg.api_port == 8765


def test_load_config_toml(tmp_path: Path):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(
        '''
api_host = "0.0.0.0"
api_port = 7777
model_name = "Qwen/custom"
'''
    )
    cfg = load_config(toml_path)
    assert cfg.api_host == "0.0.0.0"
    assert cfg.api_port == 7777
    assert cfg.model_name == "Qwen/custom"


def test_policy_default():
    p = PolicyConfig()
    assert p.default_destination == "local"
    assert any("read" in pat for pat in p.local_patterns)
    assert any("plan" in pat for pat in p.cloud_patterns)


def test_policy_invalid_default():
    with pytest.raises(ValueError):
        PolicyConfig(default_destination="martian")
