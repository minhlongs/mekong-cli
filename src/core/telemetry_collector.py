# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Telemetry Collector — Usage Event Collection."""

import atexit
import dataclasses
import hashlib
import json
import platform
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .telemetry_consent import ConsentManager


@dataclass
class TelemetryEvent:
    event_type: str
    anonymous_id: str
    timestamp: str
    session_id: str
    properties: Dict[str, Any] = field(default_factory=dict)
    cli_version: str = "3.0.0"
    mission_id: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class TelemetryCollector:
    """Collect anonymized usage telemetry and execution traces."""

    def __init__(self, consent_manager: Optional[ConsentManager] = None, output_dir: Optional[str] = None) -> None:
        self._consent_manager = consent_manager or ConsentManager()
        self._buffer: List[TelemetryEvent] = []
        self._session_id: Optional[str] = None
        self._session_start: Optional[float] = None
        self._commands_count = 0
        self._max_buffer_size = 50
        self._storage_file = Path.home() / ".mekong" / "telemetry-buffer.json"
        self._initialized = False
        self._output_dir: Optional[Path] = Path(output_dir) if output_dir else None
        self._current_trace: Optional[Any] = None
        self._trace_start_time: Optional[float] = None
        atexit.register(self._flush_on_exit)

    def start_trace(self, goal: str) -> None:
        from .telemetry_models import ExecutionTrace
        self._current_trace = ExecutionTrace(goal=goal)
        self._trace_start_time = time.time()

    def finish_trace(self) -> Any:
        from .telemetry_models import ExecutionTrace
        if self._current_trace is None:
            self._current_trace = ExecutionTrace(goal="")
        if self._trace_start_time is not None:
            self._current_trace.total_duration = time.time() - self._trace_start_time
        trace = self._current_trace
        if self._output_dir is not None:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            (self._output_dir / "execution_trace.json").write_text(json.dumps(dataclasses.asdict(trace), indent=2))
        self._current_trace = self._trace_start_time = None
        return trace

    def get_trace(self) -> Any:
        return self._current_trace

    def record_step(self, step_order: int, title: str, duration_seconds: float = 0.0, exit_code: int = 0, self_healed: bool = False, agent: Optional[str] = None, duration: Optional[float] = None) -> None:
        if self._current_trace is not None:
            from .telemetry_models import StepTrace
            self._current_trace.steps.append(StepTrace(step_order=step_order, title=title, duration_seconds=duration if duration is not None else duration_seconds, exit_code=exit_code, self_healed=self_healed, agent_used=agent))

    def record_llm_call(self) -> None:
        if self._current_trace is not None:
            self._current_trace.llm_calls += 1

    def record_error(self, error_message: str) -> None:
        if self._current_trace is not None:
            self._current_trace.errors.append(error_message)

    def _ensure_anonymous_id(self) -> Optional[str]:
        return self._consent_manager.get_anonymous_id() if self._consent_manager.has_consent() else None

    def _get_session_id(self) -> str:
        if not self._session_id:
            self._session_id = str(uuid.uuid4())
        return self._session_id

    def _hash_error(self, error_message: str) -> str:
        return hashlib.sha256(error_message.encode()).hexdigest()[:16]

    def _get_python_version(self) -> str:
        return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    def _get_os_info(self) -> str:
        return platform.system() or "unknown"

    def _append_event(self, event_type: str, anon_id: str, props: Dict[str, Any], mission_id: Optional[str] = None) -> None:
        self._buffer.append(TelemetryEvent(event_type, anon_id, datetime.now(timezone.utc).isoformat(), self._get_session_id(), props, "3.0.0", mission_id))

    def session_start(self, mission_id: Optional[str] = None) -> None:
        if not self._initialized:
            if anon_id := self._ensure_anonymous_id():
                self._session_start = time.time()
                self._append_event("session_started", anon_id, {"cli_version": "3.0.0", "python_version": self._get_python_version(), "os": self._get_os_info()}, mission_id)
            self._initialized = True

    def command_executed(self, command_name: str, duration_ms: int, exit_code: int, error_type: Optional[str] = None, mission_id: Optional[str] = None) -> None:
        if not self._initialized:
            self.session_start()
        if anon_id := self._ensure_anonymous_id():
            self._commands_count += 1
            props: Dict[str, Any] = {"command": command_name, "duration_ms": duration_ms, "exit_code": exit_code, "success": exit_code == 0, **({"error_type_hash": self._hash_error(error_type)} if error_type else {})}
            self._append_event("command_executed", anon_id, props, mission_id)
            self._check_buffer()

    def error_occurred(self, error_type: str, error_message: str, command_name: Optional[str] = None, mission_id: Optional[str] = None) -> None:
        if anon_id := self._ensure_anonymous_id():
            self._append_event("error_occurred", anon_id, {"error_type": error_type, "error_message_hash": self._hash_error(error_message), "command": command_name}, mission_id)
            self._check_buffer()

    def session_end(self, mission_id: Optional[str] = None) -> None:
        if anon_id := self._ensure_anonymous_id():
            self._append_event("session_ended", anon_id, {"duration_ms": int((time.time() - self._session_start) * 1000) if self._session_start else 0, "commands_count": self._commands_count}, mission_id)

    def _check_buffer(self) -> None:
        if len(self._buffer) >= self._max_buffer_size:
            self._flush()

    def _flush(self) -> None:
        if self._buffer:
            self._storage_file.parent.mkdir(parents=True, exist_ok=True)
            self._storage_file.write_text(json.dumps(self.get_pending_events() + [e.to_dict() for e in self._buffer], indent=2))
            self._buffer = []

    def _flush_on_exit(self) -> None:
        self.session_end()
        self._flush()

    def get_pending_events(self) -> List[dict]:
        try:
            return json.loads(self._storage_file.read_text()) if self._storage_file.exists() else []
        except json.JSONDecodeError:
            return []

    def clear_buffer(self) -> None:
        if self._storage_file.exists():
            self._storage_file.unlink()


_collector: Optional[TelemetryCollector] = None


def get_collector() -> TelemetryCollector:
    global _collector
    if _collector is None:
        _collector = TelemetryCollector()
    return _collector


def track_command(command_name: str, duration_ms: int = 0, exit_code: int = 0, error_type: Optional[str] = None) -> None:
    get_collector().command_executed(command_name, duration_ms, exit_code, error_type)


def track_error(error_type: str, error_message: str, command_name: Optional[str] = None) -> None:
    get_collector().error_occurred(error_type, error_message, command_name)
