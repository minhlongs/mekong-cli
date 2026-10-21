"""Data models and enums for the PEV Swarm Bridge & Checkpoint Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class PevPhase(str, Enum):
    """Canonical PEV lifecycle phases."""

    PLAN = "plan"
    EXECUTE = "execute"
    VERIFY = "verify"


class MissionStatus(str, Enum):
    """High-level status of a PEV swarm mission."""

    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class TaskStatus(str, Enum):
    """Execution status of an individual task in a PEV plan."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class VerificationCriteria:
    """Acceptance criteria and rubrics for verifying task deliverables."""

    exit_code: Optional[int] = 0
    file_exists: list[str] = field(default_factory=list)
    test_command: Optional[str] = None
    output_contains: list[str] = field(default_factory=list)
    output_not_contains: list[str] = field(default_factory=list)
    rubric_prompt: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VerificationCriteria":
        if not data:
            return cls()
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in valid_keys})


@dataclass
class PevTask:
    """Individual task within a PEV execution DAG."""

    task_id: str
    mission_id: str
    order_idx: int
    title: str
    description: str
    role: str
    phase: PevPhase = PevPhase.EXECUTE
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[str] = field(default_factory=list)
    context_budget: int = 24000
    allowed_tools: list[str] = field(default_factory=list)
    verification_criteria: VerificationCriteria = field(default_factory=VerificationCriteria)
    attempts: int = 0
    max_attempts: int = 3
    result_summary: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["phase"] = self.phase.value if isinstance(self.phase, PevPhase) else str(self.phase)
        d["status"] = self.status.value if isinstance(self.status, TaskStatus) else str(self.status)
        d["verification_criteria"] = self.verification_criteria.to_dict()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PevTask":
        d = dict(data)
        if isinstance(d.get("phase"), str):
            d["phase"] = PevPhase(d["phase"])
        if isinstance(d.get("status"), str):
            d["status"] = TaskStatus(d["status"])
        if isinstance(d.get("verification_criteria"), dict):
            d["verification_criteria"] = VerificationCriteria.from_dict(d["verification_criteria"])
        valid_keys = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in d.items() if k in valid_keys})


@dataclass
class PevPlan:
    """Structured execution plan resulting from the Plan phase."""

    goal: str
    mission_id: str
    tasks: list[PevTask]
    subagent_assignments: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "mission_id": self.mission_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "subagent_assignments": self.subagent_assignments,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PevPlan":
        tasks = [PevTask.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            goal=data.get("goal", ""),
            mission_id=data.get("mission_id", ""),
            tasks=tasks,
            subagent_assignments=data.get("subagent_assignments", {}),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FileSnapshot:
    """Byte-level snapshot of a workspace file."""

    relative_path: str
    sha256: str
    content_type: str  # "utf-8" or "base64"
    content: str
    size_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CheckpointRecord:
    """Durable point-in-time snapshot of mission state and workspace files."""

    checkpoint_id: str
    mission_id: str
    task_id: Optional[str]
    cycle: int
    phase: str
    label: str
    task_states: dict[str, str]
    test_results: dict[str, Any]
    file_snapshots: list[FileSnapshot] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["file_snapshots"] = [f.to_dict() for f in self.file_snapshots]
        return d
