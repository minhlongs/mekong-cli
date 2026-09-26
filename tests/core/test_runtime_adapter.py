# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Unit tests for MekongCoreRuntimeImpl in src/core/runtime_adapter.py.

Covers:
- Dataclasses and enums (Result, Observation, Verification, CheckSpec, Scope, Context, Goal, etc.)
- DAG helpers and topological sorting (_plan_has_dependencies, _topological_task_order, etc.)
- Criteria to verifier mapping (_criteria_to_verifier_dict, _report_to_verification)
- Intent classification heuristics (_classify_intent)
- Runtime initialization, destruction, and health checks
- Execution safety gates (repair limit, governance, capability governance, agent policies, cost guards)
- Delegation, planning, context normalization, and Buzz payload ingestion
- Observation, verification, memory flushing, and commit billing
- Task loop execution, repair escalation, DAG failure propagation, and result merging
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.core.governance import ActionClass, Governance, GovernanceDecision
from src.core.protocols import Plan, PlanStatus, Step
from src.core.runtime_adapter import (
    AgentId,
    CheckResult,
    CheckSpec,
    CommitRecord,
    Context,
    Criteria,
    Goal,
    MekongCoreRuntimeImpl,
    MemoryEntry,
    Observation,
    RepairAction,
    RepairStrategy,
    Result,
    Scope,
    SideEffect,
    Task,
    Verification,
    _classify_intent,
    _criteria_to_verifier_dict,
    _plan_has_dependencies,
    _report_to_verification,
    _topological_task_order,
)


class TestDataclassesAndContext:
    """Test runtime data structures, enums, and Context class."""

    def test_enums(self):
        assert Scope.SESSION.value == "session"
        assert Scope.ORG.value == "org"
        assert Scope.GLOBAL.value == "global"
        assert RepairStrategy.RETRY.value == "retry"
        assert RepairStrategy.FALLBACK.value == "fallback"
        assert RepairStrategy.ESCALATE.value == "escalate"
        assert RepairStrategy.ROLLBACK.value == "rollback"

    def test_dataclasses_instantiation(self):
        agent = AgentId("cfo")
        assert agent.name == "cfo"

        ctx = Context(principal="user1", session_id="sess-1", metadata={"env": "prod"})
        crit = Criteria(checks=[CheckSpec(kind="exit_code", params={"expected": 0})])
        goal = Goal(id="g1", intent="audit finance", context=ctx, criteria=crit)
        assert goal.id == "g1"
        assert goal.intent == "audit finance"
        assert goal.context == ctx
        assert goal.criteria == crit

        step = Step(id="s1", description="Check balances")
        task = Task(id="t1", step=step, agent=agent, params={"k": "v"})
        assert task.id == "t1"
        assert task.step == step
        assert task.agent == agent
        assert task.params == {"k": "v"}

        res = Result(task_id="t1", output={"ok": True}, error=None, metadata={"cost": 0.01})
        assert res.task_id == "t1"
        assert res.output == {"ok": True}
        assert res.error is None
        assert res.metadata == {"cost": 0.01}

        se = SideEffect(kind="file_write", target="app.py", data={"lines": 10})
        assert se.kind == "file_write"
        assert se.target == "app.py"

        obs = Observation(result=res, metrics={"duration": 1.2}, side_effects=[se])
        assert obs.result == res
        assert obs.metrics["duration"] == 1.2
        assert len(obs.side_effects) == 1

        chk_spec = CheckSpec(kind="exit_code")
        cr = CheckResult(check=chk_spec, passed=True, detail="ok")
        assert cr.check == chk_spec
        assert cr.passed is True
        assert cr.detail == "ok"

        ver = Verification(passed=True, checks=[cr], failures=[])
        assert ver.passed is True
        assert len(ver.checks) == 1

        ra = RepairAction(strategy=RepairStrategy.FALLBACK, params={"tool": "alt"})
        assert ra.strategy == RepairStrategy.FALLBACK
        assert ra.params == {"tool": "alt"}

        mem = MemoryEntry(key="k1", value="v1", scope=Scope.SESSION)
        assert mem.key == "k1"
        assert mem.value == "v1"
        assert mem.scope == Scope.SESSION

        rec = CommitRecord(id="c1", result=res)
        assert rec.id == "c1"
        assert rec.result == res

    def test_context_methods(self):
        ctx = Context(principal="admin", session_id="s100", metadata={"role": "root"})
        assert ctx.get("principal") == "admin"
        assert ctx.get("session_id") == "s100"
        assert ctx.get("role") == "root"
        assert ctx.get("missing", "default") == "default"
        assert ctx.get("missing") is None

        assert "principal" in ctx
        assert "role" in ctx
        assert "missing" not in ctx

        assert ctx["principal"] == "admin"
        assert ctx["role"] == "root"

        d = ctx.to_dict()
        assert d == {
            "principal": "admin",
            "session_id": "s100",
            "metadata": {"role": "root"},
        }


