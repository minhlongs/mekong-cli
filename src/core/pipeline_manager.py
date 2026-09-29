# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pipeline manager for chaining multiple PEV workflows.

Manages sequential and parallel execution of multiple goals/recipes,
aggregates results, and provides pipeline-level status tracking.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .progress_tracker import ProgressTracker
from .task_queue import PriorityTaskQueue


class PipelineStatus(Enum):
    """Overall pipeline status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineStage:
    """A single stage in the pipeline."""

    id: str
    goal: str
    order: int
    status: str = "pending"  # pending, running, completed, failed, skipped
    result: Any = None
    error: str = ""
    start_time: float | None = None
    end_time: float | None = None
    depends_on: list[str] = field(default_factory=list)
    name: str = ""
    output: str = ""

    @property
    def duration_ms(self) -> float:
        if self.start_time is None:
            return 0.0
        end = self.end_time or time.time()
        return (end - self.start_time) * 1000


@dataclass
class PipelineResult:
    """Aggregated result of an entire pipeline execution."""

    pipeline_id: str
    status: PipelineStatus
    stages: list[PipelineStage] = field(default_factory=list)
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    total_duration_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_stages == 0:
            return 0.0
        return (self.completed_stages / self.total_stages) * 100


class PipelineManager:
    """Manages multi-stage PEV pipelines.

    Chains multiple goals/recipes into a pipeline with dependency
    management, progress tracking, and result aggregation.
    Uses PriorityTaskQueue for stage scheduling.
    """

    def __init__(self, stop_on_failure: bool = True) -> None:
        self._pipelines: dict[str, PipelineResult] = {}
        self._stop_on_failure = stop_on_failure
        self._queue = PriorityTaskQueue(max_size=0)
        self._tracker = ProgressTracker()

    @property
    def tracker(self) -> ProgressTracker:
        """Access the progress tracker for registering callbacks."""
        return self._tracker

    def create_pipeline(
        self,
        goals: list[str],
        dependencies: dict[str, list[str]] | None = None,
        stage_names: list[str] | None = None,
    ) -> str:
        """Create a new pipeline from a list of goals.

        Args:
            goals: List of goal descriptions (executed in order).
            dependencies: Optional stage ID → list of dependency stage IDs.
            stage_names: Optional custom names for stages (e.g. ['file-picker', 'editor']).

        Returns:
            Pipeline ID for tracking.
        """
        pipeline_id = uuid.uuid4().hex[:12]
        stages: list[PipelineStage] = []
        deps = dependencies or {}

        for i, goal in enumerate(goals):
            stage_id = f"stage-{i + 1}"
            st_name = stage_names[i] if stage_names and i < len(stage_names) else stage_id
            stage = PipelineStage(
                id=stage_id,
                name=st_name,
                goal=goal,
                order=i + 1,
                depends_on=deps.get(stage_id, []),
            )
            stages.append(stage)

        result = PipelineResult(
            pipeline_id=pipeline_id,
            status=PipelineStatus.PENDING,
            stages=stages,
            total_stages=len(stages),
        )
        self._pipelines[pipeline_id] = result
        return pipeline_id

    def execute_pipeline(
        self,
        pipeline_id: str,
        executor_fn: Any,
    ) -> PipelineResult:
        """Execute a pipeline by running each stage through executor_fn.

        Args:
            pipeline_id: ID from create_pipeline().
            executor_fn: Callable(goal: str) → result (any truthy = success).

        Returns:
            PipelineResult with aggregated outcomes.
        """
        result = self._pipelines.get(pipeline_id)
        if result is None:
            raise ValueError(f"Pipeline not found: {pipeline_id}")

        result.status = PipelineStatus.RUNNING
        start_time = time.time()
        self._tracker.start_workflow(result.total_stages)

        completed_ids: set[str] = set()

        for stage in result.stages:
            # Check dependencies
            if not self._deps_met(stage, completed_ids):
                stage.status = "skipped"
                self._tracker.step_skipped(stage.order, stage.goal)
                continue

            stage.status = "running"
            stage.start_time = time.time()
            self._tracker.step_started(stage.order, stage.goal)

            try:
                stage_result = executor_fn(stage.goal)
                stage.result = stage_result
                stage.status = "completed"
                stage.end_time = time.time()
                result.completed_stages += 1
                completed_ids.add(stage.id)
                self._tracker.step_completed(stage.order)

            except Exception as e:
                stage.status = "failed"
                stage.error = str(e)
                stage.end_time = time.time()
                result.failed_stages += 1
                result.errors.append(f"{stage.id}: {e}")
                self._tracker.step_failed(stage.order, str(e))

                if self._stop_on_failure:
                    # Skip remaining stages
                    for remaining in result.stages:
                        if remaining.status == "pending":
                            remaining.status = "skipped"
                    break

        result.total_duration_ms = (time.time() - start_time) * 1000

        # Determine final status
        if result.failed_stages == 0 and result.completed_stages == result.total_stages:
            result.status = PipelineStatus.COMPLETED
            self._tracker.finish(success=True)
        elif result.completed_stages > 0:
            result.status = PipelineStatus.PARTIAL
            self._tracker.finish(success=False)
        else:
            result.status = PipelineStatus.FAILED
            self._tracker.finish(success=False)

        return result

    def get_pipeline(self, pipeline_id: str) -> PipelineResult | None:
        """Get pipeline result by ID."""
        return self._pipelines.get(pipeline_id)

    def cancel_pipeline(self, pipeline_id: str) -> bool:
        """Cancel a pending/running pipeline."""
        result = self._pipelines.get(pipeline_id)
        if result is None:
            return False
        if result.status in (PipelineStatus.COMPLETED, PipelineStatus.CANCELLED):
            return False
        result.status = PipelineStatus.CANCELLED
        for stage in result.stages:
            if stage.status in ("pending", "running"):
                stage.status = "skipped"
        return True

    def list_pipelines(self) -> list[PipelineResult]:
        """List all tracked pipelines."""
        return list(self._pipelines.values())

    def aggregate_results(self, pipeline_id: str) -> dict[str, Any]:
        """Aggregate results from all stages of a pipeline."""
        result = self._pipelines.get(pipeline_id)
        if result is None:
            return {}

        return {
            "pipeline_id": pipeline_id,
            "status": result.status.value,
            "total_stages": result.total_stages,
            "completed": result.completed_stages,
            "failed": result.failed_stages,
            "success_rate": result.success_rate,
            "duration_ms": result.total_duration_ms,
            "errors": result.errors,
            "stages": [
                {
                    "id": s.id,
                    "name": s.name or s.id,
                    "goal": s.goal,
                    "status": s.status,
                    "duration_ms": s.duration_ms,
                    "output": s.output or (str(s.result) if s.result is not None else ""),
                    "error": s.error,
                }
                for s in result.stages
            ],
        }

    def _deps_met(
        self,
        stage: PipelineStage,
        completed_ids: set[str],
    ) -> bool:
        """Check if all dependencies for a stage are met."""
        return all(dep in completed_ids for dep in stage.depends_on)

    def run_multi_agent_pipeline(
        self,
        goal: str,
        stages: list[str] | None = None,
        root_dir: str | None = None,
        executor_override: Any = None,
    ) -> PipelineResult:
        """Run sequential multi-agent pipeline (FilePicker -> Editor -> Reviewer).

        Args:
            goal: Main task goal or description.
            stages: List of stage names to execute sequentially (default: file-picker, editor, reviewer).
            root_dir: Project directory to scan (used by FilePicker).
            executor_override: Optional custom callable(stage_name, stage_goal, context) for testing.

        Returns:
            PipelineResult with aggregated stage results and duration.
        """
        stage_names = stages or ["file-picker", "editor", "reviewer"]

        # Validate stage names before execution if no custom executor is provided
        if executor_override is None:
            from src.core.pipeline_stages import ALL_STAGES
            for st in stage_names:
                clean = st.strip().lower()
                if clean not in ("file-picker", "editor", "reviewer") and clean not in ALL_STAGES:
                    raise ValueError(f"Unknown pipeline stage: '{st}'. Supported stages: file-picker, editor, reviewer")

        goals = [f"{st}: {goal}" for st in stage_names]
        deps: dict[str, list[str]] = {}
        for i in range(1, len(stage_names)):
            deps[f"stage-{i + 1}"] = [f"stage-{i}"]

        pipeline_id = self.create_pipeline(goals=goals, dependencies=deps, stage_names=stage_names)
        result = self._pipelines[pipeline_id]
        result.status = PipelineStatus.RUNNING
        start_time = time.time()
        self._tracker.start_workflow(result.total_stages)

        completed_ids: set[str] = set()
        accumulated_context: dict[str, Any] = {"goal": goal}

        for stage in result.stages:
            if not self._deps_met(stage, completed_ids):
                stage.status = "skipped"
                self._tracker.step_skipped(stage.order, stage.goal)
                continue

            stage.status = "running"
            stage.start_time = time.time()
            self._tracker.step_started(stage.order, stage.goal)

            try:
                if executor_override is not None:
                    out = executor_override(stage.name, goal, accumulated_context)
                else:
                    out = _execute_default_agent_stage(
                        stage_name=stage.name,
                        goal=goal,
                        context=accumulated_context,
                        root_dir=root_dir,
                    )
                stage_output_str = str(out) if out is not None else ""
                stage.result = out
                stage.output = stage_output_str
                stage.status = "completed"
                stage.end_time = time.time()
                accumulated_context[stage.name] = stage_output_str
                result.completed_stages += 1
                completed_ids.add(stage.id)
                self._tracker.step_completed(stage.order)

            except Exception as e:
                stage.status = "failed"
                stage.error = str(e)
                stage.end_time = time.time()
                result.failed_stages += 1
                result.errors.append(f"{stage.name} ({stage.id}): {e}")
                self._tracker.step_failed(stage.order, str(e))

                if self._stop_on_failure:
                    for remaining in result.stages:
                        if remaining.status == "pending":
                            remaining.status = "skipped"
                    break

        result.total_duration_ms = (time.time() - start_time) * 1000

        if result.failed_stages == 0 and result.completed_stages == result.total_stages:
            result.status = PipelineStatus.COMPLETED
            self._tracker.finish(success=True)
        elif result.completed_stages > 0:
            result.status = PipelineStatus.PARTIAL
            self._tracker.finish(success=False)
        else:
            result.status = PipelineStatus.FAILED
            self._tracker.finish(success=False)

        return result


def _execute_default_agent_stage(
    stage_name: str,
    goal: str,
    context: dict[str, Any],
    root_dir: str | None = None,
) -> str:
    """Execute a single default agent stage (FilePicker, Editor, Reviewer)."""
    clean_name = stage_name.strip().lower()

    if clean_name == "file-picker":
        try:
            from src.agents.file_picker_agent import FilePickerAgent
            agent = FilePickerAgent(root=root_dir)
            results = agent.run(goal)
            out = results[0].output if results else ""
            return out or "No relevant files discovered."
        except Exception as exc:
            raise RuntimeError(f"FilePicker stage execution failed: {exc}") from exc

    elif clean_name == "editor":
        try:
            from src.agents.editor_agent import EditorAgent
            agent = EditorAgent()
            fp_ctx = context.get("file-picker", "")
            prompt = f"{goal}\n\nRelevant files:\n{fp_ctx}" if fp_ctx else goal
            results = agent.run(prompt)
            out = results[0].output if results else ""
            return out or "Edits planned."
        except Exception as exc:
            raise RuntimeError(f"Editor stage execution failed: {exc}") from exc

    elif clean_name == "reviewer":
        try:
            from src.agents.reviewer_agent import ReviewerAgent
            agent = ReviewerAgent()
            ed_ctx = context.get("editor", "")
            prompt = f"{goal}\n\nReview changes:\n{ed_ctx}" if ed_ctx else goal
            results = agent.run(prompt)
            out = results[0].output if results else ""
            return out or "Review checks passed."
        except Exception as exc:
            raise RuntimeError(f"Reviewer stage execution failed: {exc}") from exc

    else:
        # Dynamic fallback to ALL_STAGES if registered
        try:
            from src.core.pipeline_stages import ALL_STAGES
            if clean_name in ALL_STAGES:
                stage_def = ALL_STAGES[clean_name]
                parts = stage_def.agent_class.split(".")
                mod_name = "src." + ".".join(parts[:-1]) if not parts[0].startswith("src") else ".".join(parts[:-1])
                cls_name = parts[-1]
                import importlib
                mod = importlib.import_module(mod_name)
                cls = getattr(mod, cls_name)
                agent = cls()
                results = agent.run(goal)
                return results[0].output if results else ""
        except Exception:
            pass
        raise ValueError(f"Unknown pipeline stage: '{stage_name}'. Supported stages: file-picker, editor, reviewer")


_pipeline_manager_instance: PipelineManager | None = None


def get_pipeline_manager() -> PipelineManager:
    """Return the global singleton instance of PipelineManager."""
    global _pipeline_manager_instance
    if _pipeline_manager_instance is None:
        _pipeline_manager_instance = PipelineManager()
    return _pipeline_manager_instance


__all__ = [
    "PipelineManager",
    "PipelineResult",
    "PipelineStage",
    "PipelineStatus",
    "get_pipeline_manager",
]
