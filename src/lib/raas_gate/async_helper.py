# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Async Helper — Run async coroutines from sync context safely.

Used by raas_gate components to fire-and-forget analytics/logging
without blocking the main synchronous flow.
"""

from __future__ import annotations

import asyncio
from typing import Any, Coroutine, Optional, TypeVar

T = TypeVar("T")


def _run_async_safe(coro: Coroutine[Any, Any, T]) -> Optional[T]:
    """
    Run async coroutine from sync context safely.

    - In async context: creates task (fire-and-forget)
    - In sync context: runs to completion
    - On any error: silently returns None (don't block main flow)

    Args:
        coro: Coroutine to run

    Returns:
        Result of coroutine or None if failed
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
            return None
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)
    except Exception:
        return None