class TestDAGAndCriteriaHelpers:
    """Test plan dependencies, topological task ordering, and verification criteria helpers."""

    def test_plan_has_dependencies(self):
        # Empty plan
        p_empty = Plan(id="p1", goal="test", steps=[])
        assert _plan_has_dependencies(p_empty) is False

        # Independent steps
        p_indep = Plan(
            id="p2",
            goal="test",
            steps=[Step(id="s1", description="s1"), Step(id="s2", description="s2")],
        )
        assert _plan_has_dependencies(p_indep) is False

        # Dependent steps
        p_dep = Plan(
            id="p3",
            goal="test",
            steps=[
                Step(id="s1", description="s1"),
                Step(id="s2", description="s2", dependencies=["s1"]),
            ],
        )
        assert _plan_has_dependencies(p_dep) is True

    def test_topological_task_order_single_or_empty(self):
        assert _topological_task_order([]) == []
        t1 = Task(id="t1", step=Step(id="s1", description="s1"), agent=AgentId("cto"))
        assert _topological_task_order([t1]) == [t1]

    def test_topological_task_order_duplicate_ids_raises(self):
        t1 = Task(id="t1", step=Step(id="s1", description="step 1"), agent=AgentId("cto"))
        t2 = Task(id="t2", step=Step(id="s1", description="duplicate step 1"), agent=AgentId("cto"))
        with pytest.raises(RuntimeError, match="duplicate task step ids in plan"):
            _topological_task_order([t1, t2])

    def test_topological_task_order_dag_resolution(self):
        s1 = Step(id="s1", description="prepare")
        s2 = Step(id="s2", description="build", dependencies=["s1"])
        s3 = Step(id="s3", description="deploy", dependencies=["s2"])

        t1 = Task(id="t1", step=s1, agent=AgentId("cto"))
        t2 = Task(id="t2", step=s2, agent=AgentId("cto"))
        t3 = Task(id="t3", step=s3, agent=AgentId("cto"))

        # Passed out of order [t3, t1, t2] -> should resolve to [t1, t2, t3]
        ordered = _topological_task_order([t3, t1, t2])
        assert [t.step.id for t in ordered] == ["s1", "s2", "s3"]

    def test_criteria_to_verifier_dict_all_kinds(self):
        crit = Criteria(
            checks=[
                CheckSpec(kind="exit_code", params={"expected": 0}),
                CheckSpec(kind="output_pattern", params={"pattern": r"OK \d+"}),
                CheckSpec(kind="output_not_contains", params={"text": "FAILED"}),
                CheckSpec(kind="file_exists", params={"filepath": "dist/bundle.js"}),
                CheckSpec(kind="file_not_exists", params={"filepath": "tmp/err.log"}),
            ]
        )
        d = _criteria_to_verifier_dict(crit)
        assert d["exit_code"] == 0
        assert d["output_contains"] == [r"OK \d+"]
        assert d["output_not_contains"] == ["FAILED"]
        assert d["file_exists"] == ["dist/bundle.js"]
        assert d["file_not_exists"] == ["tmp/err.log"]

    def test_criteria_to_verifier_dict_empty_or_no_match(self):
        assert _criteria_to_verifier_dict(Criteria()) == {}
        crit_custom = Criteria(checks=[CheckSpec(kind="unknown_check")])
        assert _criteria_to_verifier_dict(crit_custom) == {}

    def test_report_to_verification(self):
        # Passed report
        chk_pass = MagicMock()
        chk_pass.name = "exit_code"
        chk_pass.status.value = "passed"
        chk_pass.message = "Exit code 0"

        passed_report = MagicMock(
            passed=True,
            errors=[],
            checks=[chk_pass],
        )
        v_pass = _report_to_verification(passed_report)
        assert v_pass.passed is True
        assert len(v_pass.failures) == 0
        assert len(v_pass.checks) == 1
        assert v_pass.checks[0].passed is True

        # Failed report
        chk_fail = MagicMock()
        chk_fail.name = "output_pattern"
        chk_fail.status.value = "failed"
        chk_fail.message = "Pattern not found"

        failed_report = MagicMock(
            passed=False,
            errors=["Exit code 1", "Pattern not found"],
            checks=[chk_pass, chk_fail],
        )
        v_fail = _report_to_verification(failed_report)
        assert v_fail.passed is False
        assert v_fail.failures == ["Exit code 1", "Pattern not found"]
        assert len(v_fail.checks) == 2

    def test_classify_intent_all_roles(self):
        # CFO (finance, budget, accounting)
        assert _classify_intent("Monthly budget and accounting audit") == "cfo"
        assert _classify_intent("Finance report for Q3") == "cfo"

        # CMO (marketing, campaign, brand)
        assert _classify_intent("Marketing campaign for product launch") == "cmo"
        assert _classify_intent("Brand positioning update") == "cmo"

        # CSO (analysis, analyze, strategy, competitive, market)
        assert _classify_intent("Market analysis and competitor strategy") == "cso"
        assert _classify_intent("Analyze competitive landscape") == "cso"

        # CTO (code, refactor, implement, develop, debug, review)
        assert _classify_intent("Implement authentication module") == "cto"
        assert _classify_intent("Refactor database query logic") == "cto"
        assert _classify_intent("Debug crash in worker") == "cto"

        # COO (operations, logistics, workflow)
        assert _classify_intent("Optimize warehouse logistics operations") == "coo"
        assert _classify_intent("Automate daily workflow") == "coo"

        # Planner (plan, roadmap, architecture)
        assert _classify_intent("Plan sprint backlog") == "planner"
        assert _classify_intent("Quarterly roadmap update") == "planner"
        assert _classify_intent("System architecture design") == "planner"

        # Unmatched
        assert _classify_intent("deploy container image") == ""
        assert _classify_intent("") == ""
        assert _classify_intent(None) == ""


