# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/signals/emitter.py — Fan-out to 3 sinks (SQLite, PostHog, Statsig check).

ADOPTION: 2 lines at agent executor boundary:
    from src.core.signals.emitter import emit_mission_event
    emit_mission_event(mission_id, agent_id, success, duration_ms, credits_used)

Guarantees:
  - Never raises (all exceptions swallowed + logged)
  - SQLite write is sync but fast (<1ms WAL)
  - PostHog is no-op unless SIGNALS_POSTHOG_ENABLED=1
  - Statsig is read-only (flag eval, no event emit)
  - Overhead target: <5ms on hot path
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from src.core.signals.events import MissionEvent
from src.core.signals import local_store, posthog_sink

log = logging.getLogger(__name__)


def emit_mission_event(
    mission_id: Optional[str],
    agent_id: str,
    success: bool,
    duration_ms: int,
    credits_used: int = 0,
    user_id: str = "",
) -> None:
    """
    Single choke-point for mission telemetry.
    Safe to call from any context — sync, async, subprocess.

    Args:
        mission_id:   Unique ID for this run. Auto-generated if None.
        agent_id:     Version slug, e.g. "v1", "v2.1", "eval-test".
        success:      True if mission completed without error.
        duration_ms:  Wall-clock milliseconds.
        credits_used: MCU credits consumed (default 0).
        user_id:      Raw user identifier — hashed before storage.
    """
    try:
        event = MissionEvent.create(
            mission_id=mission_id or str(uuid.uuid4()),
            agent_id=agent_id,
            credits_used=credits_used,
            success=success,
            duration_ms=duration_ms,
            user_id=user_id,
        )

        # Sink 1: SQLite (always on, sync)
        local_store.write_event(event)

        # Sink 2: PostHog (no-op unless SIGNALS_POSTHOG_ENABLED=1)
        posthog_sink.emit(event)

        # Sink 3: Statsig — flag eval only, no event emit
        # Feature flags are queried by callers via get_flag_client(),
        # not pushed here. Nothing to do.

        log.debug(
            "signals.emit: mission=%s agent=%s success=%s duration=%dms credits=%d",
            event.mission_id,
            agent_id,
            success,
            duration_ms,
            credits_used,
        )

    except Exception as exc:  # noqa: BLE001
        # CRITICAL: never let telemetry break the agent path
        log.warning("signals.emit swallowed exception: %s", exc)
