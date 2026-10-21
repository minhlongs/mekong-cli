"""Polling filesystem monitor used by the autonomous watcher."""

from __future__ import annotations

import fnmatch
import hashlib
import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ._watcher_compat import bridge_value
from ._watcher_models import ChangeType, FileChangeEvent, WatcherConfig

logger = logging.getLogger(__name__)


def compute_file_hash(path: Path) -> str:
    """Compute a SHA-256 file hash efficiently in 64KB chunks."""
    try:
        hasher = bridge_value("hashlib", hashlib).sha256()
        with open(path, "rb") as file_handle:
            while chunk := file_handle.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def matches_patterns(path_str: str, patterns: List[str]) -> bool:
    """Check whether a path string matches any configured ignore pattern."""
    matcher = bridge_value("fnmatch", fnmatch).fnmatch
    normalized = path_str.replace("\\", "/")
    for pattern in patterns:
        if matcher(normalized, pattern) or matcher(f"*/{normalized}", pattern):
            return True
        if pattern.endswith("/*") and (normalized.startswith(pattern[:-2]) or f"/{pattern[:-2]}/" in normalized):
            return True
    return False


class FileSystemWatcher:
    """Thread-safe polling filesystem change monitor with debouncing."""

    def __init__(self, config: Optional[WatcherConfig] = None) -> None:
        self.config = config or bridge_value("WatcherConfig", WatcherConfig)()
        self._lock = bridge_value("threading", threading).Lock()
        self._stop_event = bridge_value("threading", threading).Event()
        self._thread: Optional[threading.Thread] = None
        self._known_files: Dict[str, Tuple[float, str, int]] = {}
        self._pending_events: Dict[str, FileChangeEvent] = {}
        self._last_event_time = 0.0
        self._callbacks: List[Callable[[List[FileChangeEvent]], None]] = []
        self._initialized = False

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def add_change_listener(self, callback: Callable[[List[FileChangeEvent]], None]) -> None:
        with self._lock:
            self._callbacks.append(callback)

    def _is_ignored(self, path: Path, rel_str: str) -> bool:
        if bridge_value("matches_patterns", matches_patterns)(rel_str, self.config.ignore_patterns):
            return True
        return any(part in {".git", ".mekong", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}
                   for part in path.parts)

    def _record_file(self, path: Path, current_files: Dict[str, Tuple[float, str, int]]) -> None:
        try:
            stat = path.stat()
            old_entry = self._known_files.get(str(path))
            f_hash = old_entry[1] if old_entry and old_entry[0] == stat.st_mtime and old_entry[2] == stat.st_size else bridge_value("compute_file_hash", compute_file_hash)(path)
            current_files[str(path)] = (stat.st_mtime, f_hash, stat.st_size)
        except (OSError, PermissionError):
            return

    def scan_once(self) -> List[FileChangeEvent]:
        events: List[FileChangeEvent] = []
        current_files: Dict[str, Tuple[float, str, int]] = {}
        path_type = bridge_value("Path", Path)
        for root_path_str in self.config.watch_paths:
            root_path = path_type(root_path_str).resolve()
            if not root_path.exists():
                continue
            if root_path.is_file():
                if not self._is_ignored(root_path, root_path.name):
                    self._record_file(root_path, current_files)
                continue
            for dirpath, dirnames, filenames in bridge_value("os", os).walk(root_path):
                dir_path = path_type(dirpath)
                try:
                    rel_dir = str(dir_path.relative_to(root_path)).replace("\\", "/")
                except ValueError:
                    rel_dir = dir_path.name
                dirnames[:] = [name for name in dirnames if not self._is_ignored(
                    dir_path / name, f"{rel_dir}/{name}" if rel_dir != "." else name)]
                for filename in filenames:
                    file_path = dir_path / filename
                    try:
                        rel_file = str(file_path.relative_to(root_path)).replace("\\", "/")
                    except ValueError:
                        rel_file = filename
                    if not self._is_ignored(file_path, rel_file):
                        self._record_file(file_path, current_files)
        with self._lock:
            if not self._initialized:
                self._known_files, self._initialized = current_files, True
                return []
            change_type = bridge_value("ChangeType", ChangeType)
            now = bridge_value("time", time).time()
            for path_str, (mtime, f_hash, size) in current_files.items():
                old_entry = self._known_files.get(path_str)
                if old_entry is None or old_entry[1] != f_hash or (old_entry[0] != mtime and old_entry[2] != size):
                    event_type = change_type.CREATED.value if old_entry is None else change_type.MODIFIED.value
                    events.append(FileChangeEvent(path_str, event_type, now, f_hash, size))
            for path_str in self._known_files:
                if path_str not in current_files:
                    events.append(FileChangeEvent(path_str, change_type.DELETED.value, now, "", 0))
            self._known_files = current_files
        return events

    def start(self, daemon: bool = True) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = bridge_value("threading", threading).Thread(
                target=self._run_loop, daemon=daemon, name="MekongFileWatcher")
            self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run_loop(self) -> None:
        if not self._initialized:
            self.scan_once()
        while not self._stop_event.is_set():
            new_events, clock = self.scan_once(), bridge_value("time", time)
            now = clock.time()
            if new_events:
                with self._lock:
                    self._pending_events.update({event.file_path: event for event in new_events})
                    self._last_event_time = now
            with self._lock:
                is_ready = self._pending_events and now - self._last_event_time >= self.config.debounce_ms / 1000.0
                batch_to_emit = list(self._pending_events.values()) if is_ready else []
                if is_ready:
                    self._pending_events.clear()
                callbacks = list(self._callbacks)
            for callback in callbacks if batch_to_emit else []:
                try:
                    callback(batch_to_emit)
                except Exception as error:
                    bridge_value("logger", logger).error(f"Error in file change callback: {error}")
            chunks = max(1, int(self.config.poll_interval / 0.1))
            for _ in range(chunks):
                if self._stop_event.is_set():
                    break
                clock.sleep(self.config.poll_interval / chunks)
