# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Task Client Models — Subagent Delegation Types & Payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class SubagentType(str, Enum):
    """Supported subagent types for delegation."""
    COOK = "cook"
    PLANNER = "planner"
    DEBUGGER = "debugger"
    RESEARCHER = "researcher"
    CODE_REVIEWER = "code-reviewer"
    TESTER = "tester"
    FULLSTACK_DEVELOPER = "fullstack-developer"
    UI_UX_DESIGNER = "ui-ux-designer"
    DOCS_MANAGER = "docs-manager"
    PROJECT_MANAGER = "project-manager"
    GIT_MANAGER = "git-manager"
    LICENSE = "license"
    BILLING = "billing"
    ANALYTICS = "analytics"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TaskRequest:
    """Request payload for subagent delegation."""
    subagent_type: SubagentType
    goal: str
    complexity: str = "moderate"
    context: Optional[Dict[str, Any]] = None
    options: Dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "subagent_type": self.subagent_type.value,
            "goal": self.goal,
            "complexity": self.complexity,
            "context": self.context,
            "options": self.options,
            "timeout_seconds": self.timeout_seconds,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


@dataclass
class TaskResult:
    """Result from subagent execution."""
    task_id: str
    status: TaskStatus
    output: Optional[str] = None
    error: Optional[str] = None
    subagent_type: Optional[str] = None
    execution_time_ms: Optional[float] = None
    credits_consumed: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "subagent_type": self.subagent_type,
            "execution_time_ms": self.execution_time_ms,
            "credits_consumed": self.credits_consumed,
            "metadata": self.metadata,
        }


@dataclass
class GatewayConfig:
    """RaaS Gateway configuration."""
    base_url: str = "https://api.cashclaw.cc"
    api_version: str = "v2"
    timeout_seconds: int = 30
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
