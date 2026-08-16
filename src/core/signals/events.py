# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/signals/events.py — MissionEvent dataclass + schema.

Schema doc:
  mission_id  : str  — unique per mission run (uuid4)
  agent_id    : str  — agent version slug, e.g. "v1", "v2.1"
  credits_used: int  — MCU credits deducted
  success     : bool — True if mission completed without error
  duration_ms : int  — wall-clock milliseconds
  ts          : str  — ISO-8601 UTC timestamp
  user_id_hash: str  — SHA-256(user_id + SALT) — GDPR safe, never raw user_id
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone


def _hash_user_id(user_id: str) -> str:
    """Hash user_id with env salt before storage. GDPR compliance."""
    salt = os.environ.get("SIGNALS_USER_SALT", "mekong-default-salt")
    return hashlib.sha256(f"{salt}:{user_id}".encode()).hexdigest()[:16]


@dataclass
class MissionEvent:
    """Immutable record of a single agent mission execution."""

    mission_id: str
    agent_id: str
    credits_used: int
    success: bool
    duration_ms: int
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    user_id_hash: str = ""

    @classmethod
    def create(
        cls,
        mission_id: str,
        agent_id: str,
        credits_used: int,
        success: bool,
        duration_ms: int,
        user_id: str = "",
    ) -> "MissionEvent":
        """Factory: hashes user_id automatically."""
        return cls(
            mission_id=mission_id,
            agent_id=agent_id,
            credits_used=credits_used,
            success=success,
            duration_ms=duration_ms,
            user_id_hash=_hash_user_id(user_id) if user_id else "",
        )

    def to_dict(self) -> dict:
        """Serialize for PostHog / JSON emit."""
        return {
            "mission_id": self.mission_id,
            "agent_id": self.agent_id,
            "credits_used": self.credits_used,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "ts": self.ts,
            "user_id_hash": self.user_id_hash,
        }
