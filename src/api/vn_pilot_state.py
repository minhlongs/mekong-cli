# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Shared mutable config state for VN Pilot API.

Single source of truth for CONFIG_DIR and MAX_PILOTS.
All vn_pilot_* modules read from here at call time (not import time)
so that test monkeypatching on vn_pilot_routes propagates correctly
via the __setattr__ proxy defined there.
"""
from __future__ import annotations

import os
from pathlib import Path

CONFIG_DIR: Path = Path(os.getenv("MEKONG_PILOT_DIR", str(Path.home() / ".mekong")))
MAX_PILOTS: int = int(os.getenv("MEKONG_MAX_PILOTS", "50"))
