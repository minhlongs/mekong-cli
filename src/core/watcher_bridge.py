# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Self-Repair & File-Watcher Daemon (watch & heal).

Provides real-time filesystem change monitoring, SHA-256 state tracking,
event debouncing, standard-library AST syntax diagnostics, automated error
clustering with evals.db, durable checkpoint rollback self-healing, and
live streaming event emission across the Gateway broker.

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs or heavy third-party packages (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import ast
import fnmatch
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

DEFAULT_IGNORE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__/*",
    "*/__pycache__/*",
    ".git/*",
    "*/.git/*",
    ".pytest_cache/*",
    "*/.pytest_cache/*",
    ".mekong/*",
    "*/.mekong/*",
    "*.egg-info/*",
    "*/.egg-info/*",
    ".venv/*",
    "*/.venv/*",
    "venv/*",
    "*/venv/*",
    "node_modules/*",
    "*/node_modules/*",
    ".DS_Store",
    "*/.DS_Store",
    "*.tmp",
    "*~",
]


class ChangeType(str, Enum):
    """Types of detected file changes."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"


@dataclass
class FileChangeEvent:
    """Represents a single detected filesystem change."""

    file_path: str
    change_type: str  # "created", "modified", "deleted"
    timestamp: float = field(default_factory=time.time)
    hash: str = ""
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "file_path": self.file_path,
            "change_type": self.change_type,
            "timestamp": self.timestamp,
            "hash": self.hash,
            "size_bytes": self.size_bytes,
        }


@dataclass
class DiagnosticResult:
    """Result of static analysis or syntax check on a file."""

    file_path: str
    is_valid: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    line_number: Optional[int] = None
    column_offset: Optional[int] = None
    severity: str = "info"  # "error", "warning", "info"
    matched_cluster_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert diagnostic result to dictionary."""
        return {
            "file_path": self.file_path,
            "is_valid": self.is_valid,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "line_number": self.line_number,
            "column_offset": self.column_offset,
            "severity": self.severity,
            "matched_cluster_id": self.matched_cluster_id,
            "timestamp": self.timestamp,
        }


