"""
AGI v2 components — reflection, world model, tool registry, collaboration, code evolution,
vector memory. All loaded lazily and silently skipped if unavailable.
"""

from typing import Any, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console


class AGIComponents:
    """
    Container and initializer for optional AGI v2 subsystems.
    Each component is loaded lazily and silently ignored on ImportError.
    """

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        self.reflection: Optional[Any] = None
        self.world_model: Optional[Any] = None
        self.tool_registry: Optional[Any] = None
        self.collaboration: Optional[Any] = None
        self.code_evolution: Optional[Any] = None
        self.vector_memory: Optional[Any] = None

        self._load(llm_client)

    def _load(self, llm_client: Optional[Any]) -> None:
        """Attempt to load each AGI subsystem; ignore failures."""
        try:
            from ..reflection import ReflectionEngine
            self.reflection = ReflectionEngine(llm_client=llm_client)
        except Exception:
            pass

        try:
            from ..world_model import WorldModel
            self.world_model = WorldModel(llm_client=llm_client)
        except Exception:
            pass

        try:
            from ..tool_registry import ToolRegistry
            self.tool_registry = ToolRegistry()
        except Exception:
            pass

        try:
            from ..collaboration import CollaborationProtocol
            self.collaboration = CollaborationProtocol(llm_client=llm_client)
        except Exception:
            pass

        try:
            from ..code_evolution import CodeEvolutionEngine
            self.code_evolution = CodeEvolutionEngine(llm_client=llm_client)
        except Exception:
            pass

        try:
            from ..vector_memory_store import VectorMemoryStore
            self.vector_memory = VectorMemoryStore()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Pre-execution hints (called by runner before workflow starts)
    # ------------------------------------------------------------------

    def print_pre_execution_hints(self, goal: str, console: "Console") -> Any:
        """Print AGI hints to console; return world snapshot (may be None)."""
        world_before = None

        if self.world_model:
            try:
                world_before = self.world_model.snapshot()
                console.print("[dim]🌍 World snapshot captured[/dim]")
            except Exception:
                pass

        if self.reflection:
            try:
                hint = self.reflection.get_strategy_suggestion(goal)
                if hint:
                    console.print(f"[dim]🪞 Strategy hint: {hint[:60]}[/dim]")
            except Exception:
                pass

        if self.tool_registry:
            try:
                suggested = self.tool_registry.suggest_tool(goal)
                if suggested:
                    console.print(
                        f"[dim]🔧 Tool available: {suggested.name} — "
                        f"{suggested.description[:40]}[/dim]"
                    )
            except Exception:
                pass

        if self.world_model:
            try:
                prediction = self.world_model.predict_side_effects(goal)
                if prediction.risk_level == "high":
                    console.print(
                        f"[bold yellow]⚠️  High-risk action detected: "
                        f"{'; '.join(prediction.warnings[:2])}[/bold yellow]"
                    )
            except Exception:
                pass

        if self.vector_memory:
            try:
                from ..vector_memory_store import VectorMemoryStore
                vec = VectorMemoryStore.text_to_hash_vector(goal)
                results = self.vector_memory.search("goal_history", vec, top_k=1)
                if results and results[0].get("score", 0) > 0.85:
                    prev = results[0].get("payload", {}).get("goal", "")
                    console.print(
                        f"[dim]🧠 Similar past goal: {prev[:50]} "
                        f"({results[0]['score']:.0%} match)[/dim]"
                    )
            except Exception:
                pass

        if self.collaboration:
            try:
                roles = self.collaboration.assign_roles(goal)
                if roles:
                    assigned = [f"{r['agent']}: {r['role']}" for r in roles[:2]]
                    console.print(f"[dim]🤝 Agents assigned: {', '.join(assigned)}[/dim]")
            except Exception:
                pass

        return world_before

    # ------------------------------------------------------------------
    # Post-execution pipeline (reflection, world diff, evolution, memory)
    # ------------------------------------------------------------------

    def run_post_execution(
        self,
        goal: str,
        status: str,
        duration_ms: float,
        world_before: Optional[Any],
        errors: List[str],
        console: "Console",
    ) -> None:
        """Run full post-execution AGI pipeline."""
        if self.reflection:
            try:
                reflection = self.reflection.reflect(
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

        if self.world_model and world_before:
            try:
                world_after = self.world_model.snapshot()
                world_diff = self.world_model.diff(world_before, world_after)
                diff_summary = world_diff.summary()
                if diff_summary and diff_summary != "No changes detected":
                    console.print(
                        f"\n[dim]🌍 World changes: {diff_summary[:100]}[/dim]"
                    )
            except Exception:
                pass

        if self.code_evolution:
            try:
                _journal = self.code_evolution.get_journal(limit=1)
                stats = self.code_evolution.get_stats()
                if stats.get("total_attempts", 0) > 0:
                    console.print(
                        f"[dim]🧬 Evolution: {stats['total_attempts']} attempts, "
                        f"{stats.get('success_rate', 0):.0%} success rate[/dim]"
                    )
            except Exception:
                pass

        if self.vector_memory:
            try:
                import hashlib
                from ..vector_memory_store import VectorMemoryStore
                vec = VectorMemoryStore.text_to_hash_vector(goal)
                goal_id = hashlib.md5(goal.encode()).hexdigest()[:12]
                self.vector_memory.get_or_create_collection("goal_history")
                self.vector_memory.upsert(
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

        if self.collaboration:
            try:
                self.collaboration.submit_review(
                    reviewer="orchestrator",
                    target=goal[:30],
                    approved=status == "success",
                    feedback=[errors[0]] if errors else ["Completed successfully"],
                )
            except Exception:
                pass


__all__ = ["AGIComponents"]
