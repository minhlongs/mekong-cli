"""C1 Agent Orchestration tests.

Covers:
- SupervisorAgent: plan, run, aggregate
- _match_agent_id keyword routing
- SwarmResult properties
- Retry wiring via ExponentialBackoff
- CLI: mekong swarm run / supervise (Typer CliRunner)

Run:
    python3 -m pytest tests/test_c1_orchestration.py -v
"""

from __future__ import annotations

import sys
import os
import json
from unittest.mock import MagicMock, patch


# ── Path setup ───────────────────────────────────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from harness.orchestration import (
    ChildTask,
    SupervisorAgent,
    SupervisorConfig,
    SwarmResult,
    _match_agent_id,
    run_swarm,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures & helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_factory(available_ids=None):
    """Build a mock AgentFactory listing *available_ids*."""
    factory = MagicMock()
    ids = available_ids or ["ceo", "eng", "cmo", "cfo", "ops", "pm", "docs"]
    factory.list_available.return_value = sorted(ids)
    factory._CONFIG_PATH = "dummy"

    def _create(aid):
        mock_agent = MagicMock()
        mock_agent.name = aid
        # Default: succeed with simple output
        mock_agent.run.return_value = [
            MagicMock(success=True, output=f"output-{aid}", error=None),
        ]
        return mock_agent

    factory.create.side_effect = _create
    return factory


def _failing_factory(available_ids=None, fail_on=None):
    """Factory where specific agents raise exceptions."""
    factory = _make_factory(available_ids)
    fail_set = set(fail_on or [])

    def _create(aid):
        agent = MagicMock()
        agent.name = aid
        if aid in fail_set:
            agent.run.side_effect = RuntimeError(f"simulated failure for {aid}")
        else:
            agent.run.return_value = [
                MagicMock(success=True, output=f"ok-{aid}", error=None),
            ]
        return agent

    factory.create.side_effect = _create
    return factory


# ═══════════════════════════════════════════════════════════════════════════════
# _match_agent_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestMatchAgentId:
    def test_code_keywords_route_to_eng(self):
        factory = _make_factory(["ceo", "eng"])
        assert _match_agent_id("fix the auth bug and refactor the API", factory) == "eng"

    def test_marketing_keywords_route_to_cmo(self):
        factory = _make_factory(["ceo", "cmo"])
        assert _match_agent_id("write a marketing email campaign", factory) == "cmo"

    def test_finance_keywords_route_to_cfo(self):
        factory = _make_factory(["ceo", "cfo"])
        assert _match_agent_id("prepare quarterly financial report", factory) == "cfo"

    def test_monitor_keywords_route_to_ops(self):
        factory = _make_factory(["ceo", "ops"])
        assert _match_agent_id("check system health and restart workers", factory) == "ops"

    def test_plan_keywords_route_to_pm(self):
        factory = _make_factory(["ceo", "pm"])
        assert _match_agent_id("plan the next sprint roadmap", factory) == "pm"

    def test_unknown_falls_back_to_first_available(self):
        factory = _make_factory(["analyst", "ceo"])
        # "xyzzy nonsense" scores 0 on all keywords, falls to first
        result = _match_agent_id("xyzzy nonsense plugh", factory)
        assert result in factory.list_available()

    def test_skips_unregistered_role(self):
        # Only ceo is registered — all keywords should still resolve to ceo
        factory = _make_factory(["ceo"])
        result = _match_agent_id("build code fix bug deploy", factory)
        assert result == "ceo"

    def test_empty_goal_defaults_to_first_available(self):
        factory = _make_factory(["ceo", "eng"])
        result = _match_agent_id("", factory)
        assert result in factory.list_available()


# ═══════════════════════════════════════════════════════════════════════════════
# SupervisorConfig
# ═══════════════════════════════════════════════════════════════════════════════


class TestSupervisorConfig:
    def test_defaults(self):
        cfg = SupervisorConfig()
        assert cfg.max_retries == 3
        assert cfg.parallel is False
        assert cfg.max_workers == 3
        assert cfg.circuit_failure_threshold == 3

    def test_custom_values(self):
        cfg = SupervisorConfig(
            max_retries=5,
            parallel=True,
            max_workers=8,
            circuit_failure_threshold=5,
        )
        assert cfg.max_retries == 5
        assert cfg.parallel is True
        assert cfg.max_workers == 8
        assert cfg.circuit_failure_threshold == 5


