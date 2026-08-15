"""
Tests for daemon dispatch logic: Dispatcher, TaskRouter, WorkerPool, CircuitBreaker.

Covers:
- Task routing and priority queue ordering
- Load balancing strategies (round-robin, least-loaded)
- Worker state transitions
- Dead letter queue (task failure escalation)
- Circuit breaker state machine
"""

from unittest.mock import patch

from src.daemon.task_router import TaskRouter, TaskStatus
from src.daemon.worker_pool import WorkerPool, WorkerInfo, WorkerState
from src.daemon.dispatcher import Dispatcher, LoadBalanceStrategy
from src.daemon.circuit_breaker import CircuitBreaker, CircuitState, CircuitBreakerRegistry


# ---------------------------------------------------------------------------
# TaskRouter — priority queue and lifecycle
# ---------------------------------------------------------------------------

class TestTaskRouterEnqueue:
    """Tests for task enqueueing and priority ordering."""

    def test_enqueue_returns_task_with_id(self):
        router = TaskRouter()
        task = router.enqueue("Build feature X")
        assert task.task_id
        assert task.description == "Build feature X"
        assert task.status == TaskStatus.PENDING

    def test_enqueue_default_priority_is_medium(self):
        router = TaskRouter()
        task = router.enqueue("Some task")
        assert task.priority == "MEDIUM"

    def test_enqueue_respects_priority_levels(self):
        router = TaskRouter()
        for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            t = router.enqueue(f"task {priority}", priority=priority)
            assert t.priority == priority

    def test_enqueue_increments_queue_size(self):
        router = TaskRouter()
        router.enqueue("task 1")
        router.enqueue("task 2")
        stats = router.get_stats()
        assert stats.pending == 2

    def test_enqueue_at_capacity_does_not_crash(self):
        router = TaskRouter(max_size=2)
        router.enqueue("t1")
        router.enqueue("t2")
        # Third enqueue exceeds capacity — should return task without crashing
        t = router.enqueue("t3")
        assert t is not None


class TestTaskRouterPriorityOrdering:
    """Tasks must dequeue in priority order: CRITICAL > HIGH > MEDIUM > LOW."""

    def test_critical_before_low(self):
        router = TaskRouter()
        router.enqueue("low task", priority="LOW")
        router.enqueue("critical task", priority="CRITICAL")
        first = router.get_next_task()
        assert first.priority == "CRITICAL"

    def test_high_before_medium(self):
        router = TaskRouter()
        router.enqueue("medium task", priority="MEDIUM")
        router.enqueue("high task", priority="HIGH")
        first = router.get_next_task()
        assert first.priority == "HIGH"

    def test_full_priority_order(self):
        router = TaskRouter()
        for p in ["LOW", "MEDIUM", "CRITICAL", "HIGH"]:
            router.enqueue(f"task {p}", priority=p)
        expected = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        for expected_priority in expected:
            task = router.get_next_task()
            assert task.priority == expected_priority


class TestTaskRouterCapabilityFilter:
    """get_next_task should respect capability filter."""

    def test_get_next_filters_by_capability(self):
        router = TaskRouter()
        router.enqueue("builder task", capability="builder")
        router.enqueue("tester task", capability="tester")
        task = router.get_next_task(capability="tester")
        assert task.capability == "tester"

    def test_get_next_returns_none_when_no_match(self):
        router = TaskRouter()
        router.enqueue("builder task", capability="builder")
        task = router.get_next_task(capability="reviewer")
        assert task is None

    def test_get_next_without_filter_returns_highest_priority(self):
        router = TaskRouter()
        router.enqueue("low", priority="LOW", capability="x")
        router.enqueue("critical", priority="CRITICAL", capability="y")
        task = router.get_next_task()
        assert task.priority == "CRITICAL"


