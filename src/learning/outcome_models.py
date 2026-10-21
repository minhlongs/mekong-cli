# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Outcome Recorder Models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class OutcomeStatus(str, Enum):
    """Execution outcome status."""

    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    PARTIAL = "partial"


@dataclass(frozen=True)
class ExecutionOutcome:
    """Single execution outcome record."""

    execution_id: str
    status: OutcomeStatus
    retry_count: int = 0
    started_at: float = field(default_factory=time.time)
    finished_at: float = field(default_factory=time.time)
    duration_ms: float = 0.0
    error_type: str | None = None
    error_message: str | None = None
    provider: str | None = None
    command: str | None = None
    recipe: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for MemoryBridge storage."""
        return {
            "execution_id": self.execution_id,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "provider": self.provider,
            "command": self.command,
            "recipe": self.recipe,
            "metadata": self.metadata,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ExecutionOutcome:
        """Deserialize from dict."""
        return ExecutionOutcome(
            execution_id=data["execution_id"],
            status=OutcomeStatus(data["status"]),
            retry_count=data.get("retry_count", 0),
            started_at=data.get("started_at", time.time()),
            finished_at=data.get("finished_at", time.time()),
            duration_ms=data.get("duration_ms", 0.0),
            error_type=data.get("error_type"),
            error_message=data.get("error_message"),
            provider=data.get("provider"),
            command=data.get("command"),
            recipe=data.get("recipe"),
            metadata=data.get("metadata", {}),
        )