class TestRuntimeInitializationAndComponents:
    """Test MekongCoreRuntimeImpl initialization, defaults, and health."""

    def test_init_with_defaults(self):
        disp = MagicMock()
        tools = MagicMock()
        runtime = MekongCoreRuntimeImpl(dispatcher=disp, tool_registry=tools)

        assert runtime._dispatcher == disp
        assert runtime._tool_registry == tools
        assert runtime._agent_id == "default"
        assert runtime._memory_store is not None
        assert runtime._telemetry is not None
        assert runtime._llm_router is not None
        assert runtime._verifier is not None
        assert runtime._memory_separation is None

    def test_init_with_custom_components(self):
        disp = MagicMock()
        tools = MagicMock()
        mem_store = MagicMock()
        mem_sep = MagicMock()
        billing = MagicMock()
        telem = MagicMock()
        router = MagicMock()
        bus = MagicMock()
        gov = MagicMock(spec=Governance)
        reg = MagicMock()
        goal_engine = MagicMock()
        verifier = MagicMock()

        runtime = MekongCoreRuntimeImpl(
            dispatcher=disp,
            tool_registry=tools,
            memory_store=mem_store,
            memory_separation=mem_sep,
            billing=billing,
            telemetry=telem,
            llm_router=router,
            capability_bus=bus,
            agent_id="custom-agent",
            governance=gov,
            max_cost_usd=5.0,
            agent_registry=reg,
            goal_engine=goal_engine,
            verifier=verifier,
        )

        assert runtime._agent_id == "custom-agent"
        assert runtime._memory_store == mem_store
        assert runtime._memory_separation == mem_sep
        assert runtime._billing == billing
        assert runtime._telemetry == telem
        assert runtime._llm_router == router
        assert runtime._capability_bus == bus
        assert runtime._governance == gov
        assert runtime._max_cost_usd == 5.0
        assert runtime._agent_registry == reg
        assert runtime._goal_engine == goal_engine
        assert runtime._verifier == verifier

    def test_health_success_and_exception(self):
        router = MagicMock()
        router.health.return_value = {"status": "ok", "provider": "mock"}
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            llm_router=router,
            agent_id="healthy-agent",
        )
        h = runtime.health()
        assert h["status"] == "ok"
        assert h["agent_id"] == "healthy-agent"
        assert h["llm_router"] == {"status": "ok", "provider": "mock"}

        # Exception in router.health
        router.health.side_effect = RuntimeError("network down")
        h_down = runtime.health()
        assert h_down["status"] == "error"
        assert h_down["error"] == "network down"

    def test_destroy(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            agent_id="test-destroy",
        )
        d = runtime.destroy()
        assert d == {"status": "destroyed", "agent_id": "test-destroy"}
        assert runtime._destroyed is True
        assert runtime._memory_store is None
        assert runtime._telemetry is None


