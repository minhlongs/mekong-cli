"""Daemon orchestration for watcher, diagnostics, and repair services."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, List, Optional

from ._watcher_compat import bridge_value
from ._watcher_diagnostics import DiagnosticsEngine
from ._watcher_filesystem import FileSystemWatcher
from ._watcher_models import ChangeType, FileChangeEvent, WatcherConfig, WatcherState
from ._watcher_repair import SelfRepairManager


class AutonomousWatchDaemon:
    """Unified autonomous daemon managing file watching, diagnostics, and repairs."""

    def __init__(self, config: Optional[WatcherConfig] = None, project_root: Optional[Path] = None) -> None:
        self.config = config or bridge_value("WatcherConfig", WatcherConfig)()
        self.project_root = bridge_value("Path", Path)(project_root or Path.cwd()).resolve()
        self.watcher = bridge_value("FileSystemWatcher", FileSystemWatcher)(self.config)
        self.diagnostics = bridge_value("DiagnosticsEngine", DiagnosticsEngine)(project_root=self.project_root)
        self.repair_mgr = bridge_value("SelfRepairManager", SelfRepairManager)(project_root=self.project_root)
        self.state = bridge_value("WatcherState", WatcherState)()
        self._lock = bridge_value("threading", threading).Lock()
        self.watcher.add_change_listener(self.process_file_batch)

    def _broadcast_gateway_event(self, event_type: str, data: dict[str, Any]) -> None:
        if not self.config.stream_gateway:
            return
        try:
            from src.core.gateway.streaming import StreamEvent, get_streaming_broker

            get_streaming_broker().publish(StreamEvent(mission_id="watch_daemon", event_type=event_type, data=data))
        except Exception:
            pass  # Gateway delivery is intentionally non-blocking.

    def start(self, daemon: bool = True) -> None:
        with self._lock:
            self.state.is_active = True
            self.state.start_time = bridge_value("time", time).time()
        self.watcher.start(daemon=daemon)
        self._broadcast_gateway_event("watch_daemon_started", {"watch_paths": self.config.watch_paths,
                                      "auto_repair": self.config.auto_repair})

    def stop(self) -> None:
        self.watcher.stop()
        with self._lock:
            self.state.is_active = False
        self._broadcast_gateway_event("watch_daemon_stopped", {"uptime_seconds": bridge_value("time", time).time() - self.state.start_time})

    def is_running(self) -> bool:
        return self.watcher.is_running()

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            with self.watcher._lock:
                self.state.files_monitored = len(self.watcher._known_files)
            return self.state.to_dict()

    def process_file_batch(self, changes: List[FileChangeEvent]) -> List[dict[str, Any]]:
        results: List[dict[str, Any]] = []
        with self._lock:
            self.state.events_detected += len(changes)
            self.state.recent_events.extend(changes)
            if len(self.state.recent_events) > 50:
                self.state.recent_events = self.state.recent_events[-50:]
        change_type = bridge_value("ChangeType", ChangeType)
        for event in changes:
            self._broadcast_gateway_event("watch_file_changed", event.to_dict())
            is_python_change = event.change_type in (change_type.CREATED.value, change_type.MODIFIED.value) and event.file_path.endswith(".py")
            if not is_python_change:
                results.append({"event": event.to_dict()})
                continue
            diagnostic = self.diagnostics.validate_file(event.file_path)
            result_item: dict[str, Any] = {"event": event.to_dict(), "diagnostic": diagnostic.to_dict(), "repair": None}
            if not diagnostic.is_valid:
                with self._lock:
                    self.state.errors_diagnosed += 1
                self._broadcast_gateway_event("watch_diagnostic_error", diagnostic.to_dict())
                if self.config.auto_repair:
                    with self._lock:
                        self.state.repairs_attempted += 1
                    self._broadcast_gateway_event("watch_repair_started", {"file_path": event.file_path,
                                                  "error": diagnostic.error_message})
                    repair_action = self.repair_mgr.diagnose_and_repair(event.file_path, diagnostic)
                    result_item["repair"] = repair_action.to_dict()
                    with self._lock:
                        if repair_action.status == "success":
                            self.state.repairs_succeeded += 1
                        self.state.recent_repairs.append(repair_action)
                        if len(self.state.recent_repairs) > 50:
                            self.state.recent_repairs = self.state.recent_repairs[-50:]
                    self._broadcast_gateway_event("watch_repair_completed", repair_action.to_dict())
            elif self.config.run_tests:
                result_item["tests"] = self.diagnostics.run_tests_for_file(event.file_path)
            results.append(result_item)
        return results

    def trigger_self_repair(self, file_path: str, mode: str = "auto") -> dict[str, Any]:
        diagnostic = self.diagnostics.validate_file(file_path)
        with self._lock:
            self.state.repairs_attempted += 1
        if mode == "rollback":
            repair = self.repair_mgr.rollback_file_checkpoint(file_path)
        elif mode == "syntax_fix":
            repair = self.repair_mgr.auto_fix_syntax(file_path, diagnostic)
        else:
            repair = self.repair_mgr.diagnose_and_repair(file_path, diagnostic)
        with self._lock:
            if repair.status == "success":
                self.state.repairs_succeeded += 1
            self.state.recent_repairs.append(repair)
        return {"file_path": file_path, "diagnostic": diagnostic.to_dict(), "repair": repair.to_dict()}
