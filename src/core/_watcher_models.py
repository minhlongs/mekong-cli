"""Data models and defaults for the autonomous watcher."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional

from ._watcher_compat import bridge_value

DEFAULT_IGNORE_PATTERNS = [
    "*.pyc", "*.pyo", "*.pyd", "__pycache__/*", "*/__pycache__/*", ".git/*", "*/.git/*",
    ".pytest_cache/*", "*/.pytest_cache/*", ".mekong/*", "*/.mekong/*", "*.egg-info/*",
    "*/.egg-info/*", ".venv/*", "*/.venv/*", "venv/*", "*/venv/*", "node_modules/*",
    "*/node_modules/*", ".DS_Store", "*/.DS_Store", "*.tmp", "*~",
]


def _now() -> float:
    return bridge_value("time", time).time()


def _default_ignore_patterns() -> List[str]:
    return list(bridge_value("DEFAULT_IGNORE_PATTERNS", DEFAULT_IGNORE_PATTERNS))


class ChangeType(str, Enum):
    """Types of detected file changes."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChangeEvent:
    """Represents a single detected filesystem change."""

    file_path: str
    change_type: str
    timestamp: float = field(default_factory=_now)
    hash: str = ""
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"file_path": self.file_path, "change_type": self.change_type,
                "timestamp": self.timestamp, "hash": self.hash, "size_bytes": self.size_bytes}


@dataclass
class DiagnosticResult:
    """Result of static analysis or syntax check on a file."""

    file_path: str
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    line_number: Optional[int] = None
    column_offset: Optional[int] = None
    severity: str = "info"
    matched_cluster_id: Optional[str] = None
    timestamp: float = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {"file_path": self.file_path, "is_valid": self.is_valid,
                "error_type": self.error_type, "error_message": self.error_message,
                "line_number": self.line_number, "column_offset": self.column_offset,
                "severity": self.severity, "matched_cluster_id": self.matched_cluster_id,
                "timestamp": self.timestamp}


@dataclass
class RepairAction:
    """Record of an automated self-repair attempt."""

    action_id: str
    file_path: str
    strategy: str
    status: str
    details: str
    timestamp: float = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {"action_id": self.action_id, "file_path": self.file_path,
                "strategy": self.strategy, "status": self.status,
                "details": self.details, "timestamp": self.timestamp}


@dataclass
class WatcherConfig:
    """Configuration parameters for the autonomous file watcher."""

    watch_paths: List[str] = field(default_factory=lambda: ["."])
    poll_interval: float = 0.5
    debounce_ms: int = 300
    ignore_patterns: List[str] = field(default_factory=_default_ignore_patterns)
    auto_repair: bool = False
    run_tests: bool = False
    test_command: str = "python3 -m pytest"
    stream_gateway: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"watch_paths": self.watch_paths, "poll_interval": self.poll_interval,
                "debounce_ms": self.debounce_ms, "ignore_patterns": self.ignore_patterns,
                "auto_repair": self.auto_repair, "run_tests": self.run_tests,
                "test_command": self.test_command, "stream_gateway": self.stream_gateway}


@dataclass
class WatcherState:
    """Runtime telemetry and state of the watch daemon."""

    start_time: float = field(default_factory=_now)
    is_active: bool = False
    total_scans: int = 0
    files_monitored: int = 0
    events_detected: int = 0
    errors_diagnosed: int = 0
    repairs_attempted: int = 0
    repairs_succeeded: int = 0
    recent_events: List[FileChangeEvent] = field(default_factory=list)
    recent_repairs: List[RepairAction] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"start_time": self.start_time,
                "uptime_seconds": _now() - self.start_time if self.is_active else 0.0,
                "is_active": self.is_active, "total_scans": self.total_scans,
                "files_monitored": self.files_monitored, "events_detected": self.events_detected,
                "errors_diagnosed": self.errors_diagnosed, "repairs_attempted": self.repairs_attempted,
                "repairs_succeeded": self.repairs_succeeded,
                "recent_events": [event.to_dict() for event in self.recent_events[-10:]],
                "recent_repairs": [repair.to_dict() for repair in self.recent_repairs[-10:]]}