class TestAgentMetaAndRiskResolution:
    """Test resolution of agent metadata and effective risk computation."""

    def test_resolve_agent_meta_explicit_and_singleton(self):
        reg_mock = MagicMock()
        meta_obj = MagicMock(risk_level="HIGH")
        reg_mock.get_meta_obj.return_value = meta_obj

        # Explicit registry
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            agent_registry=reg_mock,
        )
        assert runtime._resolve_agent_meta("cto") == meta_obj
        assert runtime._resolve_agent_meta("") is None

        # Fallback to get_registry() singleton
        runtime_no_reg = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            agent_registry=None,
        )
        with patch("src.core.agent_registry.get_registry", return_value=reg_mock):
            assert runtime_no_reg._resolve_agent_meta("cto") == meta_obj

        # Exception handled
        reg_mock.get_meta_obj.side_effect = KeyError("unknown agent")
        assert runtime._resolve_agent_meta("unknown") is None

    def test_effective_risk_ordering(self):
        runtime = MekongCoreRuntimeImpl(dispatcher=MagicMock(), tool_registry=MagicMock())
        assert runtime._effective_risk("LOW", "MEDIUM") == "MEDIUM"
        assert runtime._effective_risk("HIGH", "LOW") == "HIGH"
        assert runtime._effective_risk("MEDIUM", "CRITICAL") == "CRITICAL"
        assert runtime._effective_risk("CRITICAL", "HIGH") == "CRITICAL"
        # Unknown risk falls back to CRITICAL
        assert runtime._effective_risk("INVALID", "LOW") == "CRITICAL"
        assert runtime._effective_risk("LOW", "UNKNOWN") == "CRITICAL"


class TestMissionsAndTracing:
    """Test start_mission, run lifecycle, buzz integration, and mission tracer hooks."""

    def test_start_mission_with_tracer_and_telemetry(self):
        tracer = MagicMock()
        tracer.start_mission.return_value = "m-100"
        telem = MagicMock()
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            telemetry=telem,
        )
        m_id = runtime.start_mission(
            goal="Test Mission",
            tracer=tracer,
            mission_id="m-100",
        )
        assert m_id == "m-100"
        assert runtime._mission_id == "m-100"
        tracer.start_mission.assert_called_once_with("Test Mission", {"mission_id": "m-100"})
        telem.emit_start.assert_called_with("m-100", "Test Mission")

    def test_start_mission_tracer_exception_handled(self):
        tracer = MagicMock()
        tracer.start_mission.side_effect = RuntimeError("disk full")
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
        )
        # Should not raise
        m_id = runtime.start_mission(goal="Goal", tracer=tracer, mission_id="m-101")
        assert m_id == "m-101"

    def test_run_idempotency_and_lifecycle(self):
        disp = MagicMock()
        disp.dispatch.return_value = {"status": "ok"}
        runtime = MekongCoreRuntimeImpl(dispatcher=disp, tool_registry=MagicMock())

        res = runtime.run("Deploy service")
        assert res.error is None
        assert res.output == {"status": "ok"}

    def test_run_from_payload_with_buzz_adapter(self):
        disp = MagicMock()
        disp.dispatch.return_value = {"status": "ok"}
        runtime = MekongCoreRuntimeImpl(dispatcher=disp, tool_registry=MagicMock())

        buzz_payload = {
            "mission_id": "m-buzz",
            "goal": "Process webhook",
            "context": {"source": "telegram"},
            "criteria": {"exit_code": 0},
        }
        res = runtime.run_from_payload(buzz_payload)
        assert res.error is None
        assert runtime._mission_id == "m-buzz"

    def test_tracer_step_and_stage_and_finish(self):
        tracer = MagicMock()
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
        )
        runtime._mission_id = "m-trace"
        runtime._mission_tracer = tracer

        # _trace_step calls tracer.log_step(mission_id, task_id, {...})
        task = Task(id="t1", step=Step(id="s1", description="step 1"), agent=AgentId("cto"))
        res = Result(task_id="t1", output="ok")
        ver = Verification(passed=True, failures=[])
        runtime._trace_step(task, res, ver)
        tracer.log_step.assert_called_once_with(
            "m-trace",
            "t1",
            {
                "output": "ok",
                "error": None,
                "passed": True,
                "failures": [],
            },
        )

        # _record_stage calls tracer.record_stage(stage, metadata)
        runtime._record_stage("execute", {"count": 1})
        tracer.record_stage.assert_called_with("execute", {"count": 1})

        # _finish_mission calls tracer.end_mission(mission_id, outcome)
        runtime._finish_mission(res)
        tracer.end_mission.assert_called_with("m-trace", "success")


