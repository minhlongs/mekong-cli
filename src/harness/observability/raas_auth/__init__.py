# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Stub: RaaS auth client for observability."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class RaaSAuthClient:
    base_url: str = ""
    api_key: Optional[str] = None

    def authenticate(self) -> bool:
        return False
