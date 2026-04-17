"""Tests for SoloCompanyOrchestrator with fake LLM responses."""

from __future__ import annotations

from agent_core.memory import SeedMemory
from agent_core.orchestrator import Role, SoloCompanyOrchestrator, Task


class FakeLLM:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def chat(self, messages, system=None, max_tokens=1024):
        self.calls.append({"messages": list(messages), "system": system})
        return self._responses.pop(0) if self._responses else ""


def test_task_has_uuid_and_defaults():
    t = Task(goal="demo", assigned_role=Role.CEO)
    assert t.status == "pending"
    assert len(t.id) == 8
    assert t.context == {}


def test_orchestrator_runs_full_pipeline_pass(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            "1. Plan item A\n2. Plan item B",  # CEO plan
            '{"file_path": "out.txt", "content": "hello"}',  # Developer
            '{"status": "pass", "summary": "OK", "issues": []}',  # Tester
            '{"score": 9, "verdict": "ship", "notes": ["clean code"]}',  # Reviewer
        ]
    )
    orch = SoloCompanyOrchestrator(llm=fake, memory=tmp_memory)
    report = orch.process_goal("build a hello file")

    assert "Plan item A" in report.plan
    assert "hello" in report.artifact
    assert report.test["status"] == "pass"
    assert report.review["verdict"] == "ship"
    assert report.review["score"] == 9

    statuses = [t.status for t in report.tasks]
    assert statuses == ["completed", "completed", "completed", "completed"]
    roles = [t.assigned_role for t in report.tasks]
    assert roles == [Role.CEO, Role.DEVELOPER, Role.TESTER, Role.REVIEWER]


def test_orchestrator_marks_tester_failed(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            "plan",
            "artifact",
            '{"status": "fail", "summary": "missing X", "issues": ["X"]}',
            '{"score": 3, "verdict": "block", "notes": ["bugs"]}',
        ]
    )
    orch = SoloCompanyOrchestrator(llm=fake, memory=tmp_memory)
    report = orch.process_goal("broken goal")

    tester_task = report.tasks[2]
    assert tester_task.status == "failed"
    reviewer_task = report.tasks[3]
    assert reviewer_task.status == "failed"


def test_orchestrator_clamps_review_score(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            "plan",
            "art",
            '{"status": "pass", "summary": "ok", "issues": []}',
            '{"score": 99, "verdict": "ship", "notes": []}',
        ]
    )
    orch = SoloCompanyOrchestrator(llm=fake, memory=tmp_memory)
    report = orch.process_goal("goal")
    assert report.review["score"] == 10


def test_report_as_dict_shape(tmp_memory: SeedMemory):
    fake = FakeLLM(
        [
            "plan",
            "art",
            '{"status": "pass", "summary": "ok", "issues": []}',
            '{"score": 8, "verdict": "ship", "notes": []}',
        ]
    )
    orch = SoloCompanyOrchestrator(llm=fake, memory=tmp_memory)
    d = orch.process_goal("goal").as_dict()
    assert set(d.keys()) == {"goal", "plan", "artifact", "test", "review", "tasks"}
    assert len(d["tasks"]) == 4
    assert d["tasks"][0]["role"] == "ceo"
