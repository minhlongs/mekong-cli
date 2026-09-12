# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Coverage tests for plan_constraints, progress_tracker, graceful_shutdown,
and memory_separation modules.

Iteration 21 of the progressive coverage loop.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# ── plan_constraints ────────────────────────────────────────────────────
from src.core.plan_constraints import (
    ConstraintEngine,
    ConstraintViolation,
    MutualExclusion,
    OrderingConstraint,
    PlanConstraints,
    ResourceLimit,
    TimeBound,
)

# ── progress_tracker ────────────────────────────────────────────────────
from src.core.progress_tracker import (
    ProgressPhase,
    ProgressSnapshot,
    ProgressTracker,
    StepProgress,
)

# ── graceful_shutdown ───────────────────────────────────────────────────
from src.core.graceful_shutdown import (
    GracefulShutdownHandler,
    ShutdownContext,
    ShutdownReason,
    get_shutdown_handler,
    register_shutdown_cleanup,
    reset_shutdown_handler,
    shutdown_on_all_phases_operational,
)

# ── memory_separation ───────────────────────────────────────────────────
from src.core.memory_separation import (
    MemorySeparation,
    MemoryTier,
    _TIER_TTL,
)


# =========================================================================
# Helpers for Recipe mocking
# =========================================================================
@dataclass
class DummyRecipeStep:
    order: int
    title: str
    dependencies: list[int] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class DummyRecipe:
    name: str = "test-recipe"
    description: str = "A test recipe"
    steps: list[DummyRecipeStep] = field(default_factory=list)


