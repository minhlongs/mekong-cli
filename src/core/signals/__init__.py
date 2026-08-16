# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/signals — Offline-first signals loop for Mekong CLI.

Layers:
  1. SQLite local store (always on, sync write)
  2. PostHog sink (async, deferred — activate at 50+ customers)
  3. Feature flags (FeatureFlag interface, Statsig impl or stub)

Usage (2-line adoption at agent executor boundary):
    from src.core.signals.emitter import emit_mission_event
    emit_mission_event(mission_id, agent_id, success, duration_ms, credits_used)
"""

from src.core.signals.events import MissionEvent
from src.core.signals.emitter import emit_mission_event

__all__ = ["MissionEvent", "emit_mission_event"]
