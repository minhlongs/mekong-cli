# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
core/signals/posthog_sink.py — Async PostHog event sink (DEFERRED).

Status: STUB — activate when SIGNALS_POSTHOG_ENABLED=1 in environment.
Default: disabled. PostHog self-host on M1 Max deferred to 50+ customer milestone.

When enabled:
  - Fire-and-forget asyncio task (5s batch)
  - Host: posthog.m1max.cashclaw.cc (CF Tunnel → M1 Max localhost:8000)
  - API key from env POSTHOG_API_KEY (never in repo)
  - Batch size: up to 20 events per flush
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.signals.events import MissionEvent

log = logging.getLogger(__name__)

_POSTHOG_HOST = os.environ.get(
    "POSTHOG_HOST", "https://posthog.m1max.cashclaw.cc"
)
_POSTHOG_API_KEY = os.environ.get("POSTHOG_API_KEY", "")
_ENABLED = os.environ.get("SIGNALS_POSTHOG_ENABLED", "0") == "1"

# In-memory batch buffer — flushed every 5 seconds by background task
_batch: list[dict] = []
_flush_task: asyncio.Task | None = None  # type: ignore[type-arg]


def _is_enabled() -> bool:
    return _ENABLED and bool(_POSTHOG_API_KEY)


async def _flush_batch() -> None:
    """Flush buffered events to PostHog. Swallows all exceptions."""
    global _batch
    if not _batch:
        return
    events = _batch.copy()
    _batch = []
    try:
        import aiohttp  # optional dep — only needed when PostHog enabled

        payload = {"api_key": _POSTHOG_API_KEY, "batch": events}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{_POSTHOG_HOST}/batch/",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status >= 400:
                    log.warning("PostHog batch rejected: %s", resp.status)
    except Exception as exc:  # noqa: BLE001
        log.debug("PostHog flush skipped: %s", exc)


async def _periodic_flush(interval: int = 5) -> None:
    while True:
        await asyncio.sleep(interval)
        await _flush_batch()


def start_background_flush() -> None:
    """Start periodic flush task. Call once at process start if PostHog enabled."""
    global _flush_task
    if not _is_enabled():
        return
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            _flush_task = loop.create_task(_periodic_flush())
    except RuntimeError:
        pass  # no event loop — skip silently


def emit(event: "MissionEvent") -> None:
    """
    Queue a MissionEvent for PostHog. No-op when PostHog is disabled.
    Overhead: ~0ms (list append, no I/O on hot path).
    """
    if not _is_enabled():
        return
    _batch.append(
        {
            "event": "mission_completed",
            "distinct_id": event.user_id_hash or event.mission_id,
            "properties": event.to_dict(),
            "timestamp": event.ts,
        }
    )
    # Flush immediately if batch is large
    if len(_batch) >= 20:
        try:
            asyncio.get_event_loop().create_task(_flush_batch())
        except RuntimeError:
            pass
