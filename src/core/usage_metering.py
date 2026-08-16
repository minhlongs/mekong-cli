# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""BACKWARD-COMPAT RE-EXPORT shim — src.core.usage_metering

Merged into ``src.usage.usage_tracker`` as part of B2 (Usage Tracker Merge).
All symbols are re-exported from the unified module so existing
``from src.core.usage_metering import ...`` callers keep working.

Do NOT add new logic here — edit ``src.usage.usage_tracker`` instead.
"""

from src.usage.usage_tracker import (  # noqa: F401
    AnomalyCategory,
    UsageAnomalyDetector,
    UsageEvent,
    UsageEventType,
    UsageMetering,  # alias for UsageTracker
        get_metering,
    get_tracker,
    reset_metering,
)
from src.core.anomaly_detector import get_detector  # noqa: F401

__all__ = [
    "UsageEvent",
    "UsageEventType",
    "UsageMetering",
    "get_metering",
    "reset_metering",
    # also re-exported for any caller that imported deeper names
    "UsageAnomalyDetector",
    "AnomalyCategory",
    "get_detector",
    "get_tracker",
]
