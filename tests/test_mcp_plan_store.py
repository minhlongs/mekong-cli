"""Tests for src.core.mcp_plan_store — McpPlanStore."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from src.core.mcp_plan_store import McpPlan, McpPlanStore, _decompose_goal


class TestMcpPlan:
    def test_create(self):
        plan = McpPlan(plan_id="p1", goal="Do something")
        assert plan.plan_id == "p1"
        assert plan.goal == "Do something"
        assert plan.status == "active"
        assert plan.tasks == []
        assert plan.created_at is not None
        assert plan.completed_at is None

    def test_to_dict_roundtrip(self):
        plan = McpPlan(plan_id="p1", goal="Test", tasks=[{"id": "t1", "description": "x", "status": "todo"}])
        d = plan.to_dict()
        plan2 = McpPlan.from_dict(d)
        assert plan2.plan_id == "p1"
        assert plan2.goal == "Test"
        assert len(plan2.tasks) == 1

    def test_from_dict_missing_fields(self):
        with pytest.raises(ValueError, match="Missing plan_id or goal"):
            McpPlan.from_dict({})
        with pytest.raises(ValueError, match="Missing plan_id or goal"):
            McpPlan.from_dict({"plan_id": "p1"})

    def test_to_dict_with_completed(self):
        plan = McpPlan(plan_id="p1", goal="G", status="completed", completed_at="now")
        d = plan.to_dict()
        assert d["status"] == "completed"
        assert d["completed_at"] == "now"


class TestDecomposeGoal:
    def test_empty(self):
        assert _decompose_goal("") == []
        assert _decompose_goal("   ") == []

    def test_bullet_points(self):
        goal = "- Do A\n- Do B\n- Do C"
        tasks = _decompose_goal(goal)
        assert len(tasks) == 3
        assert tasks[0]["description"] == "Do A"
        assert tasks[1]["description"] == "Do B"
        assert tasks[2]["description"] == "Do C"

    def test_numbered_list(self):
        goal = "1. Setup\n2. Build\n3. Deploy"
        tasks = _decompose_goal(goal)
        assert len(tasks) == 3

    def test_semicolon_split(self):
        goal = "Research; Implement; Test"
        tasks = _decompose_goal(goal)
        assert len(tasks) == 3

    def test_conjunction_split(self):
        goal = "Setup CI and then Deploy"
        tasks = _decompose_goal(goal)
        assert len(tasks) == 2

    def test_single_task_fallback(self):
        goal = "Just one task here"
        tasks = _decompose_goal(goal)
        assert len(tasks) == 1
        assert tasks[0]["description"] == "Just one task here"


class TestMcpPlanStore:
    @pytest.fixture
    def store(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plans.json"
            yield McpPlanStore(path)

    def test_create_plan(self, store):
        plan = store.create("Test plan")
        assert plan.plan_id
        assert plan.goal == "Test plan"
        assert plan.status == "active"
        assert len(plan.tasks) >= 1

    def test_get_plan(self, store):
        created = store.create("Get me")
        fetched = store.get(created.plan_id)
        assert fetched is not None
        assert fetched.plan_id == created.plan_id

    def test_get_nonexistent(self, store):
        assert store.get("no-such-id") is None

    def test_list_plans(self, store):
        store.create("A")
        store.create("B")
        plans = store.list()
        assert len(plans) == 2

    def test_complete_plan(self, store):
        plan = store.create("Complete me")
        assert store.complete(plan.plan_id) is not None
        fetched = store.get(plan.plan_id)
        assert fetched is not None
        assert fetched.status == "completed"
        assert fetched.completed_at is not None

    def test_complete_nonexistent(self, store):
        assert store.complete("no-such-id") is None

    def test_update_task_status(self, store):
        plan = store.create("Multi step\n- Step A\n- Step B")
        task_id = plan.tasks[0]["id"]
        assert store.update_task_status(plan.plan_id, task_id, "in_progress") is not None
        fetched = store.get(plan.plan_id)
        assert fetched is not None
        assert fetched.tasks[0]["status"] == "in_progress"

    def test_update_nonexistent_task(self, store):
        plan = store.create("Test")
        assert store.update_task_status(plan.plan_id, "no-task", "done") is None

    def test_persistence(self, store):
        p1 = store.create("Persist me")
        store2 = McpPlanStore(store._path)
        fetched = store2.get(p1.plan_id)
        assert fetched is not None
        assert fetched.goal == "Persist me"