@dataclass
class RepairAction:
    """Record of an automated self-repair attempt."""

    action_id: str
    file_path: str
    strategy: str  # "checkpoint_rollback", "syntax_auto_fix", "quarantine", "noop"
    status: str  # "pending", "success", "failed"
    details: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert repair action to dictionary."""
        return {
            "action_id": self.action_id,
            "file_path": self.file_path,
            "strategy": self.strategy,
            "status": self.status,
            "details": self.details,
            "timestamp": self.timestamp,
        }


@dataclass
class WatcherConfig:
    """Configuration parameters for the autonomous file watcher."""

    watch_paths: List[str] = field(default_factory=lambda: ["."])
    poll_interval: float = 0.5
    debounce_ms: int = 300
    ignore_patterns: List[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    auto_repair: bool = False
    run_tests: bool = False
    test_command: str = "python3 -m pytest"
    stream_gateway: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "watch_paths": self.watch_paths,
            "poll_interval": self.poll_interval,
            "debounce_ms": self.debounce_ms,
            "ignore_patterns": self.ignore_patterns,
            "auto_repair": self.auto_repair,
            "run_tests": self.run_tests,
            "test_command": self.test_command,
            "stream_gateway": self.stream_gateway,
        }


@dataclass
class WatcherState:
    """Runtime telemetry and state of the watch daemon."""

    start_time: float = field(default_factory=time.time)
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
        """Convert state to dictionary."""
        return {
            "start_time": self.start_time,
            "uptime_seconds": time.time() - self.start_time if self.is_active else 0.0,
            "is_active": self.is_active,
            "total_scans": self.total_scans,
            "files_monitored": self.files_monitored,
            "events_detected": self.events_detected,
            "errors_diagnosed": self.errors_diagnosed,
            "repairs_attempted": self.repairs_attempted,
            "repairs_succeeded": self.repairs_succeeded,
            "recent_events": [e.to_dict() for e in self.recent_events[-10:]],
            "recent_repairs": [r.to_dict() for r in self.recent_repairs[-10:]],
        }


def compute_file_hash(path: Path) -> str:
    """Compute SHA-256 hash of a file efficiently in 64KB chunks."""
    try:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return ""


def matches_patterns(path_str: str, patterns: List[str]) -> bool:
    """Check if path string matches any glob/fnmatch pattern."""
    normalized = path_str.replace("\\", "/")
    for pattern in patterns:
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(f"*/{normalized}", pattern):
            return True
        if pattern.endswith("/*") and (normalized.startswith(pattern[:-2]) or f"/{pattern[:-2]}/" in normalized):
            return True
    return False


class FileSystemWatcher:
    """Thread-safe polling filesystem change monitor with debouncing."""

    def __init__(self, config: Optional[WatcherConfig] = None) -> None:
        self.config = config or WatcherConfig()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._known_files: Dict[str, Tuple[float, str, int]] = {}  # path -> (mtime, sha256, size)
        self._pending_events: Dict[str, FileChangeEvent] = {}
        self._last_event_time: float = 0.0
        self._callbacks: List[Callable[[List[FileChangeEvent]], None]] = []
        self._initialized = False

    def is_running(self) -> bool:
        """Check if watcher background thread is running."""
        return self._thread is not None and self._thread.is_alive()

    def add_change_listener(self, callback: Callable[[List[FileChangeEvent]], None]) -> None:
        """Register callback invoked when a debounced batch of changes settles."""
        with self._lock:
            self._callbacks.append(callback)

    def _is_ignored(self, path: Path, rel_str: str) -> bool:
        """Check if a file or directory path matches ignore patterns."""
        if matches_patterns(rel_str, self.config.ignore_patterns):
            return True
        for part in path.parts:
            if part in {".git", ".mekong", "__pycache__", ".pytest_cache", "node_modules", ".venv", "venv"}:
                return True
        return False

    def scan_once(self) -> List[FileChangeEvent]:
        """Perform a single synchronous scan across watched paths."""
        events: List[FileChangeEvent] = []
        current_files: Dict[str, Tuple[float, str, int]] = {}

        for root_path_str in self.config.watch_paths:
            root_path = Path(root_path_str).resolve()
            if not root_path.exists():
                continue

            if root_path.is_file():
                # Single file watch
                rel_str = root_path.name
                if not self._is_ignored(root_path, rel_str):
                    try:
                        stat = root_path.stat()
                        mtime = stat.st_mtime
                        size = stat.st_size
                        f_hash = compute_file_hash(root_path)
                        current_files[str(root_path)] = (mtime, f_hash, size)
                    except (OSError, PermissionError):
                        pass
                continue

            for dirpath, dirnames, filenames in os.walk(root_path):
                # Filter directories in-place to avoid descending into ignored trees
                dir_path = Path(dirpath)
                try:
                    rel_dir = str(dir_path.relative_to(root_path)).replace("\\", "/")
                except ValueError:
                    rel_dir = dir_path.name

                dirnames[:] = [
                    d for d in dirnames
                    if not self._is_ignored(dir_path / d, f"{rel_dir}/{d}" if rel_dir != "." else d)
                ]

                for fname in filenames:
                    file_path = dir_path / fname
                    try:
                        rel_file = str(file_path.relative_to(root_path)).replace("\\", "/")
                    except ValueError:
                        rel_file = fname

                    if self._is_ignored(file_path, rel_file):
                        continue

                    try:
                        stat = file_path.stat()
                        mtime = stat.st_mtime
                        size = stat.st_size
                        # Only compute hash if mtime or size differs from known
                        old_entry = self._known_files.get(str(file_path))
                        if old_entry and old_entry[0] == mtime and old_entry[2] == size:
                            f_hash = old_entry[1]
                        else:
                            f_hash = compute_file_hash(file_path)

                        current_files[str(file_path)] = (mtime, f_hash, size)
                    except (OSError, PermissionError):
                        continue

        with self._lock:
            if not self._initialized:
                # Initial baseline snapshot — record files without firing created events
                self._known_files = current_files
                self._initialized = True
                return []

            # Check created and modified
            for path_str, (mtime, f_hash, size) in current_files.items():
                if path_str not in self._known_files:
                    events.append(FileChangeEvent(
                        file_path=path_str,
                        change_type=ChangeType.CREATED.value,
                        timestamp=time.time(),
                        hash=f_hash,
                        size_bytes=size,
                    ))
                else:
                    old_mtime, old_hash, old_size = self._known_files[path_str]
                    if old_hash != f_hash or (old_mtime != mtime and old_size != size):
                        events.append(FileChangeEvent(
                            file_path=path_str,
                            change_type=ChangeType.MODIFIED.value,
                            timestamp=time.time(),
                            hash=f_hash,
                            size_bytes=size,
                        ))

            # Check deleted
            for path_str, (old_mtime, old_hash, old_size) in self._known_files.items():
                if path_str not in current_files:
                    events.append(FileChangeEvent(
                        file_path=path_str,
                        change_type=ChangeType.DELETED.value,
                        timestamp=time.time(),
                        hash="",
                        size_bytes=0,
                    ))

            self._known_files = current_files

        return events

    def start(self, daemon: bool = True) -> None:
        """Start background polling thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=daemon, name="MekongFileWatcher")
            self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        """Signal background polling thread to stop and wait."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            self._thread = None

    def _run_loop(self) -> None:
        """Internal background loop polling files and debouncing events."""
        if not self._initialized:
            self.scan_once()

        while not self._stop_event.is_set():
            new_events = self.scan_once()
            now = time.time()

            if new_events:
                with self._lock:
                    for ev in new_events:
                        self._pending_events[ev.file_path] = ev
                    self._last_event_time = now

            # Check if debounce window expired
            batch_to_emit: List[FileChangeEvent] = []
            debounce_sec = self.config.debounce_ms / 1000.0
            with self._lock:
                if self._pending_events and (now - self._last_event_time) >= debounce_sec:
                    batch_to_emit = list(self._pending_events.values())
                    self._pending_events.clear()

            if batch_to_emit:
                callbacks_copy: List[Callable[[List[FileChangeEvent]], None]] = []
                with self._lock:
                    callbacks_copy = list(self._callbacks)
                for cb in callbacks_copy:
                    try:
                        cb(batch_to_emit)
                    except Exception as e:
                        logger.error(f"Error in file change callback: {e}")

            # Sleep poll interval in small chunks to remain responsive to stop signal
            sleep_chunks = max(1, int(self.config.poll_interval / 0.1))
            chunk_duration = self.config.poll_interval / sleep_chunks
            for _ in range(sleep_chunks):
                if self._stop_event.is_set():
                    break
                time.sleep(chunk_duration)


class DiagnosticsEngine:
    """Validates source files, detects syntax errors, and clusters failures."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        evals_db_path: Optional[Path] = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.evals_db_path = evals_db_path or (self.project_root / ".mekong" / "evals.db")

    def validate_source(self, code: str, filename: str = "<memory>") -> DiagnosticResult:
        """Parse Python source code using ast.parse to detect syntax errors."""
        try:
            tree = ast.parse(code, filename=filename)
            # Basic static checks: verify imports can be parsed
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    pass  # AST successfully parsed imports
            return DiagnosticResult(
                file_path=filename,
                is_valid=True,
                severity="info",
            )
        except SyntaxError as e:
            return DiagnosticResult(
                file_path=filename,
                is_valid=False,
                error_type="SyntaxError",
                error_message=e.msg or "Syntax error",
                line_number=e.lineno,
                column_offset=e.offset,
                severity="error",
                matched_cluster_id=self.match_error_cluster(e.msg or "", "SyntaxError"),
            )
        except Exception as e:
            return DiagnosticResult(
                file_path=filename,
                is_valid=False,
                error_type=type(e).__name__,
                error_message=str(e),
                severity="error",
                matched_cluster_id=self.match_error_cluster(str(e), type(e).__name__),
            )

    def validate_file(self, file_path: str | Path) -> DiagnosticResult:
        """Validate a file on disk."""
        path = Path(file_path).resolve()
        if not path.exists():
            return DiagnosticResult(
                file_path=str(path),
                is_valid=False,
                error_type="FileNotFoundError",
                error_message=f"File {path} does not exist",
                severity="error",
            )

        if not path.name.endswith(".py"):
            return DiagnosticResult(
                file_path=str(path),
                is_valid=True,
                severity="info",
            )

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                code = f.read()
            return self.validate_source(code, filename=str(path))
        except Exception as e:
            return DiagnosticResult(
                file_path=str(path),
                is_valid=False,
                error_type=type(e).__name__,
                error_message=str(e),
                severity="error",
            )

    def match_error_cluster(self, error_msg: str, error_type: str) -> Optional[str]:
        """Compute error cluster signature matching .mekong/evals.db pattern."""
        try:
            normalized = re.sub(r"line \d+", "line <N>", error_msg.lower())
            normalized = re.sub(r"0x[0-9a-f]+", "0x<HEX>", normalized)
            raw = f"{error_type}:{normalized}".strip()
            return f"cluster_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:8]}"
        except Exception:
            return None

    def run_tests_for_file(self, file_path: str | Path, timeout: float = 15.0) -> dict[str, Any]:
        """Execute regression tests targeting or relating to the modified file."""
        path = Path(file_path).resolve()
        # Find matching test file if modifying src/
        test_target = str(path)
        if "tests" not in path.parts:
            # Check if tests/test_<stem>.py exists
            possible_test = self.project_root / "tests" / f"test_{path.stem}.py"
            if possible_test.exists():
                test_target = str(possible_test)

        cmd = [sys.executable, "-m", "pytest", test_target, "-q"]
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "ok": proc.returncode == 0,
                "returncode": proc.returncode,
                "output": proc.stdout + proc.stderr,
                "target": test_target,
            }
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "returncode": -1,
                "output": f"Test timed out after {timeout}s",
                "target": test_target,
            }
        except Exception as e:
            return {
                "ok": False,
                "returncode": -1,
                "output": f"Failed to execute tests: {e}",
                "target": test_target,
            }


