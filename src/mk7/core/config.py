"""Mekong CLI 7 — config management.

~/.mekong/config.json stores gateway connection + default model.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("MEKONG_CONFIG_DIR", Path.home() / ".mekong"))
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "base_url": "http://omnimbp.local:20128",
    "token": "sk-b9eb30e8d08b6389-bdc6e3-a980fe1f",
    "default_model": "claude-fable-5",
    "strategist_model": "strategist",
    "version": 1,
}


def load() -> dict:
    if not CONFIG_FILE.exists():
        return dict(DEFAULT_CONFIG)
    try:
        data = json.loads(CONFIG_FILE.read_text())
        merged = dict(DEFAULT_CONFIG)
        merged.update(data)
        return merged
    except Exception:
        return dict(DEFAULT_CONFIG)


def save(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))


def initialize(base_url: str | None = None, token: str | None = None) -> dict:
    config = load()
    if base_url:
        config["base_url"] = base_url.rstrip("/")
    if token:
        config["token"] = token
    save(config)
    return config


def env_overrides() -> dict:
    """Env wins over config file (same names as llm.py)."""
    return {
        "base_url": os.environ.get("OMNIROUTE_BASE_URL"),
        "token": os.environ.get("OMNIROUTE_TOKEN"),
    }