# =========================================================================
# plan_constraints.py — 119 statements
# =========================================================================
class TestPlanConstraints:
    def test_constraint_violation_dataclass(self) -> None:
        cv = ConstraintViolation(step_order=1, constraint_name="test", message="bad")
        assert cv.step_order == 1
        assert cv.constraint_name == "test"
        assert cv.message == "bad"

    def test_resource_limit_max_total_steps(self) -> None:
        engine = ConstraintEngine()
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="step1"),
                DummyRecipeStep(order=2, title="step2"),
                DummyRecipeStep(order=3, title="step3"),
            ]
        )
        constraints = PlanConstraints(
            resource_limit=ResourceLimit(max_total_steps=2)
        )
        violations = engine.validate(recipe, constraints)
        assert len(violations) == 1
        assert violations[0].constraint_name == "ResourceLimit.max_total_steps"
        assert "exceeds limit of 2" in violations[0].message

    def test_resource_limit_max_concurrent_steps(self) -> None:
        engine = ConstraintEngine()
        # 3 independent steps in parallel -> width = 3
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="step1"),
                DummyRecipeStep(order=2, title="step2"),
                DummyRecipeStep(order=3, title="step3"),
            ]
        )
        constraints = PlanConstraints(
            resource_limit=ResourceLimit(max_concurrent_steps=2)
        )
        violations = engine.validate(recipe, constraints)
        assert len(violations) == 1
        assert violations[0].constraint_name == "ResourceLimit.max_concurrent_steps"
        assert "up to 3 concurrent steps" in violations[0].message

    def test_resource_limit_compliant(self) -> None:
        engine = ConstraintEngine()
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="step1"),
                DummyRecipeStep(order=2, title="step2", dependencies=[1]),
            ]
        )
        constraints = PlanConstraints(
            resource_limit=ResourceLimit(max_total_steps=5, max_concurrent_steps=2)
        )
        violations = engine.validate(recipe, constraints)
        assert violations == []

    def test_ordering_constraint_missing_ancestor_violation(self) -> None:
        engine = ConstraintEngine()
        # "deploy" does NOT depend on "build"
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="Build artifact"),
                DummyRecipeStep(order=2, title="Deploy to staging", dependencies=[]),
            ]
        )
        constraints = PlanConstraints(
            ordering=[OrderingConstraint(before_step="Build", after_step="Deploy")]
        )
        violations = engine.validate(recipe, constraints)
        assert len(violations) == 1
        assert violations[0].step_order == 2
        assert violations[0].constraint_name == "OrderingConstraint"
        assert "must depend on a step matching 'Build'" in violations[0].message

    def test_ordering_constraint_satisfied(self) -> None:
        engine = ConstraintEngine()
        # "deploy" transitively depends on "build"
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="Build artifact"),
                DummyRecipeStep(order=2, title="Test artifact", dependencies=[1]),
                DummyRecipeStep(order=3, title="Deploy to prod", dependencies=[2]),
            ]
        )
        constraints = PlanConstraints(
            ordering=[OrderingConstraint(before_step="Build", after_step="Deploy")]
        )
        violations = engine.validate(recipe, constraints)
        assert violations == []

    def test_ordering_constraint_unmatched_steps_ignored(self) -> None:
        engine = ConstraintEngine()
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="Initialize DB"),
            ]
        )
        constraints = PlanConstraints(
            ordering=[OrderingConstraint(before_step="Compile", after_step="Package")]
        )
        violations = engine.validate(recipe, constraints)
        assert violations == []

    def test_mutual_exclusion_violation(self) -> None:
        engine = ConstraintEngine()
        # step 1 and step 2 both match and neither depends on the other
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="Flush Redis cache"),
                DummyRecipeStep(order=2, title="Migrate Redis database"),
            ]
        )
        constraints = PlanConstraints(
            mutual_exclusions=[MutualExclusion(step_titles=["redis"])]
        )
        violations = engine.validate(recipe, constraints)
        assert len(violations) == 1
        assert violations[0].constraint_name == "MutualExclusion"
        assert "may run concurrently but are mutually exclusive" in violations[0].message

    def test_mutual_exclusion_satisfied_by_dependency(self) -> None:
        engine = ConstraintEngine()
        # step 2 depends on step 1 -> serialized, not concurrent
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="Flush Redis cache"),
                DummyRecipeStep(order=2, title="Migrate Redis database", dependencies=[1]),
            ]
        )
        constraints = PlanConstraints(
            mutual_exclusions=[MutualExclusion(step_titles=["redis"])]
        )
        violations = engine.validate(recipe, constraints)
        assert violations == []

    def test_mutual_exclusion_under_two_matches(self) -> None:
        engine = ConstraintEngine()
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="Flush Redis cache"),
                DummyRecipeStep(order=2, title="Send Slack alert"),
            ]
        )
        constraints = PlanConstraints(
            mutual_exclusions=[MutualExclusion(step_titles=["redis"])]
        )
        violations = engine.validate(recipe, constraints)
        assert violations == []

    def test_time_bound_validation(self) -> None:
        engine = ConstraintEngine()
        recipe = DummyRecipe(steps=[DummyRecipeStep(order=1, title="step1")])

        # Non-positive values cause violations
        bad_bound = TimeBound(max_step_duration_s=0, max_total_duration_s=-5.0)
        violations = engine.validate(recipe, PlanConstraints(time_bound=bad_bound))
        assert len(violations) == 2
        names = {v.constraint_name for v in violations}
        assert "TimeBound.max_step_duration_s" in names
        assert "TimeBound.max_total_duration_s" in names

        # Positive values pass
        good_bound = TimeBound(max_step_duration_s=10.0, max_total_duration_s=60.0)
        assert engine.validate(recipe, PlanConstraints(time_bound=good_bound)) == []

    def test_dag_width_and_reachability_edge_cases(self) -> None:
        engine = ConstraintEngine()
        empty_recipe = DummyRecipe(steps=[])
        assert engine._dag_width(empty_recipe) == 0

        # Step referencing non-existent dependency in reachability
        recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="orphan", dependencies=[999]),
            ]
        )
        reach = engine._build_reachability(recipe)
        assert reach[1] == {999}

        # Multiple parents in DAG width calculation
        multi_parent_recipe = DummyRecipe(
            steps=[
                DummyRecipeStep(order=1, title="A"),
                DummyRecipeStep(order=2, title="B"),
                DummyRecipeStep(
                    order=3,
                    title="C",
                    params={"dependencies": [1, 2]},
                ),
            ]
        )
        assert engine._dag_width(multi_parent_recipe) == 2

    def test_type_checking_import(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import importlib
        import typing
        import src.core.plan_constraints as pc

        monkeypatch.setattr(typing, "TYPE_CHECKING", True)
        importlib.reload(pc)
        monkeypatch.setattr(typing, "TYPE_CHECKING", False)
        importlib.reload(pc)


# =========================================================================
# progress_tracker.py — 118 statements
# =========================================================================
class TestProgressTracker:
    def test_step_progress_duration_ms(self) -> None:
        step = StepProgress(step_order=1, title="test")
        assert step.duration_ms == 0.0

        step.start_time = 100.0
        step.end_time = 102.5
        assert step.duration_ms == 2500.0

        with patch("time.time", return_value=105.0):
            step.end_time = None
            assert step.duration_ms == 5000.0

    def test_progress_snapshot_remaining_steps(self) -> None:
        snap = ProgressSnapshot(
            phase=ProgressPhase.PLANNING,
            total_steps=10,
            completed_steps=3,
            failed_steps=2,
            current_step=4,
            percentage=50.0,
            elapsed_ms=123.4,
            eta_ms=None,
        )
        assert snap.remaining_steps == 5

    def test_tracker_lifecycle(self) -> None:
        tracker = ProgressTracker()
        events: list[ProgressSnapshot] = []

        # Exception in callback should be swallowed
        def faulty_cb(snap: ProgressSnapshot) -> None:
            raise RuntimeError("callback bug")

        def good_cb(snap: ProgressSnapshot) -> None:
            events.append(snap)

        tracker.register_callback(faulty_cb)
        tracker.register_callback(good_cb)

        # Start workflow
        tracker.start_workflow(total_steps=3)
        assert tracker._total_steps == 3
        assert tracker._phase == ProgressPhase.PLANNING
        assert len(events) == 1

        # Set phase
        tracker.set_phase(ProgressPhase.EXECUTING)
        assert tracker._phase == ProgressPhase.EXECUTING

        # Step 1 started and completed
        tracker.step_started(1, "Install packages")
        assert tracker._current_step == 1
        assert tracker._steps[1].status == "running"

        tracker.step_completed(1)
        assert tracker._steps[1].status == "passed"
        assert tracker._completed == 1
        assert tracker._current_step is None

        # Step 2 started and failed
        tracker.step_started(2, "Run migration")
        tracker.step_failed(2, error="Table locked")
        assert tracker._steps[2].status == "failed"
        assert tracker._steps[2].error == "Table locked"
        assert tracker._failed == 1

        # Step 3 skipped
        tracker.step_skipped(3, "Optional step")
        assert tracker._steps[3].status == "skipped"

        # Complete non-existent step orders safely
        tracker.step_completed(999)
        tracker.step_failed(998, error="no-op")

        # Finish workflow
        tracker.finish(success=True)
        assert tracker._phase == ProgressPhase.COMPLETE

        tracker.finish(success=False)
        assert tracker._phase == ProgressPhase.FAILED

    def test_percentage_elapsed_and_eta_calculations(self) -> None:
        tracker = ProgressTracker()

        # Before start: total_steps = 0, start_time = None
        assert tracker._percentage() == 0.0
        assert tracker._elapsed_ms() == 0.0
        assert tracker._estimate_eta(0.0) is None

        # Start with 4 steps
        with patch("time.time", side_effect=[100.0, 105.0]):
            tracker.start_workflow(total_steps=4)
            # done = 0 -> ETA is None
            assert tracker._estimate_eta(5000.0) is None

            tracker._completed = 2
            # 2 done out of 4, elapsed 10000ms -> avg 5000ms/step -> 2 remaining = 10000ms ETA
            eta = tracker._estimate_eta(10000.0)
            assert eta == 10000.0
            assert tracker._percentage() == 50.0

        # Snapshot structure
        snap = tracker.snapshot()
        assert snap.total_steps == 4
        assert snap.completed_steps == 2
        assert len(snap.steps) == 0


# =========================================================================
# graceful_shutdown.py — 118 statements
# =========================================================================
class TestGracefulShutdown:
    @pytest.fixture(autouse=True)
    def manage_atexit(self) -> Any:
        import atexit

        registered = []
        orig_reg = atexit.register

        def mock_register(func, *args, **kwargs):
            registered.append(func)
            return orig_reg(func, *args, **kwargs)

        with patch("atexit.register", side_effect=mock_register):
            yield

        for func in registered:
            try:
                atexit.unregister(func)
            except Exception:
                pass

    def test_shutdown_reason_enum(self) -> None:
        assert ShutdownReason.ALL_PHASES_OPERATIONAL == "all_phases_operational"
        assert ShutdownReason.USER_REQUESTED == "user_requested"
        assert ShutdownReason.ERROR == "error"

    def test_shutdown_context_dataclass(self) -> None:
        ctx = ShutdownContext(reason=ShutdownReason.MAINTENANCE)
        assert ctx.reason == ShutdownReason.MAINTENANCE
        assert ctx.cleanup_steps_completed == []
        assert ctx.errors == []

    @pytest.mark.asyncio
    async def test_initiate_shutdown_clean(self) -> None:
        handler = GracefulShutdownHandler()

        cleanup_called = False
        final_called = False

        async def cleanup_handler() -> bool:
            nonlocal cleanup_called
            cleanup_called = True
            return True

        async def final_callback() -> None:
            nonlocal final_called
            final_called = True

        handler.register_cleanup_handler(cleanup_handler, "db_cleanup")
        handler.register_final_callback(final_callback)

        code = await handler.initiate_shutdown(
            reason=ShutdownReason.ALL_PHASES_OPERATIONAL,
            details={"phases_status": {"p1": "operational", "p2": "operational"}},
        )
        assert code == 0
        assert cleanup_called is True
        assert final_called is True
        assert len(handler._shutdown_context.cleanup_steps_completed) == 1

        # Second shutdown invocation returns existing code
        code2 = await handler.initiate_shutdown()
        assert code2 == 0

    @pytest.mark.asyncio
    async def test_initiate_shutdown_with_errors(self) -> None:
        handler = GracefulShutdownHandler()

        async def failing_cleanup() -> bool:
            return False

        async def exploding_cleanup() -> bool:
            raise RuntimeError("boom")

        async def exploding_final() -> None:
            raise ValueError("final callback explosion")

        handler.register_cleanup_handler(failing_cleanup, "fail_step")
        handler.register_cleanup_handler(exploding_cleanup, "explode_step")
        handler.register_final_callback(exploding_final)

        code = await handler.initiate_shutdown(reason=ShutdownReason.ERROR)
        assert code == 1
        assert len(handler._shutdown_context.errors) == 2

    def test_on_exit_and_sync_cleanup(self) -> None:
        handler = GracefulShutdownHandler()
        # Not in progress -> triggers warning branch
        handler._on_exit()

        # In progress -> returns early
        handler._shutdown_in_progress = True
        handler._on_exit()

        handler.perform_sync_cleanup()

    def test_log_goodbye_empty_context(self) -> None:
        handler = GracefulShutdownHandler()
        handler._shutdown_context = None
        handler._log_goodbye()  # Should not raise

    def test_singleton_get_and_reset(self) -> None:
        reset_shutdown_handler()
        h1 = get_shutdown_handler()
        h2 = get_shutdown_handler()
        assert h1 is h2

        reset_shutdown_handler()
        h3 = get_shutdown_handler()
        assert h3 is not h1

    def test_register_shutdown_cleanup_helper(self) -> None:
        reset_shutdown_handler()

        async def dummy_clean() -> bool:
            return True

        register_shutdown_cleanup("dummy", dummy_clean)
        handler = get_shutdown_handler()
        assert len(handler._cleanup_handlers) == 1

    @pytest.mark.asyncio
    async def test_shutdown_on_all_phases_operational(self) -> None:
        reset_shutdown_handler()

        mock_detector = MagicMock()
        mock_info = MagicMock()
        mock_info.status.value = "operational"
        mock_detector.get_all_phases_status.return_value = {"phase1": mock_info}

        with patch("src.raas.phase_completion_detector.get_detector", return_value=mock_detector):
            with patch("glob.glob", return_value=["/tmp/mekong_1.txt", "/tmp/tom_hum_fail.txt"]):
                with patch("os.remove") as mock_remove:
                    mock_remove.side_effect = [None, OSError("permission denied")]
                    with patch("sys.exit") as mock_exit:
                        await shutdown_on_all_phases_operational()
                        mock_exit.assert_called_once_with(0)


# =========================================================================
# memory_separation.py — 95 statements
# =========================================================================
class TestMemorySeparation:
    def test_memory_tier_enum(self) -> None:
        assert MemoryTier.SESSION == "session"
        assert MemoryTier.PERSISTENT == "persistent"
        assert MemoryTier.ARCHIVE == "archive"
        assert _TIER_TTL[MemoryTier.SESSION] == 3600

    def test_parse_tier_from_key(self) -> None:
        # Valid key
        tier, key = MemorySeparation._parse_tier_from_key("tier::session::my_var")
        assert tier == MemoryTier.SESSION
        assert key == "my_var"

        # Non-prefixed key
        tier, key = MemorySeparation._parse_tier_from_key("unprefixed_key")
        assert tier is None
        assert key == "unprefixed_key"

        # Invalid tier enum value
        tier, key = MemorySeparation._parse_tier_from_key("tier::invalid_tier::key")
        assert tier is None
        assert key == "tier::invalid_tier::key"

        # Malformed format (no second delimiter)
        tier, key = MemorySeparation._parse_tier_from_key("tier::no_second_delim")
        assert tier is None
        assert key == "tier::no_second_delim"

    def test_store_and_store_raw(self) -> None:
        mock_store = MagicMock()
        mem = MemorySeparation(store=mock_store)

        # Default TTL
        mem.store("user_key", b"payload", tier=MemoryTier.PERSISTENT)
        mock_store.store.assert_called_once()
        entry = mock_store.store.call_args[0][0]
        assert entry.key == "tier::persistent::user_key"
        assert entry.value == b"payload"
        assert entry.ttl == _TIER_TTL[MemoryTier.PERSISTENT]

        # Explicit TTL
        mock_store.reset_mock()
        mem.store("user_key_2", b"payload2", tier=MemoryTier.SESSION, ttl=120)
        entry2 = mock_store.store.call_args[0][0]
        assert entry2.ttl == 120

        # store_raw
        mock_store.reset_mock()
        mem.store_raw("raw_key", b"raw_data", ttl=60)
        entry3 = mock_store.store.call_args[0][0]
        assert entry3.key == "raw_key"
        assert entry3.value == b"raw_data"
        assert entry3.ttl == 60

    def test_init_default_store(self) -> None:
        with patch("src.core.memory_scope.ScopedMemoryStore") as mock_scoped_cls:
            mem = MemorySeparation()
            assert mem._store is not None
            mock_scoped_cls.assert_called_once()

    def test_retrieve(self) -> None:
        mock_store = MagicMock()
        mem = MemorySeparation(store=mock_store)

        # Hit
        mock_entry = MagicMock(value=b"found_value")
        mock_store.retrieve.return_value = mock_entry
        assert mem.retrieve("user_key", tier=MemoryTier.PERSISTENT) == b"found_value"

        # Miss
        mock_store.retrieve.return_value = None
        assert mem.retrieve("missing_key") is None

    def test_delete(self) -> None:
        mock_store = MagicMock()
        mem = MemorySeparation(store=mock_store)

        e1 = MagicMock(key="tier::session::target")
        e2 = MagicMock(key="tier::persistent::other")
        mock_store.query.return_value = [e1, e2]
        mock_store.delete.return_value = True

        # Target found and deleted
        assert mem.delete("target") is True
        mock_store.delete.assert_called_once_with("tier::session::target", mem._mekong_scope())

        # Target not found
        assert mem.delete("nonexistent") is False

    def test_search(self) -> None:
        mock_store = MagicMock()
        mem = MemorySeparation(store=mock_store)

        e1 = MagicMock(
            key="tier::session::alpha_key",
            value=b"hello bytes world",
            created_at=100.0,
        )
        e2 = MagicMock(
            key="tier::persistent::beta_key",
            value="hello string world",
            created_at=105.0,
        )
        e3 = MagicMock(
            key="tier::persistent::unrelated",
            value=b"completely different",
            created_at=110.0,
        )
        e4 = MagicMock(
            key="raw_unprefixed_key",
            value=b"hello in raw key",
            created_at=115.0,
        )
        mock_store.query.return_value = [e1, e2, e3, e4]

        # Search matching key or bytes/string value
        res = mem.search("hello", limit=10)
        assert len(res) == 3
        keys = [r["key"] for r in res]
        assert "alpha_key" in keys
        assert "beta_key" in keys
        assert "raw_unprefixed_key" in keys

        # Search with tier filter
        res_session = mem.search("hello", tier=MemoryTier.SESSION)
        assert len(res_session) == 1
        assert res_session[0]["key"] == "alpha_key"

        # Search with limit reached
        res_limit = mem.search("hello", limit=1)
        assert len(res_limit) == 1

    def test_flush_session(self) -> None:
        mock_store = MagicMock()
        mem = MemorySeparation(store=mock_store)

        e1 = MagicMock(key="tier::session::k1")
        e2 = MagicMock(key="tier::persistent::k2")
        e3 = MagicMock(key="tier::session::k3")
        mock_store.query.return_value = [e1, e2, e3]

        deleted_count = mem.flush_session()
        assert deleted_count == 2
        assert mock_store.delete.call_count == 2

    def test_list_by_tier(self) -> None:
        mock_store = MagicMock()
        mem = MemorySeparation(store=mock_store)

        e1 = MagicMock(key="tier::persistent::k1")
        e2 = MagicMock(key="tier::session::k2")
        e3 = MagicMock(key="tier::persistent::k3")
        mock_store.query.return_value = [e1, e2, e3]

        keys = mem.list_by_tier(MemoryTier.PERSISTENT)
        assert keys == ["k1", "k3"]
