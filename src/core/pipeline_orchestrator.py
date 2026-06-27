"""Pipeline orchestrator for multi-agent Codebuff-style workflows.

Runs sequential pipeline stages (file-picker -> editor -> reviewer),
passing results between stages as context. Each stage instantiates
an agent from the registry, runs plan->execute->verify, and returns
a structured result.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum

from .agent_registry import AgentRegistry
from .agent_base import AgentBase, Result

logger = logging.getLogger(__name__)

# Default pipeline: file-picker -> editor -> reviewer
DEFAULT_PIPELINE: list[str] = ["file-picker", "editor", "reviewer"]


class StageStatus(Enum):
    """Status of a single pipeline stage."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a single pipeline stage."""

    agent_name: str
    status: StageStatus
    task_results: list[Result] = field(default_factory=list)
    output: str | None = None
    error: str | None = None
    duration_ms: float = 0.0
    start_time: float | None = None
    end_time: float | None = None


@dataclass
class PipelineResult:
    """Aggregated result of a full pipeline execution."""

    pipeline_id: str
    goal: str
    stages: list[StageResult] = field(default_factory=list)
    final_status: str = "pending"
    total_duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if not self.stages:
            return 0.0
        passed = sum(1 for s in self.stages if s.status == StageStatus.PASSED)
        return (passed / len(self.stages)) * 100

    def stage_outputs(self) -> dict[str, str]:
        """Return mapping of agent_name -> output for all passed stages."""
        return {s.agent_name: s.output or "" for s in self.stages if s.output}


class PipelineOrchestrator:
    """Orchestrates multi-agent pipeline execution.

    Runs a sequence of agents (stages), passing each stage's output
    as context to the next. Follows the plan->execute->verify pattern
    from AgentBase.

    Args:
        registry: AgentRegistry to resolve agent names. Defaults to the
            global singleton from src.agents.
        stages: Ordered list of agent names to run. Defaults to
            DEFAULT_PIPELINE (file-picker -> editor -> reviewer).
    """

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        stages: list[str] | None = None,
    ) -> None:
        self.registry = registry or _get_default_registry()
        self.stages = stages or list(DEFAULT_PIPELINE)

    def run(self, goal: str) -> PipelineResult:
        """Run the full pipeline against a goal.

        Args:
            goal: High-level description of what to accomplish.

        Returns:
            PipelineResult with all stage outputs and final status.
        """
        pipeline_id = str(uuid.uuid4())[:8]
        result = PipelineResult(pipeline_id=pipeline_id, goal=goal)
        t0 = time.monotonic()

        context: str = goal

        for agent_name in self.stages:
            stage = self._run_stage(agent_name, context)
            result.stages.append(stage)

            if stage.status == StageStatus.FAILED:
                result.final_status = "failed"
                result.errors.append(
                    f"[{agent_name}] {stage.error or 'stage failed'}"
                )
                break

            # Pass this stage's output as context to the next
            if stage.output:
                context = stage.output

        if result.final_status == "pending":
            result.final_status = "completed"

        result.total_duration_ms = (time.monotonic() - t0) * 1000
        return result

    def _run_stage(self, agent_name: str, context: str) -> StageResult:
        """Run a single pipeline stage.

        Args:
            agent_name: Registered agent name to instantiate.
            context: Input text for the agent (goal + prior stage output).

        Returns:
            StageResult with status, output, and timing.
        """
        stage = StageResult(
            agent_name=agent_name,
            status=StageStatus.PENDING,
        )
        stage.start_time = time.monotonic()

        # Resolve agent from registry
        try:
            agent_cls: type[AgentBase] = self.registry.get(agent_name)
        except KeyError:
            stage.status = StageStatus.FAILED
            stage.error = f"Unknown agent: '{agent_name}'. Available: {self.registry.list_agents()}"
            stage.end_time = time.monotonic()
            stage.duration_ms = (stage.end_time - stage.start_time) * 1000
            logger.error("Pipeline stage failed: %s", stage.error)
            return stage

        # Instantiate and run
        try:
            agent: AgentBase = agent_cls()
        except Exception as exc:
            stage.status = StageStatus.FAILED
            stage.error = f"Failed to instantiate {agent_name}: {exc}"
            stage.end_time = time.monotonic()
            stage.duration_ms = (stage.end_time - stage.start_time) * 1000
            logger.error("Pipeline stage failed: %s", stage.error)
            return stage

        stage.status = StageStatus.RUNNING
        logger.info("Pipeline stage [%s]: running with context=%s", agent_name, context[:80])

        try:
            task_results: list[Result] = agent.run(context)
            stage.task_results = task_results

            # Check if all tasks succeeded
            all_passed = all(r.success for r in task_results)
            if not all_passed:
                stage.status = StageStatus.FAILED
                errors = [r.error for r in task_results if r.error]
                stage.error = "; ".join(errors) if errors else "One or more tasks failed"
                logger.warning("Pipeline stage [%s]: failed", agent_name)
            else:
                stage.status = StageStatus.PASSED
                # Concatenate outputs from all tasks
                outputs = [r.output for r in task_results if r.output]
                stage.output = "\n".join(str(o) for o in outputs)
                logger.info("Pipeline stage [%s]: passed", agent_name)

        except Exception as exc:
            stage.status = StageStatus.FAILED
            stage.error = str(exc)
            logger.exception("Pipeline stage [%s]: exception", agent_name)

        stage.end_time = time.monotonic()
        stage.duration_ms = (stage.end_time - stage.start_time) * 1000
        return stage


def _get_default_registry() -> AgentRegistry:
    """Return the global agent registry, importing lazily to avoid circular deps."""
    from src.agents import registry  # noqa: PLC0415
    return registry


# Export
__all__ = [
    "PipelineOrchestrator",
    "PipelineResult",
    "StageResult",
    "StageStatus",
    "DEFAULT_PIPELINE",
]
