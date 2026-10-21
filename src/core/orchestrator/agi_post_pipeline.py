# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Post-execution pipeline routines for AGI v2 subsystems."""

from __future__ import annotations

import hashlib
from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


def execute_agi_post_pipeline(
    components: Any,
    goal: str,
    status: str,
    duration_ms: float,
    world_before: Optional[Any],
    errors: List[str],
    console: "Console",
) -> None:
    """Run full post-execution AGI pipeline."""
    if components.reflection:
        try:
            reflection = components.reflection.reflect(
                goal=goal,
                status=status,
                duration_ms=duration_ms,
                error=errors[0] if errors else "",
            )
            if reflection.lesson_learned:
                console.print(
                    f"\n[dim]🪞 Reflection: {reflection.lesson_learned[:80]}[/dim]"
                )
            if reflection.strategy_change:
                console.print(
                    f"[dim]🪞 Strategy change: {reflection.strategy_change[:60]}[/dim]"
                )
        except Exception:
            pass

    if components.world_model and world_before:
        try:
            world_after = components.world_model.snapshot()
            world_diff = components.world_model.diff(world_before, world_after)
            diff_summary = world_diff.summary()
            if diff_summary and diff_summary != "No changes detected":
                console.print(
                    f"\n[dim]🌍 World changes: {diff_summary[:100]}[/dim]"
                )
        except Exception:
            pass

    if components.code_evolution:
        try:
            _journal = components.code_evolution.get_journal(limit=1)
            stats = components.code_evolution.get_stats()
            if stats.get("total_attempts", 0) > 0:
                console.print(
                    f"[dim]🧬 Evolution: {stats['total_attempts']} attempts, "
                    f"{stats.get('success_rate', 0):.0%} success rate[/dim]"
                )
        except Exception:
            pass

    if components.vector_memory:
        try:
            from ..vector_memory_store import VectorMemoryStore
            vec = VectorMemoryStore.text_to_hash_vector(goal)
            goal_id = hashlib.md5(goal.encode()).hexdigest()[:12]
            components.vector_memory.get_or_create_collection("goal_history")
            components.vector_memory.upsert(
                collection="goal_history",
                id=goal_id,
                vector=vec,
                payload={
                    "goal": goal,
                    "status": status,
                    "duration_ms": duration_ms,
                    "errors": errors[:3] if errors else [],
                },
            )
        except Exception:
            pass

    if components.collaboration:
        try:
            components.collaboration.submit_review(
                reviewer="orchestrator",
                target=goal[:30],
                approved=status == "success",
                feedback=[errors[0]] if errors else ["Completed successfully"],
            )
        except Exception:
            pass


__all__ = ["execute_agi_post_pipeline"]