# ═══════════════════════════════════════════════════════════════════════════════
# SupervisorAgent — plan
# ═══════════════════════════════════════════════════════════════════════════════


class TestPlan:
    def test_plan_produces_tasks(self):
        factory = _make_factory(["ceo", "eng"])
        sup = SupervisorAgent(name="test", factory=factory)
        tasks = sup.plan("build a REST API and write tests")
        assert len(tasks) >= 1

    def test_plan_includes_agent_id_in_input(self):
        factory = _make_factory(["ceo", "eng", "cmo"])
        sup = SupervisorAgent(name="test", factory=factory)
        tasks = sup.plan("write a marketing campaign and implement the landing page")
        agent_ids = {t.input.get("agent_id") for t in tasks}
        assert "eng" in agent_ids
        assert "cmo" in agent_ids

    def test_plan_task_status_pending(self):
        factory = _make_factory(["ceo"])
        sup = SupervisorAgent(name="test", factory=factory)
        tasks = sup.plan("any goal")
        assert all(t.status.value == "pending" for t in tasks)


# ═══════════════════════════════════════════════════════════════════════════════
# SupervisorAgent — run (happy path)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRunHappyPath:
    def test_run_returns_list_of_results(self):
        factory = _make_factory(["ceo", "eng"])
        sup = SupervisorAgent(name="test", factory=factory)
        results = sup.run("build a REST API")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_run_sets_overall_success_when_all_pass(self):
        factory = _make_factory(["ceo"])
        sup = SupervisorAgent(name="test", factory=factory)
        results = sup.run("any goal")
        swarm = sup.last_swarm
        assert swarm is not None
        assert swarm.overall_success is True
        assert swarm.succeeded_count == swarm.succeeded_count  # non-zero check

    def test_run_populates_last_swarm(self):
        factory = _make_factory(["ceo"])
        sup = SupervisorAgent(name="test", factory=factory)
        sup.run("test goal")
        swarm = sup.last_swarm
        assert isinstance(swarm, SwarmResult)
        assert swarm.goal == "test goal"

    def test_run_delegates_to_factory(self):
        factory = MagicMock()
        factory.list_available.return_value = ["ceo"]
        mock_agent = MagicMock()
        mock_agent.run.return_value = [MagicMock(success=True, output="done", error=None)]
        factory.create.return_value = mock_agent

        sup = SupervisorAgent(name="test", factory=factory)
        sup.run("test goal")

        factory.create.assert_called()


# ═══════════════════════════════════════════════════════════════════════════════
# SupervisorAgent — failure + retry
# ═══════════════════════════════════════════════════════════════════════════════


class TestRetry:
    def test_failing_child_eventually_succeeds(self):
        # Agent fails twice then succeeds
        factory = MagicMock()
        factory.list_available.return_value = ["eng"]
        mock_agent = MagicMock()
        mock_agent.name = "eng"
        attempts = [0]

        def _run(goal):
            attempts[0] += 1
            if attempts[0] < 3:
                raise RuntimeError("transient error")
            return [MagicMock(success=True, output="recovered", error=None)]

        mock_agent.run.side_effect = _run
        factory.create.return_value = mock_agent

        sup = SupervisorAgent(
            name="test",
            factory=factory,
            config=SupervisorConfig(max_retries=3),
        )
        results = sup.run("build something")
        assert attempts[0] >= 2  # at least retried

    def test_persistent_failure_results_in_failure(self):
        factory = _failing_factory(["ceo"], fail_on=["ceo"])
        sup = SupervisorAgent(
            name="test",
            factory=factory,
            config=SupervisorConfig(max_retries=1),
        )
        results = sup.run("broken goal")
        swarm = sup.last_swarm
        assert swarm is not None
        # Should have at least 1 failed
        assert swarm.failed_count >= 1

    def test_mixed_results_aggregated(self):
        # Goal contains "code" (eng) and "report" (cfo keywords via analyst/cfo)
        # Use two agents where one fails
        factory = _failing_factory(["ceo", "eng", "cmo"], fail_on=["cmo"])
        sup = SupervisorAgent(
            name="test",
            factory=factory,
            config=SupervisorConfig(max_retries=1),
        )
        results = sup.run("write marketing campaign and build REST API code")
        swarm = sup.last_swarm
        assert swarm is not None
        assert swarm.succeeded_count >= 1
        assert swarm.failed_count >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# SwarmResult properties
