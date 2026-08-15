"""Mekong CLI - Agent Base Module.

Core logic inherited from ClaudeKit DNA.
Pattern: Plan-Execute-Verify
Extended with Codebuff-inspired fields (backward compatible).
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Coroutine, Union

logger = logging.getLogger(__name__)

# Step hook type: async callbacks for generator-like control flow
# (mirrors Codebuff's handleSteps pattern without breaking sync contract)
StepHook = Coroutine[Any, Any, None]
StepHooksDict = dict[str, StepHook]


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Task:
    """Single task unit."""

    id: str
    description: str
    input: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    output: Union[str, dict, list, None] = None
    error: Union[str, None] = None


@dataclass
class Result:
    """Task execution result."""

    task_id: str
    success: bool
    output: Union[str, dict, list, None] = None
    error: Union[str, None] = None


class AgentBase(ABC):
    """Base class for all Mekong CLI agents.

    Follows ClaudeKit's Plan-Execute-Verify pattern:
    1. Plan: Parse input -> Task list
    2. Execute: Run each task
    3. Verify: Validate output

    Extended with Codebuff-inspired fields (all optional, backward compat):
    - allowed_tools: restrict which tools this agent can invoke
    - spawnable_agents: agent IDs this agent can delegate to
    - output_mode: control result format
    - step_hooks: async callbacks for lifecycle events
    """

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Warn at class-definition time if plan or execute are not overridden."""
        super().__init_subclass__(**kwargs)
        import warnings as _warnings
        # Only warn for concrete (non-abstract) classes missing the methods
        abstract_methods: frozenset = getattr(cls, "__abstractmethods__", frozenset())
        unimplemented = [
            m for m in ("plan", "execute")
            if m in abstract_methods
        ]
        if unimplemented and getattr(cls, "__abstractmethods__", None) != frozenset(unimplemented):
            _warnings.warn(
                f"{cls.__name__} does not implement: {unimplemented}. "
                "Calls to these methods will raise NotImplementedError.",
                stacklevel=2,
            )

    def __init__(
        self,
        name: str,
        max_retries: int = 3,
        allowed_tools: list[str] | None = None,
        spawnable_agents: list[str] | None = None,
        output_mode: str = "last_message",
        step_hooks: dict[str, Any] | None = None,
    ) -> None:
        """Initialize AgentBase with name and retry configuration.

        Args:
            name: Unique identifier for this agent.
            max_retries: Maximum retry attempts per task before marking as failed.
            allowed_tools: Tool names this agent may invoke. Empty = all tools.
            spawnable_agents: Agent IDs this agent can delegate to.
            output_mode: Result format: 'last_message', 'all_messages', 'structured'.
            step_hooks: Async callbacks for lifecycle events
                (on_step_start, on_step_end, on_tool_call, on_error).
        """
        self.name = name
        self.max_retries = max_retries
        self.tasks: list[Task] = []
        # Codebuff-inspired extensions (all have safe defaults)
        self.allowed_tools: list[str] = allowed_tools if allowed_tools is not None else []
        self.spawnable_agents: list[str] = list(spawnable_agents) if spawnable_agents else []
        self.output_mode: str = output_mode
        self.step_hooks: dict[str, Any] = dict(step_hooks) if step_hooks else {}

    @abstractmethod
    def plan(self, input_data: str) -> list[Task]:
        """Parse input into executable tasks.

        Args:
            input_data: Raw input (string, dict, etc.)

        Returns:
            List of Task objects to execute
        """

    @abstractmethod
    def execute(self, task: Task) -> Result:
        """Execute a single task.

        Args:
            task: Task to execute

        Returns:
            Result with output or error
        """

    def verify(self, result: Result) -> bool:
        """Validate task result.

        Override for custom validation logic.

        Args:
            result: Result to validate

        Returns:
            True if valid, False to retry
        """
        return result.success

    async def _fire_hook(self, hook_name: str, **kwargs: Any) -> None:
        """Fire a step hook if registered. Non-blocking on errors.

        Args:
            hook_name: One of: on_step_start, on_step_end, on_tool_call, on_error.
            **kwargs: Hook payload data.
        """
        hook = self.step_hooks.get(hook_name)
        if hook is None:
            return
        try:
            import inspect
            if inspect.iscoroutinefunction(hook):
                await hook(**kwargs)
            else:
                # Sync callback - call directly
                hook(**kwargs)
        except Exception:
            logger.debug("Step hook %r raised (non-fatal)", hook_name, exc_info=True)

    def run(self, input_data: str) -> list[Result]:
        """Main execution loop.

        Args:
            input_data: Input to process

        Returns:
            List of results from all tasks
        """
        results: list[Result] = []

        # Phase 1: Plan
        self.tasks = self.plan(input_data)

        # Phase 2-3: Execute & Verify
        for task in self.tasks:
            task.status = TaskStatus.RUNNING
            retries = 0
            result = Result(task_id=task.id, success=False, output=None, error="max_retries=0")

            while retries < self.max_retries:
                result = self.execute(task)

                if self.verify(result):
                    task.status = TaskStatus.SUCCESS
                    task.output = result.output
                    break
                retries += 1
                task.status = TaskStatus.RETRY

            if task.status != TaskStatus.SUCCESS:
                task.status = TaskStatus.FAILED
                task.error = result.error

            results.append(result)

        return results

    def __repr__(self) -> str:
        """Return a developer-friendly string representation of the agent."""
        return f"<Agent:{self.name} tasks={len(self.tasks)}>"


# Export
__all__ = ["AgentBase", "Result", "Task", "TaskStatus", "StepHooksDict"]