class TestContextAndGoalExtraction:
    """Test goal normalization and context parameter resolution."""

    def test_goal_with_and_without_context(self):
        runtime = MekongCoreRuntimeImpl(dispatcher=MagicMock(), tool_registry=MagicMock())

        ctx = Context(principal="u1", session_id="s1", metadata={"env": "staging"})
        g1 = runtime.goal("Deploy code", ctx)
        assert g1.intent == "Deploy code"
        assert g1.context == ctx

        g2 = runtime.goal("Simple goal")
        assert g2.intent == "Simple goal"
        assert g2.context.principal == "default"

    def test_context_method_variations(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(), tool_registry=MagicMock(), agent_id="agent-007"
        )
        runtime._mission_id = "m-ctx"

        # None -> returns default dict
        c_none = runtime.context(None)
        assert c_none["principal"] == "agent-007"
        assert c_none["mission_id"] == "m-ctx"

        # Goal instance
        ctx_obj = Context(principal="userX", session_id="sessY", metadata={"role": "dev"})
        g = Goal(id="g1", intent="test", context=ctx_obj, criteria=Criteria())
        c_goal = runtime.context(g)
        assert c_goal["principal"] == "userX"
        assert c_goal["session_id"] == "sessY"

        # Dict goal
        c_dict = runtime.context({"mission_id": "m-override", "metadata": {"tag": "v1"}})
        assert c_dict["mission_id"] == "m-override"
        assert c_dict["metadata"] == {"tag": "v1"}


class TestPlanningAndDelegationLogic:
    """Test plan generation, GoalEngine integration, fallback single steps, and delegation."""

    def test_plan_with_string_and_dict_and_goal_engine(self):
        mock_goal_engine = MagicMock()
        mock_plan = Plan(
            id="p-engine",
            goal="GoalEngine Plan",
            steps=[Step(id="s1", description="step from engine")],
            status=PlanStatus.PENDING,
        )
        mock_goal_engine.decompose.return_value = mock_plan

        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            goal_engine=mock_goal_engine,
        )
        # Intent "implement microservice" maps to "cto", which triggers GoalEngine
        p = runtime.plan("implement microservice")
        assert p.id.startswith("plan-")
        assert len(p.steps) == 1
        mock_goal_engine.decompose.assert_called_once_with("implement microservice")

    def test_plan_fallback_single_step_for_unknown_intent(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            goal_engine=None,
        )
        # Unmatched intent -> single step plan
        p_unknown = runtime.plan("make coffee")
        assert len(p_unknown.steps) == 1
        assert p_unknown.steps[0].id == "step-0"
        assert p_unknown.steps[0].description == "make coffee"

    def test_delegate_role_and_agent_mapping_and_audit(self):
        gov = MagicMock(spec=Governance)
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            governance=gov,
        )
        # Step with role in params
        s1 = Step(id="s1", description="architect system", params={"role": "architect"})
        s2 = Step(id="s2", description="write code", params={"role": "backend"})
        s3 = Step(id="s3", description="general task", params={})
        plan = Plan(id="p1", goal="Business ops", steps=[s1, s2, s3])

        tasks = runtime.delegate(plan)
        assert len(tasks) == 3
        assert tasks[0].agent.name == "planner"
        assert tasks[1].agent.name == "cto"
        assert tasks[2].agent.name == "default"


