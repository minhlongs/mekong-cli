# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Agent Base Module."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import inspect
import logging
from typing import Any, Coroutine, Union
import warnings as _warnings

logger = logging.getLogger(__name__)

StepHook = Coroutine[Any, Any, None]
StepHooksDict = dict[str, StepHook]


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class Task:
    id: str
    description: str
    input: dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    output: Union[str, dict, list, None] = None
    error: Union[str, None] = None


@dataclass
class Result:
    task_id: str
    success: bool
    output: Union[str, dict, list, None] = None
    error: Union[str, None] = None


class AgentBase(ABC):
    """Base class for all Mekong CLI agents (Plan-Execute-Verify)."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        abstract_methods: frozenset = getattr(cls, "__abstractmethods__", frozenset())
        unimplemented = [m for m in ("plan", "execute") if m in abstract_methods]
        if unimplemented and getattr(cls, "__abstractmethods__", None) != frozenset(unimplemented):
            _warnings.warn(
                f"{cls.__name__} does not implement: {unimplemented}. Calls to these methods will raise NotImplementedError.",
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
        self.name = name
        self.max_retries = max_retries
        self.tasks: list[Task] = []
        self.allowed_tools: list[str] = allowed_tools if allowed_tools is not None else []
        self.spawnable_agents: list[str] = list(spawnable_agents) if spawnable_agents else []
        self.output_mode: str = output_mode
        self.step_hooks: dict[str, Any] = dict(step_hooks) if step_hooks else {}

    @abstractmethod
    def plan(self, input_data: str) -> list[Task]:
        """Parse input into executable tasks."""

    @abstractmethod
    def execute(self, task: Task) -> Result:
        """Execute a single task."""

    def verify(self, result: Result) -> bool:
        """Validate task result."""
        return result.success

    async def _fire_hook(self, hook_name: str, **kwargs: Any) -> None:
        hook = self.step_hooks.get(hook_name)
        if hook is None:
            return
        try:
            if inspect.iscoroutinefunction(hook):
                await hook(**kwargs)
            else:
                hook(**kwargs)
        except Exception:
            logger.debug("Step hook %r raised (non-fatal)", hook_name, exc_info=True)

    def run(self, input_data: str) -> list[Result]:
        """Main execution loop."""
        results: list[Result] = []
        self.tasks = self.plan(input_data)

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
        return f"<Agent:{self.name} tasks={len(self.tasks)}>"


__all__ = ["AgentBase", "Result", "Task", "TaskStatus", "StepHooksDict"]
