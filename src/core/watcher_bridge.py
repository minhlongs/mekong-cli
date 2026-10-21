"""Backward-compatible facade for the autonomous self-repair watcher.

Public symbols remain available from ``src.core.watcher_bridge`` while the
implementation is separated into standard-library-only focused modules.
"""

from __future__ import annotations

import logging
import threading
from typing import Optional

from ._watcher_daemon import AutonomousWatchDaemon
from ._watcher_diagnostics import DiagnosticsEngine
from ._watcher_filesystem import FileSystemWatcher, compute_file_hash, matches_patterns
from ._watcher_models import (
    DEFAULT_IGNORE_PATTERNS,
    ChangeType,
    DiagnosticResult,
    FileChangeEvent,
    RepairAction,
    WatcherConfig,
    WatcherState,
)
from ._watcher_repair import SelfRepairManager

logger = logging.getLogger(__name__)

# Keep imported types picklable and introspectable under their historic path.
for _public_type in (
    ChangeType,
    FileChangeEvent,
    DiagnosticResult,
    RepairAction,
    WatcherConfig,
    WatcherState,
    FileSystemWatcher,
    DiagnosticsEngine,
    SelfRepairManager,
    AutonomousWatchDaemon,
):
    _public_type.__module__ = __name__

compute_file_hash.__module__ = __name__
matches_patterns.__module__ = __name__

# Singleton state deliberately lives in this facade so legacy monkeypatches of
# these names continue to control get_watch_daemon().
_GLOBAL_WATCH_DAEMON: Optional[AutonomousWatchDaemon] = None
_GLOBAL_WATCH_LOCK = threading.Lock()


def get_watch_daemon(config: Optional[WatcherConfig] = None) -> AutonomousWatchDaemon:
    """Get or initialize the singleton autonomous watch daemon."""
    global _GLOBAL_WATCH_DAEMON
    with _GLOBAL_WATCH_LOCK:
        if _GLOBAL_WATCH_DAEMON is None:
            _GLOBAL_WATCH_DAEMON = AutonomousWatchDaemon(config=config)
        elif config is not None:
            _GLOBAL_WATCH_DAEMON.config = config
            _GLOBAL_WATCH_DAEMON.watcher.config = config
        return _GLOBAL_WATCH_DAEMON


__all__ = [
    "DEFAULT_IGNORE_PATTERNS",
    "ChangeType",
    "FileChangeEvent",
    "DiagnosticResult",
    "RepairAction",
    "WatcherConfig",
    "WatcherState",
    "FileSystemWatcher",
    "DiagnosticsEngine",
    "SelfRepairManager",
    "AutonomousWatchDaemon",
    "compute_file_hash",
    "matches_patterns",
    "get_watch_daemon",
    "_GLOBAL_WATCH_DAEMON",
    "_GLOBAL_WATCH_LOCK",
]

del _public_type
