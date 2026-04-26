"""Unit tests for seed/config.py — ENV var overrides."""

import os
import importlib
import sys

import pytest


def _reload_config(monkeypatch, **env_overrides):
    """Reload seed.config with patched env vars."""
    for k, v in env_overrides.items():
        monkeypatch.setenv(k, v)
    # Remove cached module so ENV vars take effect
    for mod in list(sys.modules.keys()):
        if mod.startswith("seed.config") or mod == "seed.config":
            del sys.modules[mod]
    import seed.config as cfg
    return cfg


def test_default_ollama_url():
    import seed.config as cfg
    assert cfg.OLLAMA_BASE_URL  # non-empty
    assert "http" in cfg.OLLAMA_BASE_URL


def test_env_override_ollama_url(monkeypatch):
    cfg = _reload_config(monkeypatch, OLLAMA_BASE_URL="http://custom-host:11434")
    assert cfg.OLLAMA_BASE_URL == "http://custom-host:11434"


def test_env_override_llm_model(monkeypatch):
    cfg = _reload_config(monkeypatch, LLM_MODEL="llama3:8b")
    assert cfg.LLM_MODEL == "llama3:8b"


def test_env_override_embed_model(monkeypatch):
    cfg = _reload_config(monkeypatch, EMBED_MODEL="nomic-embed-text:latest")
    assert cfg.EMBED_MODEL == "nomic-embed-text:latest"


def test_env_override_timeout(monkeypatch):
    cfg = _reload_config(monkeypatch, LLM_TIMEOUT="30")
    assert cfg.LLM_TIMEOUT == 30


def test_default_paths_are_strings():
    import seed.config as cfg
    assert isinstance(cfg.CHROMA_PATH, str)
    assert isinstance(cfg.SQLITE_PATH, str)
    assert isinstance(cfg.OUTPUTS_DIR, str)
