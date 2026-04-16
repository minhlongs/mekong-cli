"""
core/telemetry/instrument.py — @observe_agent decorator for agent boundary instrumentation.

Wraps sync and async callables. Records:
  - invocation latency (ms) → METERS.invocation_ms
  - retry count on exception → METERS.retry_total

Usage (1-line adoption):
  from src.core.telemetry import observe_agent

  @observe_agent("planner")
  def run_planner(task: str) -> str:
      ...

  @observe_agent("executor")
  async def run_executor(task: str) -> str:
      ...

Token cost must be recorded explicitly by the caller after obtaining LLM response:
  from src.core.telemetry.meters import METERS
  METERS.token_cost_usd.add(cost_usd, {"agent_name": "planner"})

PII note: agent_name label only — no user data in metric attributes.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional

from src.core.telemetry.meters import METERS

logger = logging.getLogger(__name__)

_PII_ATTR_KEYS = frozenset({"user_email", "api_key", "bearer_token", "user_id"})


def _safe_attrs(agent_name: str, extra: Optional[dict] = None) -> dict:
    """Build metric attribute dict, stripping any PII keys."""
    attrs: dict = {"agent_name": agent_name}
    if extra:
        for k, v in extra.items():
            if k not in _PII_ATTR_KEYS:
                attrs[k] = str(v)
    return attrs


def observe_agent(
    agent_name: str,
    extra_attrs: Optional[dict] = None,
) -> Callable:
    """
    Decorator factory. Records latency and retries for the wrapped function.

    Args:
        agent_name: Stable identifier used as metric label (e.g. "planner", "executor").
        extra_attrs: Optional extra metric attributes (PII keys stripped automatically).
    """
    attrs = _safe_attrs(agent_name, extra_attrs)

    def decorator(fn: Callable) -> Callable:
        if asyncio.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                t0 = time.perf_counter()
                try:
                    result = await fn(*args, **kwargs)
                    return result
                except Exception:
                    METERS.retry_total.add(1, attrs)
                    logger.debug("observe_agent retry recorded for %s", agent_name)
                    raise
                finally:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    METERS.invocation_ms.record(elapsed_ms, attrs)

            return async_wrapper
        else:
            @functools.wraps(fn)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                t0 = time.perf_counter()
                try:
                    result = fn(*args, **kwargs)
                    return result
                except Exception:
                    METERS.retry_total.add(1, attrs)
                    logger.debug("observe_agent retry recorded for %s", agent_name)
                    raise
                finally:
                    elapsed_ms = (time.perf_counter() - t0) * 1000
                    METERS.invocation_ms.record(elapsed_ms, attrs)

            return sync_wrapper

    return decorator
