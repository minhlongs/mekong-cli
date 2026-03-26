"""
Mission Dispatch — Routes QueueItems through LLMRouter + executor/agent_loop.

Wires the dispatch pipeline:
  QueueItem → Task → LLMRouter.route() → MissionExecutor.run_llm()
                                        OR run_agent_sync() (tool-use tasks)

Capabilities that trigger agent_loop (tool use):
  builder, reviewer, tester, researcher, debugger

All others use MissionExecutor.run_llm() directly.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .executor import MissionExecutor, MissionResult
from .llm_router import LLMRouter
from .task_router import Task

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
JOURNAL_FILE = MEKONG_ROOT / ".mekong" / "journal" / "missions.json"

# Capabilities that require tool use via agent_loop
AGENT_CAPABILITIES = {"builder", "reviewer", "tester", "researcher", "debugger"}

# Module-level singletons (lazy init)
_router: LLMRouter | None = None
_executor: MissionExecutor | None = None


def _get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router


def _get_executor() -> MissionExecutor:
    global _executor
    if _executor is None:
        _executor = MissionExecutor(working_dir=str(MEKONG_ROOT))
    return _executor


def _queue_item_to_task(item: Any) -> Task:
    """Convert a QueueItem to a Task for LLMRouter.route()."""
    priority_map = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    # Infer capability from description heuristics if not set
    desc_lower = item.description.lower()
    capability = "general"
    for cap in AGENT_CAPABILITIES:
        if cap in desc_lower:
            capability = cap
            break

    return Task(
        task_id=item.task_id,
        description=item.description,
        priority_value=priority_map.get(item.priority, 2),
        capability=capability,
    )


def _update_journal(task_id: str, updates: dict) -> None:
    """Patch a mission entry in the journal by task_id."""
    if not JOURNAL_FILE.exists():
        return
    try:
        data = json.loads(JOURNAL_FILE.read_text())
        missions = data.get("missions", [])
        for m in missions:
            if m.get("task_id") == task_id:
                m.update(updates)
                break
        JOURNAL_FILE.write_text(json.dumps({"missions": missions}, indent=2))
    except (json.JSONDecodeError, OSError):
        logger.warning(f"[Dispatch] Failed to update journal for {task_id}")


def dispatch_task(item: Any) -> MissionResult:
    """
    Dispatch a single QueueItem through the LLM pipeline.

    Flow:
      1. Convert QueueItem → Task
      2. LLMRouter.route(task) → ModelConfig
      3. If capability needs tool use → agent_loop.run_agent_sync()
         else → MissionExecutor.run_llm(prompt, model_config)
      4. Update journal with result
      5. Return MissionResult

    Args:
        item: QueueItem from get_dispatch_queue()

    Returns:
        MissionResult with success/output/error/duration
    """
    router = _get_router()
    executor = _get_executor()
    task = _queue_item_to_task(item)

    # Mark active in journal
    _update_journal(item.task_id, {
        "status": "active",
        "started_at": datetime.now().isoformat(),
    })

    model_config = router.route(task)

    # Tool-use path via agent_loop
    if task.capability in AGENT_CAPABILITIES:
        try:
            from .agent_loop import run_agent_sync
            # Map capability to tier: coding-capable → deep, else fast
            tier = "deep" if task.capability in {"builder", "reviewer"} else "fast"
            output = run_agent_sync(item.description, model_tier=tier)
            result = MissionResult(success=True, output=output, exit_code=0)
            router.record_success(model_config)
        except Exception as exc:
            result = MissionResult(success=False, error=str(exc))
            router.record_failure(model_config)
    else:
        # Direct LLM path via executor
        result = executor.run_llm(item.description, model_config)
        if result.success:
            router.record_success(model_config)
        else:
            router.record_failure(model_config)

    # Update journal with outcome
    _update_journal(item.task_id, {
        "status": "success" if result.success else "failed",
        "completed_at": datetime.now().isoformat(),
        "duration_ms": int(result.duration * 1000),
        "output": result.output[:500] if result.output else "",
        "error": result.error[:300] if result.error else "",
    })

    logger.info(
        f"[Dispatch] {item.task_id} ({task.capability}) "
        f"→ {'OK' if result.success else 'FAIL'} in {result.duration:.1f}s"
    )
    return result


def dispatch_next() -> MissionResult | None:
    """
    Dequeue and dispatch the highest-priority pending task.

    Returns:
        MissionResult if a task was dispatched, None if queue empty.
    """
    # Import here to avoid circular at module level
    from .mission_control import get_dispatch_queue

    queue = get_dispatch_queue()
    # get_dispatch_queue() already returns sorted by priority; pick first pending
    pending = [item for item in queue if item.status == "pending"]
    if not pending:
        logger.debug("[Dispatch] No pending tasks in queue")
        return None

    item = pending[0]
    logger.info(f"[Dispatch] dispatch_next → {item.task_id} [{item.priority}] {item.description[:60]}")
    return dispatch_task(item)


__all__ = ["dispatch_task", "dispatch_next"]