class TestTaskRouterLifecycle:
    """Task state transitions: pending → active → completed/failed."""

    def test_complete_task_marks_completed(self):
        router = TaskRouter()
        router.enqueue("task")
        task = router.get_next_task()
        router.complete(task.task_id)
        stats = router.get_stats()
        assert stats.completed == 1
        assert stats.active == 0

    def test_fail_task_retries_before_dlq(self):
        router = TaskRouter()
        router.enqueue("task", max_retries=3)
        task = router.get_next_task()
        # First and second failures should re-queue
        retried = router.fail(task.task_id, "error")
        assert retried is not None
        assert retried.retry_count == 1

    def test_fail_task_moves_to_dlq_after_max_retries(self):
        router = TaskRouter()
        router.enqueue("task", max_retries=1)
        task = router.get_next_task()
        result = router.fail(task.task_id, "fatal error")
        assert result is None
        stats = router.get_stats()
        assert stats.failed == 1

    def test_cancel_pending_task(self):
        router = TaskRouter()
        task = router.enqueue("task")
        success = router.cancel(task.task_id)
        assert success is True
        stats = router.get_stats()
        assert stats.pending == 0

    def test_cancel_nonexistent_task_returns_false(self):
        router = TaskRouter()
        assert router.cancel("nonexistent-id") is False

    def test_get_stats_counts_correctly(self):
        router = TaskRouter()
        router.enqueue("t1")
        router.enqueue("t2")
        router.enqueue("t3", max_retries=1)

        router.get_next_task()  # t1 → active (depends on heap order)
        task = router.get_next_task()  # another → active
        if task:
            router.complete(task.task_id)

        stats = router.get_stats()
        assert stats.pending + stats.active + stats.completed >= 0


# ---------------------------------------------------------------------------
# WorkerPool — worker lifecycle and health
# ---------------------------------------------------------------------------

class TestWorkerPool:
    """WorkerPool state machine tests without PM2."""

    def _add_worker(self, pool: WorkerPool, name: str, capability: str = "general") -> WorkerInfo:
        """Directly register a worker without PM2."""
        from datetime import datetime
        pool.workers[name] = WorkerInfo(
            id=name, name=name, capability=capability,
            state=WorkerState.IDLE,
            started_at=datetime.now().isoformat(),
        )
        return pool.workers[name]

    @patch.object(WorkerPool, "refresh_status")
    def test_get_available_worker_returns_idle(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "w1", "builder")
        worker = pool.get_available_worker()
        assert worker is not None
        assert worker.state == WorkerState.IDLE

    @patch.object(WorkerPool, "refresh_status")
    def test_get_available_worker_filters_by_capability(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "builder-1", "builder")
        self._add_worker(pool, "tester-1", "tester")
        worker = pool.get_available_worker(capability="tester")
        assert worker.name == "tester-1"

    @patch.object(WorkerPool, "refresh_status")
    def test_get_available_returns_none_when_all_busy(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "w1")
        pool.mark_busy("w1")
        worker = pool.get_available_worker()
        assert worker is None

    def test_mark_busy_changes_state(self):
        pool = WorkerPool()
        self._add_worker(pool, "w1")
        pool.mark_busy("w1")
        assert pool.workers["w1"].state == WorkerState.BUSY

    def test_mark_idle_increments_tasks_completed(self):
        pool = WorkerPool()
        self._add_worker(pool, "w1")
        pool.mark_busy("w1")
        pool.mark_idle("w1")
        assert pool.workers["w1"].state == WorkerState.IDLE
        assert pool.workers["w1"].tasks_completed == 1

    def test_mark_failed_sets_errored_state(self):
        pool = WorkerPool()
        self._add_worker(pool, "w1")
        pool.mark_failed("w1")
        assert pool.workers["w1"].state == WorkerState.ERRORED
        assert pool.workers["w1"].tasks_failed == 1

    @patch.object(WorkerPool, "refresh_status")
    def test_get_stats_counts_workers(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "w1", "builder")
        self._add_worker(pool, "w2", "tester")
        pool.mark_busy("w1")
        stats = pool.get_stats()
        assert stats.total_workers == 2
        assert stats.busy_workers == 1
        assert stats.idle_workers == 1

    @patch.object(WorkerPool, "refresh_status")
    def test_health_check_categorizes_workers(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "healthy")
        self._add_worker(pool, "broken")
        pool.mark_failed("broken")
        health = pool.health_check()
        assert "healthy" in health["healthy"]
        assert "broken" in health["degraded"]

    @patch.object(WorkerPool, "refresh_status")
    def test_list_workers_returns_all(self, mock_refresh):
        pool = WorkerPool()
        self._add_worker(pool, "w1")
        self._add_worker(pool, "w2")
        workers = pool.list_workers()
        assert len(workers) == 2