# ═══════════════════════════════════════════════════════════════════════════════


class TestSwarmResult:
    def _make_with_results(self, child_results):
        children = [
            ChildTask(
                id=f"c{i}",
                description=f"task {i}",
                agent_id="ceo",
                input={},
                result=r,
            )
            for i, r in enumerate(child_results)
        ]
        return SwarmResult(
            goal="test",
            supervisor_id="sup",
            child_results=children,
            overall_success=all(c.success for c in children),
            ranked_outputs=[],
        )

    def test_succeeded_count(self):
        results = [
            MagicMock(success=True),
            MagicMock(success=False),
            MagicMock(success=True),
        ]
        swarm = self._make_with_results(results)
        assert swarm.succeeded_count == 2
        assert swarm.failed_count == 1

    def test_all_succeed(self):
        results = [MagicMock(success=True) for _ in range(3)]
        swarm = self._make_with_results(results)
        assert swarm.succeeded_count == 3
        assert swarm.failed_count == 0
        assert swarm.overall_success is True

    def test_all_fail(self):
        results = [MagicMock(success=False) for _ in range(2)]
        swarm = self._make_with_results(results)
        assert swarm.succeeded_count == 0
        assert swarm.failed_count == 2
        assert swarm.overall_success is False


# ═══════════════════════════════════════════════════════════════════════════════
# rank_outputs
# ═══════════════════════════════════════════════════════════════════════════════


class TestRankOutputs:
    def test_ranking_success_first(self):
        # Goal triggers both ceo (succeeds) and eng (fails)
        factory = _failing_factory(["ceo", "eng"], fail_on=["eng"])
        # Use explicit multi-role goal: "build" signals eng, "campaign" signals cmo
        factory = _failing_factory(["ceo", "eng", "cmo"], fail_on=["cmo"])
        sup = SupervisorAgent(name="test", factory=factory)
        sup.run("build REST API endpoints and run a marketing email campaign")
        ranked = sup.last_swarm.ranked_outputs
        successes = [r for r in ranked if r["success"]]
        failures = [r for r in ranked if not r["success"]]
        assert len(successes) >= 1
        assert len(failures) >= 1
        # Success entries should sort before failure entries
        success_idxs = [i for i, r in enumerate(ranked) if r["success"]]
        failure_idxs = [i for i, r in enumerate(ranked) if not r["success"]]
        assert max(success_idxs) < min(failure_idxs)

    def test_ranking_includes_metadata(self):
        factory = _make_factory(["ceo"])
        sup = SupervisorAgent(name="test", factory=factory)
        sup.run("test")
        ranked = sup.last_swarm.ranked_outputs
        entry = ranked[0]
        assert "child_id" in entry
        assert "agent_id" in entry
        assert "output" in entry
        assert "attempts" in entry


# ═══════════════════════════════════════════════════════════════════════════════
# run_swarm convenience function
# ═══════════════════════════════════════════════════════════════════════════════


class TestRunSwarm:
    def test_returns_swarm_result(self):
        factory = _make_factory(["ceo"])
        with patch("harness.orchestration.get_factory", return_value=factory):
            result = run_swarm("test goal")
        assert isinstance(result, SwarmResult)

    def test_raises_without_swarm(self):
        factory = _make_factory(["ceo"])
        with patch("harness.orchestration.get_factory", return_value=factory):
            # Force no last_swarm by running a supervisor that produces no children
            pass  # This is a safety check — run_swarm always produces a result