class TestExecutionGatesAndPolicyEnforcement:
    """Test the 5-phase execution safety gates and Lane E9 policy checks."""

    def test_gate_repair_limit_exceeded(self):
        runtime = MekongCoreRuntimeImpl(dispatcher=MagicMock(), tool_registry=MagicMock())
        runtime._repair_count = 3

        task = Task(id="t1", step=Step(id="s1", description="fix bug"), agent=AgentId("cto"))
        res = runtime.execute(task)
        assert res.error == "Max repair retries (3) exceeded"

    def test_gate_governance_forbidden(self):
        gov = MagicMock(spec=Governance)
        gov.classify.return_value = GovernanceDecision(action_class=ActionClass.FORBIDDEN, reason="Dangerous operation")
        runtime = MekongCoreRuntimeImpl(dispatcher=MagicMock(), tool_registry=MagicMock(), governance=gov)

        task = Task(id="t1", step=Step(id="s1", description="rm -rf /"), agent=AgentId("cto"))
        res = runtime.execute(task)
        assert res.metadata.get("gate_blocked") is True
        assert "Action forbidden: Dangerous operation" in res.error

    def test_gate_governance_review_required(self):
        gov = MagicMock(spec=Governance)
        gov.classify.return_value = GovernanceDecision(action_class=ActionClass.REVIEW_REQUIRED, reason="Needs human signoff")
        runtime = MekongCoreRuntimeImpl(dispatcher=MagicMock(), tool_registry=MagicMock(), governance=gov)
        task = Task(id="t1", step=Step(id="s1", description="deploy prod"), agent=AgentId("cto"))

        # Approval rejected
        gov.request_approval.return_value = False
        res = runtime.execute(task)
        assert res.metadata.get("gate_blocked") is True
        assert "Action requires human approval" in res.error

        # Approval accepted
        gov.request_approval.return_value = True
        disp = MagicMock()
        disp.dispatch.return_value = {"status": "ok"}
        runtime._dispatcher = disp
        res_ok = runtime.execute(task)
        assert res_ok.error is None

    def test_gate_e9_capability_governance_and_policies(self):
        bus = MagicMock()
        gov = MagicMock(spec=Governance)
        reg = MagicMock()

        cap_obj = MagicMock(risk_level="HIGH", cost=0.05)
        bus.get.return_value = cap_obj

        meta_obj = MagicMock(
            risk_level="MEDIUM",
            allowed_tools=["db_query"],
            max_budget=0.10,
            max_iterations=2,
            approval_policy="MANUAL",
        )
        reg.get_meta_obj.return_value = meta_obj

        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            capability_bus=bus,
            governance=gov,
            agent_registry=reg,
        )

        task = Task(
            id="t1",
            step=Step(id="s1", description="query user data"),
            agent=AgentId("cto"),
            params={"capability_id": "db_query"},
        )

        # 1. Capability Forbidden
        gov.classify_risk.return_value = GovernanceDecision(action_class=ActionClass.FORBIDDEN, reason="Risk forbidden")
        res1 = runtime.execute(task)
        assert "Capability forbidden: Risk forbidden" in res1.error

        # 2. Allowed tools violation
        gov.classify_risk.return_value = GovernanceDecision(action_class=ActionClass.SAFE, reason="Safe")
        task_disallowed = Task(
            id="t2",
            step=Step(id="s2", description="shell command"),
            agent=AgentId("cto"),
            params={"capability_id": "shell_exec"},
        )
        res2 = runtime.execute(task_disallowed)
        assert "not allowed for agent 'cto'" in res2.error

        # 3. Agent Max Budget exceeded
        meta_obj.max_budget = 0.04
        res3 = runtime.execute(task)
        assert "Agent budget exceeded" in res3.error
        meta_obj.max_budget = 1.0  # restore

        # 4. Agent Max Iterations exceeded
        meta_obj.max_iterations = 1
        runtime._repair_count = 1
        res4 = runtime.execute(task)
        assert "Agent iteration cap exceeded" in res4.error
        runtime._repair_count = 0  # restore

        # 5. Approval Policy DENY
        meta_obj.approval_policy = "DENY"
        res5 = runtime.execute(task)
        assert "Agent approval policy DENY" in res5.error
        meta_obj.approval_policy = "MANUAL"  # restore

        # 6. Capability requires human approval rejected
        gov.classify_risk.return_value = GovernanceDecision(action_class=ActionClass.REVIEW_REQUIRED, reason="Needs review")
        gov.request_approval.return_value = False
        res6 = runtime.execute(task)
        assert "Capability requires human approval" in res6.error

        # 7. Successful capability execution records spend
        gov.request_approval.return_value = True
        disp = MagicMock()
        disp.dispatch.return_value = {"status": "ok"}
        runtime._dispatcher = disp
        res7 = runtime.execute(task)
        assert res7.error is None
        assert runtime._agent_spend["cto"] == pytest.approx(0.05)

    def test_gate_cost_limit_enforcement(self):
        router = MagicMock()
        router.estimate_cost.return_value = {"cost_usd": 2.50}
        disp = MagicMock()
        disp.dispatch.return_value = {"status": "ok"}

        runtime = MekongCoreRuntimeImpl(
            dispatcher=disp,
            tool_registry=MagicMock(),
            llm_router=router,
            max_cost_usd=3.0,
        )

        task = Task(id="t1", step=Step(id="s1", description="summarize logs"), agent=AgentId("cto"))
        # First execution: 2.50 <= 3.0 -> OK
        res1 = runtime.execute(task)
        assert res1.error is None
        assert runtime._spent_cost_usd == 2.50

        # Second execution: 2.50 + 2.50 = 5.00 > 3.0 -> Blocked
        res2 = runtime.execute(task)
        assert res2.metadata.get("gate_blocked") is True
        assert "Cost ceiling exceeded" in res2.error

    def test_execution_tool_registry_and_noop(self):
        tools = MagicMock()
        tools.execute.return_value = {"result": "tool-ran"}
        runtime = MekongCoreRuntimeImpl(dispatcher=None, tool_registry=tools)

        task_tool = Task(
            id="t1",
            step=Step(id="s1", description="run tool"),
            agent=AgentId("cto"),
            params={"tool": "code_search", "query": "auth"},
        )
        res = runtime.execute(task_tool)
        assert res.output == {"result": "tool-ran"}

        # Neither tool nor dispatcher
        runtime_noop = MekongCoreRuntimeImpl(dispatcher=None, tool_registry=None)
        task_noop = Task(id="t2", step=Step(id="s2", description="noop"), agent=AgentId("cli"))
        res_noop = runtime_noop.execute(task_noop)
        assert res_noop.output == {"status": "noop", "task_id": "t2"}

    def test_execution_dispatch_error_propagation_and_exception(self):
        disp = MagicMock()
        disp.dispatch.return_value = {"status": "failed", "error": "Exit code 127"}
        runtime = MekongCoreRuntimeImpl(dispatcher=disp, tool_registry=MagicMock())

        task = Task(id="t1", step=Step(id="s1", description="run shell"), agent=AgentId("cto"))
        res = runtime.execute(task)
        assert res.error == "Exit code 127"

        # Dispatcher exception caught
        disp.dispatch.side_effect = RuntimeError("network timeout")
        res_exc = runtime.execute(task)
        assert res_exc.error == "network timeout"


