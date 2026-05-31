"""Agent layer — registry, classifier, queue, dispatcher."""

from .base import AgentBase, Task, Result
from .registry import AgentRegistry
from .classifier import classify_task, TaskProfile
from .queue import PriorityTaskQueue, QueuedTask, TaskPriority
from .dispatcher import (
    build_message_chain,
    load_agent_prompt,
    inject_codebase_context,
    inject_metrics_context,
)

__all__ = [
    "AgentBase", "Task", "Result",
    "AgentRegistry",
    "classify_task", "TaskProfile",
    "PriorityTaskQueue", "QueuedTask", "TaskPriority",
    "build_message_chain",
    "load_agent_prompt",
    "inject_codebase_context",
    "inject_metrics_context",
]
