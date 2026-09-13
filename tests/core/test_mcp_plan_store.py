"""Tests for src.core.mcp_plan_store — McpPlanStore."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

import src.core.mcp_plan_store as mod
from src.core.mcp_plan_store import (
    McpPlan,
    McpPlanStore,
    _decompose_goal,
    get_plan_store,
)


class TestMcpPlan:
    def test_create(self):
        plan = McpPlan(plan_id="p1", goal="Do something")
        assert plan.plan_id == "p1"
        assert plan.goal == "Do something"
        assert plan.status == "active"
        assert plan.tasks == []
        assert plan.created_at is not None
        assert plan.completed_at is None

    def test_invalid_status_defaults_to_active(self):
        plan = McpPlan(plan_id="p1", goal="g", status="invalid_status")
        assert plan.status == "active"

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

    def test_asterisk_bullet_points(self):
        goal = "* Task 1\n* Task 2"
        tasks = _decompose_goal(goal)
        assert len(tasks) == 2
        assert tasks[0]["description"] == "Task 1"
        assert tasks[1]["description"] == "Task 2"

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

    def test_other_conjunctions(self):
        assert len(_decompose_goal("Do X then Do Y")) == 2
        assert len(_decompose_goal("Do X followed by Do Y")) == 2
        assert len(_decompose_goal("Do X afterwards Do Y")) == 2

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

    def test_default_path(self):
        s = McpPlanStore()
        assert s._path.name == "mcp_plans.json"

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

    def test_list_with_status_filter(self, store):
        p1 = store.create("Plan 1")
        p2 = store.create("Plan 2")
        store.complete(p1.plan_id)
        active = store.list(status="active")
        assert len(active) == 1
        assert active[0].plan_id == p2.plan_id
        completed = store.list(status="completed")
        assert len(completed) == 1
        assert completed[0].plan_id == p1.plan_id

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

    def test_update_task_status_nonexistent_plan(self, store):
        assert store.update_task_status("nonexistent-plan", "t1", "done") is None

    def test_delete(self, store):
        p = store.create("To delete")
        assert store.delete(p.plan_id) is True
        assert store.get(p.plan_id) is None
        assert store.delete("nonexistent-id") is False

    def test_stats(self, store):
        store.create("Active")
        p2 = store.create("Completed")
        store.complete(p2.plan_id)
        st = store.stats()
        assert st["total"] == 2
        assert st["active"] == 1
        assert st["completed"] == 1

    def test_load_skips_when_already_loaded(self, store):
        store.create("Plan")
        assert len(store._plans) == 1
        store._load()
        assert len(store._plans) == 1

    def test_load_skips_malformed_items(self, store):
        path = store._path
        items = [
            {"plan_id": "p1", "goal": "ok"},
            {"bad": 123},
            {"plan_id": "p2"},
        ]
        path.write_text(json.dumps(items), encoding="utf-8")
        s2 = McpPlanStore(path)
        plans = s2.list()
        assert len(plans) == 1
        assert plans[0].plan_id == "p1"

    def test_load_handles_invalid_json(self, store):
        path = store._path
        path.write_text("{not valid json", encoding="utf-8")
        s2 = McpPlanStore(path)
        assert s2.list() == []

    def test_load_handles_oserror(self, store):
        path = store._path
        s2 = McpPlanStore(path)
        with patch("pathlib.Path.read_text", side_effect=OSError("Read error")):
            assert s2.list() == []

    def test_load_empty_or_whitespace_file(self, store):
        path = store._path
        path.write_text("   \n", encoding="utf-8")
        s2 = McpPlanStore(path)
        assert s2.list() == []

    def test_load_non_list_json(self, store):
        path = store._path
        path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        s2 = McpPlanStore(path)
        assert s2.list() == []

    def test_save_not_dirty_early_return(self, store):
        store._dirty = False
        store._save()

    def test_save_oserror(self, store):
        store._dirty = True
        with patch("pathlib.Path.write_text", side_effect=OSError("Write failed")):
            store._save()
            assert store._dirty is True

    def test_persistence(self, store):
        p1 = store.create("Persist me")
        store2 = McpPlanStore(store._path)
        fetched = store2.get(p1.plan_id)
        assert fetched is not None
        assert fetched.goal == "Persist me"


class TestGetPlanStore:
    def test_singleton(self):
        mod._store = None
        try:
            s1 = get_plan_store()
            s2 = get_plan_store()
            assert s1 is s2
        finally:
            mod._store = None
