"""Data models and enums for the Mekong Core Runtime."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.core.protocols import Step


class RepairStrategy(str, Enum):
    RETRY, FALLBACK, ESCALATE, ROLLBACK = "retry", "fallback", "escalate", "rollback"


class Scope(str, Enum):
    SESSION, ORG, GLOBAL = "session", "org", "global"


@dataclass(frozen=True)
class AgentId:
    name: str


@dataclass(frozen=True)
class CheckSpec:
    kind: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SideEffect:
    kind: str
    target: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepairAction:
    strategy: RepairStrategy = RepairStrategy.RETRY
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    principal: str
    session_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "principal": self.principal,
            "session_id": self.session_id,
            "metadata": dict(self.metadata),
        }

    def __getitem__(self, key: str) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return self.metadata[key]

    def get(self, key: str, default: Any = None) -> Any:
        if hasattr(self, key):
            return getattr(self, key)
        return self.metadata.get(key, default)

    def __contains__(self, key: object) -> bool:
        return hasattr(self, str(key)) or str(key) in self.metadata


@dataclass
class Criteria:
    checks: list[CheckSpec] = field(default_factory=list)


@dataclass
class Goal:
    id: str
    intent: str
    context: Context
    criteria: Criteria
    priority: int = 0


@dataclass
class Task:
    id: str
    step: Step
    agent: AgentId
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Result:
    task_id: str
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    check: CheckSpec
    passed: bool
    detail: str = ""


@dataclass
class Verification:
    passed: bool
    checks: list[CheckResult] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


@dataclass
class Observation:
    result: Result
    metrics: dict[str, Any] = field(default_factory=dict)
    side_effects: list[SideEffect] = field(default_factory=list)


@dataclass
class MemoryEntry:
    key: str
    value: Any
    scope: Scope = Scope.SESSION
    timestamp: float = field(default_factory=time.time)


@dataclass
class CommitRecord:
    id: str
    result: Result
    memory_refs: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


_DEFAULT_CRITERIA = Criteria(checks=[CheckSpec(kind="exit_code", params={"expected": 0})])
_MAX_REPAIR_ATTEMPTS = 3