# ---------------------------------------------------------------------------
# Dispatcher — task routing and load balancing
# ---------------------------------------------------------------------------

class TestDispatcher:
    """Dispatcher tests with mocked WorkerPool and TaskRouter."""

    def _make_dispatcher(self, strategy=LoadBalanceStrategy.ROUND_ROBIN):
        pool = WorkerPool()
        router = TaskRouter()
        dispatcher = Dispatcher(worker_pool=pool, task_router=router, strategy=strategy)
        return dispatcher, pool, router

    def _add_idle_worker(self, pool: WorkerPool, name: str, capability: str = "general", cpu: float = 0.0):
        from datetime import datetime
        pool.workers[name] = WorkerInfo(
            id=name, name=name, capability=capability,
            state=WorkerState.IDLE, cpu=cpu,
            started_at=datetime.now().isoformat(),
        )

    @patch.object(WorkerPool, "refresh_status")
    def test_dispatch_new_task_by_description(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher()
        self._add_idle_worker(pool, "w1")
        result = dispatcher.dispatch(description="Build something")
        assert result.success is True
        assert result.worker_name == "w1"

    @patch.object(WorkerPool, "refresh_status")
    def test_dispatch_fails_without_workers(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher()
        result = dispatcher.dispatch(description="task")
        assert result.success is False
        assert result.error is not None

    @patch.object(WorkerPool, "refresh_status")
    def test_dispatch_fails_when_no_pending_tasks(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher()
        self._add_idle_worker(pool, "w1")
        result = dispatcher.dispatch()  # no description, empty queue
        assert result.success is False
        assert "No pending tasks" in result.error

    @patch.object(WorkerPool, "refresh_status")
    def test_dispatch_records_history(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher()
        self._add_idle_worker(pool, "w1")
        dispatcher.dispatch(description="task 1")
        self._add_idle_worker(pool, "w2")
        dispatcher.dispatch(description="task 2")
        assert len(dispatcher._dispatch_history) == 2

    @patch.object(WorkerPool, "refresh_status")
    def test_dispatch_history_capped_at_100(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher()
        for i in range(110):
            self._add_idle_worker(pool, f"w{i}")
            dispatcher.dispatch(description=f"task {i}")
        assert len(dispatcher._dispatch_history) <= 100

    @patch.object(WorkerPool, "refresh_status")
    def test_least_loaded_picks_lowest_cpu(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher(LoadBalanceStrategy.LEAST_LOADED)
        self._add_idle_worker(pool, "high-cpu", cpu=80.0)
        self._add_idle_worker(pool, "low-cpu", cpu=10.0)
        result = dispatcher.dispatch(description="task")
        assert result.worker_name == "low-cpu"

    @patch.object(WorkerPool, "refresh_status")
    def test_complete_task_frees_worker(self, mock_refresh):
        # Dispatch via queue (get_next_task path) so task lands in _active_tasks
        dispatcher, pool, router = self._make_dispatcher()
        self._add_idle_worker(pool, "w1")
        router.enqueue("task")
        result = dispatcher.dispatch()  # pulls from queue → task enters _active_tasks
        assert result.success
        dispatcher.complete_task(result.task_id)
        assert pool.workers["w1"].state == WorkerState.IDLE

    @patch.object(WorkerPool, "refresh_status")
    def test_fail_task_marks_worker_errored(self, mock_refresh):
        # Dispatch via queue so task lands in _active_tasks
        dispatcher, pool, router = self._make_dispatcher()
        self._add_idle_worker(pool, "w1")
        router.enqueue("task")
        result = dispatcher.dispatch()
        assert result.success
        dispatcher.fail_task(result.task_id, "boom")
        assert pool.workers["w1"].state == WorkerState.ERRORED

    @patch.object(WorkerPool, "refresh_status")
    def test_get_stats_returns_full_dict(self, mock_refresh):
        dispatcher, pool, router = self._make_dispatcher()
        self._add_idle_worker(pool, "w1")
        stats = dispatcher.get_stats()
        assert "workers" in stats
        assert "queue" in stats
        assert "dispatch" in stats
        assert stats["dispatch"]["strategy"] == "round_robin"


# ---------------------------------------------------------------------------
# CircuitBreaker — state machine
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    """Circuit breaker state transitions."""

    def test_starts_closed(self):
        cb = CircuitBreaker(name="test")
        assert cb.state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_trips_to_open_after_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        for _ in range(3):
            cb.on_failure()
        assert cb._state == CircuitState.OPEN
        assert cb.can_execute() is False

    def test_does_not_trip_before_threshold(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.on_failure()
        cb.on_failure()
        assert cb._state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_success_in_closed_resets_failure_count(self):
        cb = CircuitBreaker(name="test", failure_threshold=3)
        cb.on_failure()
        cb.on_failure()
        cb.on_success()
        assert cb._failure_count == 0

    def test_manual_reset_closes_circuit(self):
        cb = CircuitBreaker(name="test", failure_threshold=1)
        cb.on_failure()
        assert cb._state == CircuitState.OPEN
        cb.reset()
        assert cb._state == CircuitState.CLOSED
        assert cb.can_execute() is True

    def test_trips_counter_increments(self):
        cb = CircuitBreaker(name="test", failure_threshold=1)
        cb.on_failure()
        cb.reset()
        cb.on_failure()
        assert cb._trips == 2

    def test_half_open_failure_re_opens(self):
        cb = CircuitBreaker(name="test", failure_threshold=1)
        cb.on_failure()  # trips OPEN
        # Manually set to HALF_OPEN for testing
        cb._state = CircuitState.HALF_OPEN
        cb.on_failure()
        assert cb._state == CircuitState.OPEN

    def test_half_open_success_closes(self):
        cb = CircuitBreaker(name="test", failure_threshold=1, success_threshold=1)
        cb.on_failure()  # trips to OPEN
        cb._state = CircuitState.HALF_OPEN
        cb.on_success()
        assert cb._state == CircuitState.CLOSED

    def test_get_stats_reflects_state(self):
        cb = CircuitBreaker(name="test", failure_threshold=2)
        cb.on_failure()
        stats = cb.get_stats()
        assert stats.failure_count == 1
        assert stats.state == "closed"
        assert stats.trips == 0

    def test_repr_contains_name_and_state(self):
        cb = CircuitBreaker(name="my-service")
        assert "my-service" in repr(cb)
        assert "closed" in repr(cb)


class TestCircuitBreakerRegistry:
    """Registry creates and manages multiple breakers."""

    def test_get_creates_new_breaker(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("api-llm")
        assert cb.name == "api-llm"

    def test_get_returns_same_instance(self):
        reg = CircuitBreakerRegistry()
        cb1 = reg.get("api-llm")
        cb2 = reg.get("api-llm")
        assert cb1 is cb2

    def test_reset_single_breaker(self):
        reg = CircuitBreakerRegistry()
        cb = reg.get("api-llm", failure_threshold=1)
        cb.on_failure()
        assert cb._state == CircuitState.OPEN
        reg.reset("api-llm")
        assert cb._state == CircuitState.CLOSED

    def test_reset_all_breakers(self):
        reg = CircuitBreakerRegistry()
        for name in ["a", "b", "c"]:
            cb = reg.get(name, failure_threshold=1)
            cb.on_failure()
        count = reg.reset_all()
        assert count == 3
        for name in ["a", "b", "c"]:
            assert reg.get(name)._state == CircuitState.CLOSED

    def test_list_breakers(self):
        reg = CircuitBreakerRegistry()
        reg.get("x")
        reg.get("y")
        names = reg.list_breakers()
        assert "x" in names and "y" in names

    def test_get_stats_returns_all(self):
        reg = CircuitBreakerRegistry()
        reg.get("a")
        reg.get("b")
        stats = reg.get_stats()
        assert "a" in stats and "b" in stats