class TestObservationMemoryAndCommit:
    """Test observe, verify, remember, flush_session, commit, and billing."""

    def test_observe_and_verify(self):
        telemetry = MagicMock()
        runtime = MekongCoreRuntimeImpl(dispatcher=MagicMock(), tool_registry=MagicMock(), telemetry=telemetry)
        runtime._mission_id = "m-obs"

        # Result with error and estimated cost
        res = Result(task_id="t1", output="some output", error="fail", metadata={"estimated_cost": {"cost_usd": 0.01}})
        obs = runtime.observe(res)
        assert obs.metrics["has_error"] is True
        assert obs.metrics["estimated_cost"] == {"cost_usd": 0.01}
        assert len(obs.side_effects) == 1
        assert obs.side_effects[0].kind == "error"
        telemetry.emit.assert_called_with({
            "event_type": "task_completed",
            "metric": 1.0,
            "estimated_cost": {"cost_usd": 0.01},
            "mission_id": "m-obs",
        })

        # verify with empty criteria -> passed iff no error
        res_ok = Result(task_id="t2", output="success", error=None)
        obs_ok = Observation(result=res_ok)
        ver_ok = runtime.verify(obs_ok, Criteria())
        assert ver_ok.passed is True

        ver_fail = runtime.verify(obs, Criteria())
        assert ver_fail.passed is False

    def test_remember_and_flush_session(self):
        mem_store = MagicMock()
        mem_store.delete.return_value = True
        mem_sep = MagicMock()
        mem_sep.flush_session.return_value = 2

        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            memory_store=mem_store,
            memory_separation=mem_sep,
        )

        obs = Observation(result=Result(task_id="t1", output="res", error=None))
        entry = runtime.remember(obs)
        assert entry.key == "obs-t1"
        assert "obs-t1" in runtime._session_keys
        mem_store.store.assert_called_once()

        # Flush session deletes tracked keys and calls separation flush
        cleared = runtime.flush_session()
        assert cleared == 3  # 1 from store.delete + 2 from separation
        assert len(runtime._session_keys) == 0
        mem_store.prune_expired.assert_called_once()

    def test_remember_fallback_on_store_exception(self):
        mem_store = MagicMock()
        mem_store.store.side_effect = Exception("store unavailable")
        mem_sep = MagicMock()

        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            memory_store=mem_store,
            memory_separation=mem_sep,
        )

        obs = Observation(result=Result(task_id="t2", output="res", error=None))
        entry = runtime.remember(obs)
        assert entry.key == "obs-t2"
        mem_sep.store.assert_called_once()

    def test_commit_and_billing_and_telemetry(self):
        billing = MagicMock()
        telemetry = MagicMock()
        runtime = MekongCoreRuntimeImpl(
            dispatcher=MagicMock(),
            tool_registry=MagicMock(),
            billing=billing,
            telemetry=telemetry,
            agent_id="cfo",
        )
        runtime._mission_id = "m-commit"

        res = Result(task_id="t1", output="done", error=None)
        commit = runtime.commit(res)
        assert commit.result == res
        billing.record_usage.assert_called_with("cfo", 0, "default", "run")
        billing.check_quota.assert_called_with("cfo")
        telemetry.emit.assert_called_with({
            "event_type": "run_completed",
            "task_id": "t1",
            "error": None,
            "mission_id": "m-commit",
        })

        # Billing exception handled gracefully
        billing.record_usage.side_effect = Exception("billing error")
        commit2 = runtime.commit(res)
        assert commit2.id is not None


