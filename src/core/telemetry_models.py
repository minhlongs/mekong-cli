"""Mekong CLI - Telemetry Data Models.

Dataclasses for execution trace telemetry and subsystem health metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class StepTrace:
    """Trace data for a single execution step."""

    step_order: int
    title: str
    duration_seconds: float
    exit_code: int
    self_healed: bool = False
    agent_used: str | None = None


@dataclass
class ExecutionTrace:
    """Complete trace for one orchestration run."""

    goal: str
    steps: list[StepTrace] = field(default_factory=list)
    total_duration: float = 0.0
    llm_calls: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class SubsystemHealth:
    """Health metrics for a single AGI subsystem.

    Tracks activation count, success contribution, and latency
    for each of the 9 AGI subsystems (Memory, Reflection, WorldModel, etc.).
    """

    subsystem: str
    activation_count: int = 0
    success_contribution: float = 0.0
    avg_latency_ms: float = 0.0
    error_count: int = 0
    last_activated: datetime | None = None

    def record_activation(self, latency_ms: float, success: bool) -> None:
        """Record a subsystem activation event."""
        self.activation_count += 1
        if not success:
            self.error_count += 1
        # Running average for latency
        prev_total = self.avg_latency_ms * (self.activation_count - 1)
        self.avg_latency_ms = (prev_total + latency_ms) / self.activation_count
        self.last_activated = datetime.now(timezone.utc)

    @property
    def success_rate(self) -> float:
        """Subsystem success rate (0.0 - 1.0)."""
        if self.activation_count == 0:
            return 0.0
        return (self.activation_count - self.error_count) / self.activation_count

    def to_dict(self) -> dict:
        """Serialize to dict for reporting."""
        return {
            "subsystem": self.subsystem,
            "activation_count": self.activation_count,
            "success_contribution": self.success_contribution,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "error_count": self.error_count,
            "success_rate": round(self.success_rate, 4),
            "last_activated": (
                self.last_activated.isoformat() if self.last_activated else None
            ),
        }


@dataclass
class SubsystemHealthReport:
    """Aggregated health report across all subsystems."""

    subsystems: list[SubsystemHealth] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def add_subsystem(self, health: SubsystemHealth) -> None:
        """Add or update subsystem health entry."""
        for i, s in enumerate(self.subsystems):
            if s.subsystem == health.subsystem:
                self.subsystems[i] = health
                return
        self.subsystems.append(health)

    def get_subsystem(self, name: str) -> SubsystemHealth | None:
        """Get health for a specific subsystem."""
        for s in self.subsystems:
            if s.subsystem == name:
                return s
        return None

    @property
    def total_activations(self) -> int:
        """Total activations across all subsystems."""
        return sum(s.activation_count for s in self.subsystems)

    @property
    def active_count(self) -> int:
        """Number of subsystems with at least one activation."""
        return sum(1 for s in self.subsystems if s.activation_count > 0)

    @property
    def coverage(self) -> float:
        """Subsystem coverage ratio (active/total)."""
        if not self.subsystems:
            return 0.0
        return self.active_count / len(self.subsystems)

    def to_dict(self) -> dict:
        """Serialize full report."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "total_activations": self.total_activations,
            "active_count": self.active_count,
            "coverage": round(self.coverage, 4),
            "subsystems": [s.to_dict() for s in self.subsystems],
        }


__all__ = [
    "ExecutionTrace",
    "StepTrace",
    "SubsystemHealth",
    "SubsystemHealthReport",
]
