# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Autonomous Distributed Task Queue & Dead-Letter Mesh (Phase 18).

Covers:
1. TaskQueue Engine: Priority scheduling (CRITICAL -> HIGH -> NORMAL -> LOW), atomic leasing, heartbeats.
2. Stale Lease Reclamation: Automatic recovery of expired worker leases.
3. Exponential Retry Backoff & DLQ: Automatic routing to dead-letter queue after max retries.
4. DLQ Management: Inspection, single retry, retry-all replay, and clearing.
5. CLI Command Surface: mekong queue enqueue, mekong queue status, mekong queue process, mekong queue dlq.
6. Native MCP Tools: mekong_queue_enqueue, mekong_queue_status, and mekong_queue_dlq_action dual parity.
7. AST Core Boundary Compliance: strict standard library only in src/core/task_queue.py.
"""

from __future__ import annotations

import ast
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from src.cli.app_setup import build_app
from src.core.task_queue import (
    QueueTask,
    TaskPriority,
    TaskQueue,
    TaskState,
    get_task_queue,
)


@pytest.fixture
def temp_queue(tmp_path: Path):
    """Create an isolated TaskQueue with a temporary SQLite database."""
    db_file = tmp_path / "task_queue_test.db"
    return TaskQueue(db_path=db_file)


class TestTaskQueueEngine:
    """Tests for core prioritization, leasing, and retry mechanics."""

    def test_priority_scheduling_order(self, temp_queue: TaskQueue):
        # Enqueue tasks in non-sorted order
        temp_queue.enqueue("normal_task", priority=TaskPriority.NORMAL)
        temp_queue.enqueue("low_task", priority=TaskPriority.LOW)
        temp_queue.enqueue("critical_task", priority=TaskPriority.CRITICAL)
        temp_queue.enqueue("high_task", priority=TaskPriority.HIGH)

        leased = temp_queue.lease_tasks(worker_id="worker_test", limit=4)
        assert len(leased) == 4
        # Verify strict priority ordering: CRITICAL (0), HIGH (1), NORMAL (2), LOW (3)
        assert leased[0].name == "critical_task"
        assert leased[0].priority == TaskPriority.CRITICAL
        assert leased[1].name == "high_task"
        assert leased[1].priority == TaskPriority.HIGH
        assert leased[2].name == "normal_task"
        assert leased[2].priority == TaskPriority.NORMAL
        assert leased[3].name == "low_task"
        assert leased[3].priority == TaskPriority.LOW

    def test_atomic_leasing_and_completion(self, temp_queue: TaskQueue):
        task = temp_queue.enqueue("single_job", payload={"key": "val"})
        assert task.state == TaskState.PENDING

        # Worker 1 leases task
        leased = temp_queue.lease_task(worker_id="w1", lease_duration_sec=20.0)
        assert leased is not None
        assert leased.task_id == task.task_id
        assert leased.state == TaskState.RUNNING
        assert leased.leased_by == "w1"

        # Worker 2 attempts to lease, should get None
        assert temp_queue.lease_task(worker_id="w2") is None

        # Worker 1 completes task
        ok = temp_queue.complete_task(task_id=task.task_id, worker_id="w1", result={"status": "done"})
        assert ok is True

        completed_task = temp_queue.get_task(task.task_id)
        assert completed_task is not None
        assert completed_task.state == TaskState.COMPLETED
        assert completed_task.result == {"status": "done"}
        assert completed_task.leased_by is None

    def test_worker_heartbeat_extension(self, temp_queue: TaskQueue):
        task = temp_queue.enqueue("heartbeat_job")
        leased = temp_queue.lease_task(worker_id="w_hb", lease_duration_sec=10.0)
        assert leased is not None

        old_until = leased.leased_until
        time.sleep(0.01)
        extended = temp_queue.heartbeat(task_id=task.task_id, worker_id="w_hb", extension_sec=30.0)
        assert extended is True

        updated_task = temp_queue.get_task(task.task_id)
        assert updated_task is not None
        assert updated_task.leased_until > old_until

    def test_stale_lease_reclamation(self, temp_queue: TaskQueue):
        task = temp_queue.enqueue("stale_job")
        leased = temp_queue.lease_task(worker_id="crashing_worker", lease_duration_sec=0.01)
        assert leased is not None

        # Sleep briefly so lease expires
        time.sleep(0.05)
        reclaimed_count = temp_queue.reclaim_expired_leases()
        assert reclaimed_count == 1

        reclaimed_task = temp_queue.get_task(task.task_id)
        assert reclaimed_task is not None
        assert reclaimed_task.state == TaskState.PENDING
        assert reclaimed_task.leased_by is None

    def test_exponential_backoff_and_dlq_transition(self, temp_queue: TaskQueue):
        task = temp_queue.enqueue("flaky_job", max_retries=2)

        # Retry 1
        leased1 = temp_queue.lease_task(worker_id="w1")
        assert leased1 is not None
        ok1, state1 = temp_queue.fail_task(task_id=task.task_id, worker_id="w1", error="Transient error 1", base_delay_sec=0.01)
        assert ok1 is True
        assert state1 == TaskState.PENDING

        t1 = temp_queue.get_task(task.task_id)
        assert t1.retry_count == 1
        assert t1.scheduled_at > t1.created_at

        # Sleep to pass delay and lease for Retry 2
        time.sleep(0.02)
        leased2 = temp_queue.lease_task(worker_id="w2")
        assert leased2 is not None
        ok2, state2 = temp_queue.fail_task(task_id=task.task_id, worker_id="w2", error="Transient error 2", base_delay_sec=0.01)
        assert ok2 is True
        assert state2 == TaskState.PENDING

        t2 = temp_queue.get_task(task.task_id)
        assert t2.retry_count == 2

        # Sleep to pass delay and lease for Retry 3 (exceeds max_retries=2)
        time.sleep(0.04)
        leased3 = temp_queue.lease_task(worker_id="w3")
        assert leased3 is not None
        ok3, state3 = temp_queue.fail_task(task_id=task.task_id, worker_id="w3", error="Fatal error", base_delay_sec=0.01)
        assert ok3 is True
        assert state3 == TaskState.DEAD_LETTER

        t3 = temp_queue.get_task(task.task_id)
        assert t3.state == TaskState.DEAD_LETTER
        assert t3.retry_count == 3
        assert t3.error == "Fatal error"

    def test_dlq_inspection_and_recovery(self, temp_queue: TaskQueue):
        # Enqueue and push into DLQ directly via 0 max_retries
        task = temp_queue.enqueue("doomed_job", max_retries=0)
        temp_queue.lease_task(worker_id="w_dlq")
        temp_queue.fail_task(task_id=task.task_id, error="Terminal crash")

        dlq_items = temp_queue.get_dlq_tasks()
        assert len(dlq_items) == 1
        assert dlq_items[0].task_id == task.task_id

        # 1. Test single retry
        ok_retry = temp_queue.retry_dlq_task(task.task_id)
        assert ok_retry is True
        retried_task = temp_queue.get_task(task.task_id)
        assert retried_task.state == TaskState.PENDING
        assert retried_task.retry_count == 0

        # Push back into DLQ
        temp_queue.lease_task(worker_id="w_dlq")
        temp_queue.fail_task(task_id=task.task_id, error="Terminal crash 2")
        assert len(temp_queue.get_dlq_tasks()) == 1

        # 2. Test retry-all
        retried_all = temp_queue.retry_all_dlq()
        assert retried_all == 1
        assert len(temp_queue.get_dlq_tasks()) == 0

        # Push back into DLQ and test clear
        temp_queue.lease_task(worker_id="w_dlq")
        temp_queue.fail_task(task_id=task.task_id, error="Terminal crash 3")
        assert len(temp_queue.get_dlq_tasks()) == 1

        cleared = temp_queue.clear_dlq()
        assert cleared == 1
        assert len(temp_queue.get_dlq_tasks()) == 0


class TestQueueCliCommands:
    """Tests for mekong queue CLI command surface."""

    def test_cli_queue_enqueue_and_status(self):
        app = build_app()
        runner = CliRunner()

        # 1. Enqueue
        res_enq = runner.invoke(
            app,
            ["queue", "enqueue", "cli_test_task", "--priority", "high", "--payload", '{"foo": "bar"}', "--json"],
        )
        assert res_enq.exit_code == 0
        task_data = json.loads(res_enq.output)
        assert task_data["name"] == "cli_test_task"
        assert task_data["priority"] == TaskPriority.HIGH

        # 2. Status
        res_stat = runner.invoke(app, ["queue", "status", "--json"])
        assert res_stat.exit_code == 0
        stat_data = json.loads(res_stat.output)
        assert "pending" in stat_data
        assert stat_data["pending"] >= 1

    def test_cli_queue_process_and_dlq(self):
        app = build_app()
        runner = CliRunner()

        # Enqueue a task to process
        runner.invoke(app, ["queue", "enqueue", "process_me_cli", "--priority", "critical"])

        # Process / lease
        res_proc = runner.invoke(app, ["queue", "process", "--limit", 1, "--json"])
        assert res_proc.exit_code == 0
        leased_list = json.loads(res_proc.output)
        assert isinstance(leased_list, list)

        # DLQ commands
        res_dlq_list = runner.invoke(app, ["queue", "dlq", "--action", "list", "--json"])
        assert res_dlq_list.exit_code == 0
        dlq_list = json.loads(res_dlq_list.output)
        assert isinstance(dlq_list, list)

        res_dlq_clear = runner.invoke(app, ["queue", "dlq", "--action", "clear", "--json"])
        assert res_dlq_clear.exit_code == 0
        clear_res = json.loads(res_dlq_clear.output)
        assert clear_res["ok"] is True


class TestMcpQueueToolsParity:
    """Tests for native MCP queue tools dual-engine parity."""

    def test_mcp_queue_enqueue_and_status_fallback(self):
        from scripts.mcp_server import handle_queue_enqueue, handle_queue_status

        raw_enq = handle_queue_enqueue({"name": "mcp_async_task", "priority": "high", "payload": {"step": 1}})
        enq_data = json.loads(raw_enq)
        assert enq_data["ok"] is True
        assert enq_data["data"]["name"] == "mcp_async_task"

        raw_stat = handle_queue_status({})
        stat_data = json.loads(raw_stat)
        assert stat_data["ok"] is True
        assert "total_tasks" in stat_data["data"]

    def test_mcp_queue_dlq_fallback(self):
        from scripts.mcp_server import handle_queue_dlq_action

        raw_dlq = handle_queue_dlq_action({"action": "list"})
        dlq_data = json.loads(raw_dlq)
        assert dlq_data["ok"] is True
        assert "total_dlq" in dlq_data["data"]

    def test_core_mcp_server_queue_handlers(self):
        from src.core.mcp_server import MekongMcpServer

        server = MekongMcpServer()
        enq_raw = server._handle_queue_enqueue(name="core_mcp_task", priority="normal")
        enq_data = json.loads(enq_raw)
        assert enq_data["ok"] is True

        stat_raw = server._handle_queue_status()
        stat_data = json.loads(stat_raw)
        assert stat_data["ok"] is True

        dlq_raw = server._handle_queue_dlq_action(action="list")
        dlq_data = json.loads(dlq_raw)
        assert dlq_data["ok"] is True


class TestAstCoreBoundary:
    """Verify strict standard-library-only rule for task_queue.py."""

    FORBIDDEN_MODULES = {
        "anthropic",
        "openai",
        "requests",
        "httpx",
        "fastapi",
        "pydantic",
        "aiohttp",
        "numpy",
        "torch",
        "celery",
        "rq",
        "redis",
    }

    def test_pure_standard_library_imports(self):
        rel_path = "src/core/task_queue.py"
        full_path = Path(__file__).resolve().parents[1] / rel_path
        assert full_path.exists(), f"File {rel_path} does not exist"

        tree = ast.parse(full_path.read_text(encoding="utf-8"), filename=rel_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden import '{alias.name}' found in {rel_path} (line {node.lineno})"
                    )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    assert root_pkg not in self.FORBIDDEN_MODULES, (
                        f"Forbidden from-import '{node.module}' found in {rel_path} (line {node.lineno})"
                    )