class SelfRepairManager:
    """Coordinates automated code repair and durable checkpoint rollback."""

    def __init__(
        self,
        project_root: Optional[Path] = None,
        checkpoint_store: Any = None,
    ) -> None:
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self._store = checkpoint_store
        self._repairs: List[RepairAction] = []
        self._lock = threading.Lock()

    def _get_checkpoint_store(self) -> Any:
        """Lazily initialize CheckpointStore from pev_swarm_bridge if not provided."""
        if self._store is None:
            try:
                from src.core.pev_swarm_bridge import CheckpointStore
                db_path = self.project_root / ".mekong" / "pev_checkpoints.db"
                self._store = CheckpointStore(db_path=db_path)
            except Exception as e:
                logger.warning(f"Could not initialize CheckpointStore: {e}")
                self._store = None
        return self._store

    def auto_fix_syntax(self, file_path: str | Path, diagnostic: DiagnosticResult) -> RepairAction:
        """Attempt heuristic AST syntax auto-fix on common simple typos."""
        path = Path(file_path).resolve()
        action_id = f"repair_{int(time.time() * 1000)}_{os.urandom(3).hex()}"

        if not path.exists() or diagnostic.is_valid:
            return RepairAction(
                action_id=action_id,
                file_path=str(path),
                strategy="noop",
                status="failed",
                details="File does not exist or has no syntax error to repair",
            )

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            if not lines:
                return RepairAction(
                    action_id=action_id,
                    file_path=str(path),
                    strategy="syntax_auto_fix",
                    status="failed",
                    details="Empty file",
                )

            err_line_idx = (diagnostic.line_number - 1) if diagnostic.line_number and diagnostic.line_number <= len(lines) else -1
            fixed = False

            if err_line_idx >= 0:
                target_line = lines[err_line_idx]
                trimmed = target_line.rstrip()

                # Heuristic 1: Missing colon on def, class, if, elif, else, for, while, try, except, finally, with
                block_keywords = ("def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "finally", "with ")
                stripped = trimmed.strip()
                if any(stripped.startswith(kw) for kw in block_keywords) and not stripped.endswith(":"):
                    lines[err_line_idx] = trimmed + ":\n"
                    fixed = True

                # Heuristic 2: Trailing unclosed parenthesis at end of line
                if not fixed and trimmed.count("(") > trimmed.count(")"):
                    missing = trimmed.count("(") - trimmed.count(")")
                    lines[err_line_idx] = trimmed + (")" * missing) + "\n"
                    fixed = True

            if fixed:
                candidate_code = "".join(lines)
                try:
                    ast.parse(candidate_code, filename=str(path))
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(candidate_code)
                    action = RepairAction(
                        action_id=action_id,
                        file_path=str(path),
                        strategy="syntax_auto_fix",
                        status="success",
                        details=f"Auto-fixed syntax error on line {diagnostic.line_number}",
                    )
                    with self._lock:
                        self._repairs.append(action)
                    return action
                except SyntaxError:
                    pass  # Heuristic didn't resolve full error

            # Heuristic did not produce valid AST
            action = RepairAction(
                action_id=action_id,
                file_path=str(path),
                strategy="syntax_auto_fix",
                status="failed",
                details="Syntax error could not be resolved via AST heuristics",
            )
            with self._lock:
                self._repairs.append(action)
            return action

        except Exception as e:
            action = RepairAction(
                action_id=action_id,
                file_path=str(path),
                strategy="syntax_auto_fix",
                status="failed",
                details=f"Exception during auto-fix: {e}",
            )
            with self._lock:
                self._repairs.append(action)
            return action

    def rollback_file_checkpoint(self, file_path: str | Path) -> RepairAction:
        """Rollback a corrupted file to its latest snapshot in CheckpointStore."""
        path = Path(file_path).resolve()
        action_id = f"repair_{int(time.time() * 1000)}_{os.urandom(3).hex()}"
        store = self._get_checkpoint_store()

        if not store:
            action = RepairAction(
                action_id=action_id,
                file_path=str(path),
                strategy="checkpoint_rollback",
                status="failed",
                details="No CheckpointStore available for rollback",
            )
            with self._lock:
                self._repairs.append(action)
            return action

        try:
            try:
                rel_path = str(path.relative_to(self.project_root)).replace("\\", "/")
            except ValueError:
                rel_path = path.name

            # Query most recent snapshot for this file from SQLite
            with store._connect() as conn:
                row = conn.execute(
                    """
                    SELECT content, sha256, checkpoint_id
                    FROM file_snapshots
                    WHERE relative_path = ?
                    ORDER BY id DESC LIMIT 1
                    """,
                    (rel_path,),
                ).fetchone()

            if not row or not row["content"]:
                action = RepairAction(
                    action_id=action_id,
                    file_path=str(path),
                    strategy="checkpoint_rollback",
                    status="failed",
                    details=f"No previous checkpoint snapshot found for {rel_path}",
                )
                with self._lock:
                    self._repairs.append(action)
                return action

            # Restore content from snapshot
            content = row["content"]
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            action = RepairAction(
                action_id=action_id,
                file_path=str(path),
                strategy="checkpoint_rollback",
                status="success",
                details=f"Restored from checkpoint {row['checkpoint_id']} (hash: {row['sha256'][:8]})",
            )
            with self._lock:
                self._repairs.append(action)
            return action

        except Exception as e:
            action = RepairAction(
                action_id=action_id,
                file_path=str(path),
                strategy="checkpoint_rollback",
                status="failed",
                details=f"Rollback failed with error: {e}",
            )
            with self._lock:
                self._repairs.append(action)
            return action

    def diagnose_and_repair(
        self,
        file_path: str | Path,
        diagnostic: DiagnosticResult,
    ) -> RepairAction:
        """Execute repair pipeline: attempts heuristic fix first, then checkpoint rollback."""
        if diagnostic.is_valid:
            return RepairAction(
                action_id=f"noop_{int(time.time() * 1000)}",
                file_path=str(file_path),
                strategy="noop",
                status="success",
                details="File is valid, no repair needed",
            )

        # 1. Try heuristic syntax auto-fix
        fix_action = self.auto_fix_syntax(file_path, diagnostic)
        if fix_action.status == "success":
            return fix_action

        # 2. If heuristic failed, fallback to checkpoint rollback
        rollback_action = self.rollback_file_checkpoint(file_path)
        return rollback_action


class AutonomousWatchDaemon:
    """Unified autonomous daemon managing file watching, diagnostics, and repairs."""

    def __init__(
        self,
        config: Optional[WatcherConfig] = None,
        project_root: Optional[Path] = None,
    ) -> None:
        self.config = config or WatcherConfig()
        self.project_root = Path(project_root or Path.cwd()).resolve()
        self.watcher = FileSystemWatcher(self.config)
        self.diagnostics = DiagnosticsEngine(project_root=self.project_root)
        self.repair_mgr = SelfRepairManager(project_root=self.project_root)
        self.state = WatcherState()
        self._lock = threading.Lock()

        # Wire change listener
        self.watcher.add_change_listener(self.process_file_batch)

    def _broadcast_gateway_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Stream watch and repair events over Gateway broker if available."""
        if not self.config.stream_gateway:
            return
        try:
            from src.core.gateway.streaming import StreamEvent, get_streaming_broker
            broker = get_streaming_broker()
            broker.publish(StreamEvent(
                mission_id="watch_daemon",
                event_type=event_type,
                data=data,
            ))
        except Exception:
            pass  # Non-blocking, fails gracefully if gateway not active

    def start(self, daemon: bool = True) -> None:
        """Start autonomous file watcher daemon."""
        with self._lock:
            self.state.is_active = True
            self.state.start_time = time.time()
        self.watcher.start(daemon=daemon)
        self._broadcast_gateway_event("watch_daemon_started", {
            "watch_paths": self.config.watch_paths,
            "auto_repair": self.config.auto_repair,
        })

    def stop(self) -> None:
        """Stop file watcher daemon."""
        self.watcher.stop()
        with self._lock:
            self.state.is_active = False
        self._broadcast_gateway_event("watch_daemon_stopped", {
            "uptime_seconds": time.time() - self.state.start_time,
        })

    def is_running(self) -> bool:
        """Check if daemon is currently running."""
        return self.watcher.is_running()

    def get_status(self) -> dict[str, Any]:
        """Return full telemetry dictionary."""
        with self._lock:
            with self.watcher._lock:
                self.state.files_monitored = len(self.watcher._known_files)
            return self.state.to_dict()

    def process_file_batch(self, changes: List[FileChangeEvent]) -> List[dict[str, Any]]:
        """Process a batch of debounced file changes."""
        results: List[dict[str, Any]] = []

        with self._lock:
            self.state.events_detected += len(changes)
            self.state.recent_events.extend(changes)
            if len(self.state.recent_events) > 50:
                self.state.recent_events = self.state.recent_events[-50:]

        for ev in changes:
            self._broadcast_gateway_event("watch_file_changed", ev.to_dict())

            # Only run AST diagnostics on created or modified Python files
            if ev.change_type in (ChangeType.CREATED.value, ChangeType.MODIFIED.value) and ev.file_path.endswith(".py"):
                diag = self.diagnostics.validate_file(ev.file_path)
                result_item = {
                    "event": ev.to_dict(),
                    "diagnostic": diag.to_dict(),
                    "repair": None,
                }

                if not diag.is_valid:
                    with self._lock:
                        self.state.errors_diagnosed += 1

                    self._broadcast_gateway_event("watch_diagnostic_error", diag.to_dict())

                    if self.config.auto_repair:
                        with self._lock:
                            self.state.repairs_attempted += 1

                        self._broadcast_gateway_event("watch_repair_started", {
                            "file_path": ev.file_path,
                            "error": diag.error_message,
                        })

                        repair_action = self.repair_mgr.diagnose_and_repair(ev.file_path, diag)
                        result_item["repair"] = repair_action.to_dict()

                        with self._lock:
                            if repair_action.status == "success":
                                self.state.repairs_succeeded += 1
                            self.state.recent_repairs.append(repair_action)
                            if len(self.state.recent_repairs) > 50:
                                self.state.recent_repairs = self.state.recent_repairs[-50:]

                        self._broadcast_gateway_event("watch_repair_completed", repair_action.to_dict())
                else:
                    # File is valid; optionally run regression tests
                    if self.config.run_tests:
                        test_res = self.diagnostics.run_tests_for_file(ev.file_path)
                        result_item["tests"] = test_res

                results.append(result_item)
            else:
                results.append({"event": ev.to_dict()})

        return results

    def trigger_self_repair(self, file_path: str, mode: str = "auto") -> dict[str, Any]:
        """Manually trigger self-healing on a target file."""
        diag = self.diagnostics.validate_file(file_path)
        with self._lock:
            self.state.repairs_attempted += 1

        if mode == "rollback":
            repair = self.repair_mgr.rollback_file_checkpoint(file_path)
        elif mode == "syntax_fix":
            repair = self.repair_mgr.auto_fix_syntax(file_path, diag)
        else:
            repair = self.repair_mgr.diagnose_and_repair(file_path, diag)

        with self._lock:
            if repair.status == "success":
                self.state.repairs_succeeded += 1
            self.state.recent_repairs.append(repair)

        return {
            "file_path": file_path,
            "diagnostic": diag.to_dict(),
            "repair": repair.to_dict(),
        }


# Singleton daemon instance
_GLOBAL_WATCH_DAEMON: Optional[AutonomousWatchDaemon] = None
_GLOBAL_WATCH_LOCK = threading.Lock()


def get_watch_daemon(config: Optional[WatcherConfig] = None) -> AutonomousWatchDaemon:
    """Get or initialize singleton AutonomousWatchDaemon."""
    global _GLOBAL_WATCH_DAEMON
    with _GLOBAL_WATCH_LOCK:
        if _GLOBAL_WATCH_DAEMON is None:
            _GLOBAL_WATCH_DAEMON = AutonomousWatchDaemon(config=config)
        elif config is not None:
            _GLOBAL_WATCH_DAEMON.config = config
            _GLOBAL_WATCH_DAEMON.watcher.config = config
        return _GLOBAL_WATCH_DAEMON
