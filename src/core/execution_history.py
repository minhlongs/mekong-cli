# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Execution History (Event Sourcing)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import json
from pathlib import Path
import time
from typing import Any
import uuid


class EventKind(str, Enum):
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    STEP_SCHEDULED = "step_scheduled"
    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_RETRIED = "step_retried"
    STEP_HEARTBEAT = "step_heartbeat"
    ROLLBACK_STARTED = "rollback_started"
    ROLLBACK_COMPLETED = "rollback_completed"
    SELF_HEAL_ATTEMPTED = "self_heal_attempted"
    SELF_HEAL_SUCCEEDED = "self_heal_succeeded"
    CHECKPOINT_SAVED = "checkpoint_saved"


@dataclass
class ExecutionEvent:
    event_id: str
    kind: EventKind
    timestamp: float
    workflow_id: str
    step_order: int | None = None
    data: dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def create(
        kind: EventKind, workflow_id: str, step_order: int | None = None, data: dict[str, Any] | None = None,
    ) -> "ExecutionEvent":
        return ExecutionEvent(
            event_id=uuid.uuid4().hex[:12], kind=kind, timestamp=time.time(),
            workflow_id=workflow_id, step_order=step_order, data=data or {},
        )


class ExecutionHistory:
    """Append-only event log for workflow execution."""

    def __init__(self, storage_dir: str | None = None, batch_size: int = 10) -> None:
        self._storage_dir = Path(storage_dir) if storage_dir else Path(".mekong/history")
        self._events: dict[str, list[ExecutionEvent]] = {}
        self._batch_size = batch_size
        self._pending_events: dict[str, list[ExecutionEvent]] = {}

    def append(self, event: ExecutionEvent) -> None:
        wf_id = event.workflow_id
        self._events.setdefault(wf_id, []).append(event)
        self._pending_events.setdefault(wf_id, []).append(event)
        if len(self._pending_events[wf_id]) >= self._batch_size:
            self.flush(wf_id)

    def get_history(self, workflow_id: str) -> list[ExecutionEvent]:
        return sorted(self._events.get(workflow_id, []), key=lambda e: e.timestamp)

    def get_last_checkpoint(self, workflow_id: str) -> int | None:
        last_completed = 0
        for event in self.get_history(workflow_id):
            if event.kind == EventKind.STEP_COMPLETED and event.step_order:
                last_completed = max(last_completed, event.step_order)
        return last_completed if last_completed > 0 else None

    def get_step_events(self, workflow_id: str, step_order: int) -> list[ExecutionEvent]:
        return [e for e in self.get_history(workflow_id) if e.step_order == step_order]

    def get_retry_count(self, workflow_id: str, step_order: int) -> int:
        return sum(1 for e in self.get_step_events(workflow_id, step_order) if e.kind == EventKind.STEP_RETRIED)

    def persist(self, workflow_id: str) -> Path:
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._storage_dir / f"{workflow_id}.jsonl"
        with open(filepath, "a", encoding="utf-8") as f:
            for event in self._events.get(workflow_id, []):
                f.write(json.dumps(asdict(event), default=str) + "\n")
        return filepath

    def flush(self, workflow_id: str) -> Path | None:
        if not self._pending_events.get(workflow_id):
            return None
        self._storage_dir.mkdir(parents=True, exist_ok=True)
        filepath = self._storage_dir / f"{workflow_id}.jsonl"
        with open(filepath, "a", encoding="utf-8") as f:
            for event in self._pending_events[workflow_id]:
                f.write(json.dumps(asdict(event), default=str) + "\n")
        self._pending_events[workflow_id] = []
        return filepath

    def flush_all(self) -> None:
        for wf_id in list(self._pending_events.keys()):
            self.flush(wf_id)

    def load(self, workflow_id: str) -> list[ExecutionEvent]:
        filepath = self._storage_dir / f"{workflow_id}.jsonl"
        if not filepath.exists():
            return []
        events: list[ExecutionEvent] = []
        for line in filepath.read_text(encoding="utf-8").strip().split("\n"):
            if not line:
                continue
            raw = json.loads(line)
            raw["kind"] = EventKind(raw["kind"])
            events.append(ExecutionEvent(**raw))
        self._events[workflow_id] = events
        return events

    def workflow_ids(self) -> list[str]:
        if not self._storage_dir.exists():
            return []
        return [p.stem for p in self._storage_dir.glob("*.jsonl")]

    def clear(self, workflow_id: str) -> None:
        self._events.pop(workflow_id, None)
        filepath = self._storage_dir / f"{workflow_id}.jsonl"
        if filepath.exists():
            filepath.unlink()


__all__ = ["EventKind", "ExecutionEvent", "ExecutionHistory"]