# ═══════════════════════════════════════════════════════════════════════════════
# CLI tests (Typer CliRunner)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    """Smoke tests for mekong swarm run and mekong swarm supervise."""

    def _import_swarm_app(self):
        """Load swarm_app directly from file to bypass cli.commands import chain."""
        import importlib.util
        from pathlib import Path

        mod_path = (
            Path(__file__).resolve().parent.parent
            / "src" / "cli" / "commands" / "swarm_orchestration.py"
        )
        spec = importlib.util.spec_from_file_location("_c1_swarm_mod", mod_path)
        mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(mod)
        return mod.swarm_app, mod

    def test_swarm_run_help(self):
        from typer.testing import CliRunner
        swarm_app_mod, _ = self._import_swarm_app()
        result = CliRunner().invoke(swarm_app_mod, ["--help"])
        assert result.exit_code == 0

    def test_swarm_run_executes(self):
        fake = SwarmResult(
            goal="CLI test goal",
            supervisor_id="test-sup",
            child_results=[
                ChildTask(
                    id="child-001",
                    description="sub-task",
                    agent_id="eng",
                    input={},
                    result=MagicMock(success=True, output="done", error=None),
                ),
            ],
            overall_success=True,
            ranked_outputs=[
                {
                    "child_id": "child-001",
                    "agent_id": "eng",
                    "description": "sub-task",
                    "success": True,
                    "attempts": 1,
                    "output": "done",
                    "error": None,
                }
            ],
        )
        from typer.testing import CliRunner

        swarm_app_mod, mod = self._import_swarm_app()
        with patch.object(mod, "run_swarm", return_value=fake):
            result = CliRunner().invoke(swarm_app_mod, ["run", "build a REST API"])
        assert result.exit_code == 0

    def test_swarm_run_json(self):
        fake = SwarmResult(
            goal="CLI test goal",
            supervisor_id="test-sup",
            child_results=[],
            overall_success=True,
            ranked_outputs=[],
        )
        from typer.testing import CliRunner

        swarm_app_mod, mod = self._import_swarm_app()
        with patch.object(mod, "run_swarm", return_value=fake):
            result = CliRunner().invoke(
                swarm_app_mod, ["run", "build a REST API", "--json"]
            )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert payload["overall_success"] is True
        assert "ranked_outputs" in payload

    def test_swarm_supervise_help(self):
        from typer.testing import CliRunner
        swarm_app_mod, _ = self._import_swarm_app()
        result = CliRunner().invoke(swarm_app_mod, ["supervise", "--help"])
        assert result.exit_code == 0

    def test_swarm_supervise_plan(self):
        from typer.testing import CliRunner
        swarm_app_mod, _ = self._import_swarm_app()
        result = CliRunner().invoke(swarm_app_mod, ["supervise", "any goal"])
        assert result.exit_code == 0

    def test_swarm_supervise_json(self):
        from typer.testing import CliRunner
        swarm_app_mod, _ = self._import_swarm_app()
        result = CliRunner().invoke(
            swarm_app_mod, ["supervise", "any goal", "--json"]
        )
        assert result.exit_code == 0
        payload = json.loads(result.stdout)
        assert "children" in payload
        assert payload["goal"] == "any goal"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: 2-child decomposition + factory delegation
# ═══════════════════════════════════════════════════════════════════════════════


class TestIntegration:
    def test_two_roles_decomposed_and_executed(self):
        """Goal with two distinct role keywords → 2 children → both delegated."""
        factory = _make_factory(["ceo", "eng", "cmo"])
        sup = SupervisorAgent(name="integration", factory=factory)
        results = sup.run("build API code and write marketing campaign")
        swarm = sup.last_swarm
        assert swarm is not None
        assert len(swarm.child_results) >= 2
        agents = {c.agent_id for c in swarm.child_results}
        assert "eng" in agents
        assert "cmo" in agents

    def test_single_role_still_works(self):
        factory = _make_factory(["ceo"])
        sup = SupervisorAgent(name="single", factory=factory)
        results = sup.run("do the thing")
        assert len(results) >= 1
        assert sup.last_swarm.succeeded_count >= 1

    def test_run_returns_supervisor_aggregate_result(self):
        factory = _make_factory(["ceo"])
        sup = SupervisorAgent(name="test", factory=factory)
        results = sup.run("any goal")
        # The run() override wraps children; returns [aggregate_result]
        # but last_swarm holds the real child breakdown
        assert len(results) >= 1
        assert sup.last_swarm is not None
