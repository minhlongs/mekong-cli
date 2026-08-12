"""Mekong CLI 7 — Multi-profile (OPC Platform productize).

Mỗi OPC = 1 profile: ~/.mekong/profiles/<company>/opc/ — config + state riêng.
Default profile (không tên) = state cũ ~/.mekong/opc/ (backward compatible).
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROFILES_DIR = Path.home() / ".mekong" / "profiles"
PROFILE_FILE = Path.home() / ".mekong" / "profile.json"
DEFAULT_PROFILE = "default"


def active_profile() -> str:
    """Profile đang dùng: env MK_PROFILE > ~/.mekong/profile.json > default."""
    env = os.environ.get("MK_PROFILE", "").strip()
    if env:
        return env
    if PROFILE_FILE.exists():
        try:
            return json.loads(PROFILE_FILE.read_text()).get("active", DEFAULT_PROFILE)
        except Exception:
            pass
    return DEFAULT_PROFILE


def set_active_profile(name: str) -> None:
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(json.dumps({"active": name}, indent=2))


def list_profiles() -> list[str]:
    if not PROFILES_DIR.exists():
        return []
    return sorted(d.name for d in PROFILES_DIR.iterdir() if d.is_dir())


def init_profile(name: str) -> Path:
    """Tạo profile mới — trả state dir của nó."""
    p = PROFILES_DIR / name / "opc"
    p.mkdir(parents=True, exist_ok=True)
    return p


def state_dir() -> Path:
    """State dir cho profile đang dùng. Default → ~/.mekong/opc (backward compat)."""
    name = active_profile()
    if name == DEFAULT_PROFILE:
        return Path.home() / ".mekong" / "opc"
    return PROFILES_DIR / name / "opc"