class TestTaskLoopAndDAGExecution:
    """Test task execution loop, repair strategies, DAG execution, and cancellation."""

    def test_run_task_loop_cancelled_and_repair_escalate(self):
        disp = MagicMock()
        runtime = MekongCoreRuntimeImpl(dispatcher=disp, tool_registry=MagicMock())

        task = Task(id="t1", step=Step(id="s1", description="step 1"), agent=AgentId("cto"))

        # Pre-cancelled
        runtime._cancel_requested = True
        res_cancelled = runtime._run_task_loop(task, Criteria())
        assert res_cancelled.error == "mission cancelled"
        assert res_cancelled.metadata.get("cancelled") is True
        runtime._cancel_requested = False

        # Verify failure leading to repair ESCALATE strategy. Mock repair()
        # directly so execute() runs the dispatch unimpeded.
        disp.dispatch.return_value = {"error": "syntax error"}
        runtime._verifier = MagicMock()
        runtime._verifier.verify.return_value = MagicMock(passed=False, errors=["syntax error"], checks=[])
        runtime._repair_count = 0
        runtime.repair = MagicMock(return_value=RepairAction(strategy=RepairStrategy.ESCALATE))

        res_escalated = runtime._run_task_loop(task, Criteria(checks=[CheckSpec(kind="exit_code")]))
        assert res_escalated.error == "syntax error"
        runtime.repair.assert_called()

    def test_run_dag_tasks_cancellation_propagation(self):
        s1 = Step(id="s1", description="s1")
        s2 = Step(id="s2", description="s2", dependencies=["s1"])
        t1 = Task(id="t1", step=s1, agent=AgentId("cto"))
        t2 = Task(id="t2", step=s2, agent=AgentId("cto"))

        disp = MagicMock()
        # s1 fails permanently — repair() escalates so the loop returns the
        # original failed result, which then triggers DAG cancellation of t2.
        disp.dispatch.return_value = {"error": "compile failed"}
        runtime = MekongCoreRuntimeImpl(dispatcher=disp, tool_registry=MagicMock())
        runtime._verifier = MagicMock()
        runtime._verifier.verify.return_value = MagicMock(passed=False, errors=["compile failed"], checks=[])
        runtime._repair_count = 0
        runtime.repair = MagicMock(return_value=RepairAction(strategy=RepairStrategy.ESCALATE))

        crit = Criteria(checks=[CheckSpec(kind="exit_code")])
        results = runtime._run_dag_tasks([t1, t2], crit)
        assert len(results) == 2
        assert results[0].error == "compile failed"
        assert results[1].error == "mission cancelled"
        assert results[1].metadata.get("cancelled") is True

    def test_merge_results_single_and_multiple(self):
        r1 = Result(task_id="t1", output="out1", error=None)
        assert MekongCoreRuntimeImpl._merge_results([r1]) == r1

        r2 = Result(task_id="t2", output="out2", error="failed step")
        merged = MekongCoreRuntimeImpl._merge_results([r1, r2])
        assert merged.task_id == "merged"
        assert merged.output == ["out1", "out2"]
        assert merged.error == "failed step"
        assert merged.metadata["task_count"] == 2
