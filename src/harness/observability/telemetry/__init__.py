# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Telemetry utilities — thin wrappers over local telemetry modules."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .meters import METERS
from .gpu_probe import GpuProbe

@dataclass
class ExecutionTrace:
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str = ""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

def setup_telemetry(*args: Any, **kwargs: Any) -> None:
    return None

def observe_agent(*args: Any, **kwargs: Any) -> None:
    return None

__all__ = [
    "ExecutionTrace",
    "setup_telemetry",
    "observe_agent",
    "METERS",
    "GpuProbe",
]
