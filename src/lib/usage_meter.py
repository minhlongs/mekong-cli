"""BACKWARD-COMPAT RE-EXPORT shim — src.lib.usage_meter
Merged into ``src.usage.usage_tracker`` as part of B2 (Usage Tracker Merge).
All symbols are re-exported so existing ``from src.lib.usage_meter import ...``
callers keep working. Do NOT add new logic here.
"""
from src.usage.usage_tracker import (  # noqa: F401
    UsageEvent,
    UsageEventType,
    UsageMetering,
    get_metering,
    reset_metering,
)

__all__ = [
    "UsageEvent",
    "UsageEventType",
    "UsageMetering",
    "get_metering",
    "reset_metering",
]
