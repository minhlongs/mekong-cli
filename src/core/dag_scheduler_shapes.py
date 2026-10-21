# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""DAG scheduler shared shapes — step result and identifier coercion helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class DAGStepResult:
    order: Any
    success: bool
    result: Any = None
    error: str | None = None


def coerce_id(val: Any, default: Any = None) -> Any:
    """Normalize a step or dependency identifier to an int when possible."""
    if isinstance(val, int):
        return val
    if isinstance(val, str):
        return int(val) if val.isdigit() else val
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def get_order(step: Any, default: Any = 0) -> Any:
    """Resolve a step's execution order, preferring explicit order then id."""
    target = getattr(step, "step", step)
    val = (
        target.get("order", target.get("id", default))
        if isinstance(target, dict)
        else getattr(target, "order", getattr(target, "id", default))
    )
    return coerce_id(val, default)


def get_dependencies(step: Any) -> list[Any]:
    """Resolve a step's dependency ids, dropping uncoercible entries."""
    target = getattr(step, "step", step)
    raw = (
        target.get("dependencies", target.get("depends_on", []))
        if isinstance(target, dict)
        else getattr(target, "dependencies", getattr(target, "depends_on", []))
    ) or []
    return [cid for d in raw if (cid := coerce_id(d)) is not None]
