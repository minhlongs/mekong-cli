# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for MissionEvent and Signals schema (src/core/signals/events.py).

Verifies GDPR-safe salted hashing of user IDs, MissionEvent creation with
default and custom timestamps, factory method behavior, and serialization.
"""

from __future__ import annotations

import hashlib
import os
from unittest.mock import patch

from src.core.signals.events import MissionEvent, _hash_user_id


class TestHashUserId:
    """Validate GDPR-safe user_id hashing behavior."""

    def test_default_salt_produces_consistent_16_char_hash(self):
        with patch.dict(os.environ, {}, clear=True):
            # Explicitly ensure SIGNALS_USER_SALT is absent
            os.environ.pop("SIGNALS_USER_SALT", None)
            h1 = _hash_user_id("user_123")
            h2 = _hash_user_id("user_123")
            assert h1 == h2
            assert len(h1) == 16
            expected = hashlib.sha256(b"mekong-default-salt:user_123").hexdigest()[:16]
            assert h1 == expected

    def test_custom_salt_from_env_changes_hash(self):
        with patch.dict(os.environ, {"SIGNALS_USER_SALT": "custom-secure-salt-999"}):
            h = _hash_user_id("user_123")
            assert len(h) == 16
            expected = hashlib.sha256(b"custom-secure-salt-999:user_123").hexdigest()[:16]
            assert h == expected
            # Must differ from default salt
            default_h = hashlib.sha256(b"mekong-default-salt:user_123").hexdigest()[:16]
            assert h != default_h

    def test_different_users_produce_different_hashes(self):
        h1 = _hash_user_id("alice")
        h2 = _hash_user_id("bob")
        assert h1 != h2


class TestMissionEvent:
    """Validate MissionEvent dataclass, factory, and serialization."""

    def test_direct_instantiation(self):
        event = MissionEvent(
            mission_id="m-001",
            agent_id="v1",
            credits_used=5,
            success=True,
            duration_ms=1200,
        )
        assert event.mission_id == "m-001"
        assert event.agent_id == "v1"
        assert event.credits_used == 5
        assert event.success is True
        assert event.duration_ms == 1200
        assert event.user_id_hash == ""
        assert event.ts  # ISO string auto-populated

    def test_create_factory_with_user_id(self):
        event = MissionEvent.create(
            mission_id="m-002",
            agent_id="v2.1",
            credits_used=10,
            success=True,
            duration_ms=3500,
            user_id="customer_abc",
        )
        assert event.mission_id == "m-002"
        assert event.agent_id == "v2.1"
        assert event.credits_used == 10
        assert event.success is True
        assert event.duration_ms == 3500
        assert event.user_id_hash == _hash_user_id("customer_abc")
        assert len(event.user_id_hash) == 16

    def test_create_factory_without_user_id(self):
        event = MissionEvent.create(
            mission_id="m-003",
            agent_id="v1",
            credits_used=0,
            success=False,
            duration_ms=450,
            user_id="",
        )
        assert event.user_id_hash == ""

    def test_to_dict_serialization(self):
        event = MissionEvent.create(
            mission_id="m-004",
            agent_id="v3.0",
            credits_used=2,
            success=True,
            duration_ms=800,
            user_id="u_99",
        )
        d = event.to_dict()
        assert isinstance(d, dict)
        assert d == {
            "mission_id": "m-004",
            "agent_id": "v3.0",
            "credits_used": 2,
            "success": True,
            "duration_ms": 800,
            "ts": event.ts,
            "user_id_hash": event.user_id_hash,
        }
