"""Deterministic 20-Scenario Autonomous Runtime Trust Matrix (T01–T20).

Verifies Supreme Command #01 — Mekong CLI Autonomous Runtime Convergence:
- T01–T07: Execution Truth (H1–H7 elimination)
- T08–T09: Ticket Admission Deduplication & Immutable Mandate Integrity
- T10–T12: Fail-Closed Governance, Untrusted Content Separation & Payload-Bound Approvals
- T13–T15: Crash Lease Recovery, Non-Idempotent Safety & Transactional Report Outbox
- T16–T19: Bounded 2+1 Worker Lanes & Git Worktree Isolation
- T20: Honest Cost Accounting & Budget Exhaustion Enforcement
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from src.core.buzz_adapter import BuzzAdapter
from src.core.governance import ActionClass, Governance
from src.core.runtime_adapter import MekongCoreRuntimeImpl, Result
from src.mekongcli.core.execution import ExecutionOutcome, LocalExecutor
from src.mekongcli.core.goal_engine import (
    ExecutionTruthStatus,
    GoalEngine,
    GoalStatus,
    ImmutableMandate,
    MandateIntegrityError,
    SQLiteGoalStore,
    TaskStatus,
    WorkerLease,
    WorktreeEscapeError,
    WorktreeIsolationManager,
)
from src.opc.approval import PayloadBoundApprovalEngine
from src.opc.models import ActionPayload, ApprovalDecision, UsageRecord, UsageStage
from src.opc.usage import UsageLedger


def _make_engine(tmp_path: Path) -> tuple[SQLiteGoalStore, GoalEngine]:
    db_path = tmp_path / ".mekong" / "goals.sqlite3"
    store = SQLiteGoalStore(db_path=db_path)
    engine = GoalEngine(store=store, cwd=tmp_path, max_autonomous_workers=2)
    return store, engine


def _make_mandate(
    ticket_id: str = "tkt_100",
    source_id: str = "github_webhook",
    event_id: str = "evt_unique_999",
    cost_budget: float = 5.0,
) -> ImmutableMandate:
    return ImmutableMandate(
        ticket_id=ticket_id,
        source_id=source_id,
        event_id=event_id,
        requester="owner@mekong.vn",
        authorized_scope="/workspace",
        workspace_id="ws_default",
        mandate_version=1,
        policy_version="2026-11-01.v1",
        accepted_at="2026-11-01T00:00:00Z",
        permitted_capabilities=("invoice.read", "invoice.parse"),
        resource_boundaries=("/workspace",),
        risk_classification="LOW",
        cost_budget=cost_budget,
        retry_budget=3,
        verification_requirements="standard",
    )


def test_t01_simulated_mode_never_claims_verified_success(tmp_path: Path) -> None:
    """T01: execute_commands=False marks tasks and goal SIMULATED, never VERIFIED_SUCCESS."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Simulate deployment plan")
    finished = engine.run_goal(goal.id, verification_profile="none", execute_commands=False)

    assert finished.truth_status == ExecutionTruthStatus.SIMULATED
    assert finished.truth_status != ExecutionTruthStatus.VERIFIED_SUCCESS
    tasks = store.get_tasks(goal.id)
    assert len(tasks) > 0
    assert all(t.truth_status == ExecutionTruthStatus.SIMULATED for t in tasks)


def test_t02_nonzero_exit_code_marks_execution_failed(tmp_path: Path) -> None:
    """T02: Real command returning non-zero exit code marks task FAILED / EXECUTION_FAILED."""
    store, engine = _make_engine(tmp_path)
    fail_script = tmp_path / "fail_42.py"
    fail_script.write_text("import sys\nsys.exit(42)\n", encoding="utf-8")
    goal = engine.create_goal("Run failing shell command")
    tasks = store.get_tasks(goal.id)
    first_task = tasks[0]
    first_task.command = "python3 fail_42.py"
    first_task.max_attempts = 1
    store.save_tasks([first_task])

    finished = engine.run_goal(goal.id, verification_profile="none", execute_commands=True)
    updated_tasks = {t.id: t for t in store.get_tasks(goal.id)}

    assert updated_tasks[first_task.id].status == TaskStatus.FAILED
    assert updated_tasks[first_task.id].truth_status == ExecutionTruthStatus.EXECUTION_FAILED
    assert updated_tasks[first_task.id].exit_code == 42
    assert finished.status == GoalStatus.FAILED
    assert finished.truth_status == ExecutionTruthStatus.EXECUTION_FAILED


def test_t03_blocked_sanitizer_command_marks_execution_failed_with_reason(tmp_path: Path) -> None:
    """T03: Command blocked by CommandSanitizer (exit_code=126) fails with blocked_reason."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Run dangerous command")
    tasks = store.get_tasks(goal.id)
    first_task = tasks[0]
    first_task.command = "rm -rf /"
    first_task.max_attempts = 1
    store.save_tasks([first_task])

    finished = engine.run_goal(goal.id, verification_profile="none", execute_commands=True)
    updated = {t.id: t for t in store.get_tasks(goal.id)}[first_task.id]

    assert updated.status == TaskStatus.FAILED
    assert updated.truth_status == ExecutionTruthStatus.EXECUTION_FAILED
    assert updated.exit_code == 126
    assert updated.blocked_reason is not None
    assert finished.status == GoalStatus.FAILED


def test_t04_parallel_worker_uncaught_exception_marks_goal_failed(tmp_path: Path) -> None:
    """T04: Uncaught exception inside parallel worker marks task & goal EXECUTION_FAILED."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Parallel crash test")
    tasks = store.get_tasks(goal.id)
    first_task = tasks[0]
    first_task.command = "python3 -c 'print(1)'"
    first_task.max_attempts = 1
    store.save_tasks([first_task])

    def _exploding_outcome(
        command: str,
        cwd: Path | None = None,
        timeout_seconds: float | None = None,
        worktree_root: Path | None = None,
    ) -> ExecutionOutcome:
        raise RuntimeError("worker thread exploded")

    engine._execute_task_outcome = _exploding_outcome  # type: ignore[method-assign]
    finished = engine.run_goal_parallel(
        goal.id,
        verification_profile="none",
        execute_commands=True,
    )
    updated = {t.id: t for t in store.get_tasks(goal.id)}[first_task.id]
    assert updated.status == TaskStatus.FAILED
    assert updated.truth_status == ExecutionTruthStatus.EXECUTION_FAILED
    assert "worker thread exploded" in (updated.result_summary or "")
    assert finished.status == GoalStatus.FAILED
    assert finished.truth_status == ExecutionTruthStatus.EXECUTION_FAILED


def test_t05_upstream_failure_propagates_blocked_to_downstream_tasks(tmp_path: Path) -> None:
    """T05: Failed upstream task transitions all dependent downstream tasks to BLOCKED."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("DAG failure propagation")
    tasks = store.get_tasks(goal.id)
    assert len(tasks) >= 2

    root_task = tasks[0]
    root_task.command = "python3 -c 'import sys; sys.exit(1)'"
    root_task.max_attempts = 1
    store.save_tasks([root_task])

    finished = engine.run_goal(goal.id, verification_profile="none", execute_commands=True)
    after_tasks = store.get_tasks(goal.id)
    downstream = [t for t in after_tasks if root_task.id in t.depends_on]
    assert len(downstream) >= 1
    for dt in downstream:
        assert dt.status == TaskStatus.BLOCKED
        assert dt.truth_status == ExecutionTruthStatus.BLOCKED
        assert dt.blocked_reason is not None
        assert root_task.id in dt.blocked_reason
    assert finished.status == GoalStatus.FAILED


def test_t06_verification_profile_none_never_reports_verified_success(tmp_path: Path) -> None:
    """T06: verification_profile='none' never produces VERIFIED_SUCCESS even if command exits 0."""
    store, engine = _make_engine(tmp_path)
    ok_script = tmp_path / "ok.py"
    ok_script.write_text("print(42)\n", encoding="utf-8")
    goal = engine.create_goal("Run command with profile none")
    tasks = store.get_tasks(goal.id)
    for t in tasks:
        t.command = "python3 ok.py"
    store.save_tasks(tasks)

    finished = engine.run_goal(goal.id, verification_profile="none", execute_commands=True)
    assert finished.truth_status == ExecutionTruthStatus.UNAVAILABLE
    assert finished.truth_status != ExecutionTruthStatus.VERIFIED_SUCCESS


def test_t07_runtime_commit_distinguishes_runtime_state_from_git_commit() -> None:
    """T07: MekongCoreRuntimeImpl.commit() reports runtime_state_commit when git_sha is absent."""
    rt = MekongCoreRuntimeImpl(dispatcher=None, tool_registry=None)
    rec_state = rt.commit(Result(task_id="t1", output="ok", metadata={}))
    assert rec_state.commit_kind == "runtime_state_commit"
    assert rec_state.git_sha is None

    valid_sha = "284f85a520000000000000000000000000000000"
    rec_git = rt.commit(Result(task_id="t2", output="ok", metadata={"git_sha": valid_sha}))
    assert rec_git.commit_kind == "git_commit"
    assert rec_git.git_sha == valid_sha


def test_t08_duplicate_ticket_intake_deduplicated_idempotently(tmp_path: Path) -> None:
    """T08: Duplicate (source_id, event_id) webhook intake is deduplicated in SQLiteGoalStore."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Process invoice #100")
    mandate1 = _make_mandate(
        ticket_id="tkt_100",
        source_id="github_webhook",
        event_id="evt_unique_999",
    )
    res1 = store.admit_ticket(goal.id, mandate1)
    assert res1["deduplicated"] is False
    assert res1["ticket_id"] == "tkt_100"

    mandate_dup = _make_mandate(
        ticket_id="tkt_200_duplicate",
        source_id="github_webhook",
        event_id="evt_unique_999",
    )
    res2 = store.admit_ticket(goal.id, mandate_dup)
    assert res2["deduplicated"] is True
    assert res2["ticket_id"] == "tkt_100"


def test_t09_immutable_mandate_blocks_worker_tampering(tmp_path: Path) -> None:
    """T09: Worker attempt to mutate ImmutableMandate is blocked by trigger & HMAC check."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Audit tax report")
    mandate = _make_mandate(
        ticket_id="tkt_mandate_1",
        source_id="cli",
        event_id="evt_m1",
        cost_budget=2.5,
    )
    store.admit_ticket(goal.id, mandate)
    verified = store.verify_mandate_integrity("tkt_mandate_1")
    assert verified.verify_hash() is True

    with pytest.raises(MandateIntegrityError):
        store.attempt_worker_mandate_mutation(
            "tkt_mandate_1",
            cost_budget=9999.0,
            permitted_capabilities=("tax.read", "shell.exec"),
        )
    assert store.verify_mandate_integrity("tkt_mandate_1").cost_budget == 2.5


def test_t10_governance_classify_risk_fails_closed_on_unknown_risk(tmp_path: Path) -> None:
    """T10: Governance.classify_risk() defaults unknown/empty risk levels to FORBIDDEN."""
    gov = Governance(audit_path=str(tmp_path / "audit.yaml"))
    for bad_risk in ("", "   ", "UNKNOWN_TIER", "SUPER_SAFE_BYPASS", "EXTREME"):
        decision = gov.classify_risk(bad_risk)
        assert decision.action_class == ActionClass.FORBIDDEN


def test_t11_untrusted_content_cannot_escalate_capabilities(tmp_path: Path) -> None:
    """T11: Untrusted content (issue comment / log output) attempting non-low risk is DENIED."""
    gov = Governance(audit_path=str(tmp_path / "audit.yaml"))
    decision = gov.evaluate_ticket_action(
        actor="worker_agent_1",
        capability="config.modify",
        resource_scope="/workspace/src",
        risk_level="MEDIUM",
        mandate_capabilities=("config.modify", "file.read"),
        mandate_boundaries=("/workspace",),
        untrusted_context=True,
    )
    assert decision.decision == "DENY"
    assert "Untrusted content" in decision.decision_reason


def test_t12_destructive_capability_requires_single_use_payload_bound_token(tmp_path: Path) -> None:
    """T12: HIGH-risk action requires valid, non-tampered, single-use ApprovalToken."""
    gov = Governance(audit_path=str(tmp_path / "audit.yaml"))
    approval_engine = PayloadBoundApprovalEngine()
    now = int(time.time())
    payload = ActionPayload(
        principal="owner@mekong.vn",
        capability="deploy.prod",
        connector="cloudflare",
        recipient="prod-worker",
        content="deploy v6.0.1",
        parameters={"env": "production"},
        attachments=(),
        budget_amount="1.00",
        budget_currency="USD",
        expires_at=now + 3600,
    )

    # 1. Without token -> APPROVAL_REQUIRED
    d_missing = gov.evaluate_ticket_action(
        actor="worker_1",
        capability="deploy.prod",
        resource_scope="/workspace/deploy",
        risk_level="HIGH",
        mandate_capabilities=("deploy.prod",),
        mandate_boundaries=("/workspace",),
        action_payload=payload,
        approval_token=None,
        approval_engine=approval_engine,
    )
    assert d_missing.decision == "APPROVAL_REQUIRED"

    # 2. Issue token and tamper with payload -> DENY
    token = approval_engine.issue_token(
        run_id="run_01",
        payload=payload,
        decision=ApprovalDecision.APPROVE,
        custom_ttl=600,
    )
    tampered_payload = ActionPayload(
        principal="owner@mekong.vn",
        capability="deploy.prod",
        connector="cloudflare",
        recipient="prod-worker",
        content="deploy backdoor",
        parameters={"env": "production"},
        attachments=(),
        budget_amount="1.00",
        budget_currency="USD",
        expires_at=now + 3600,
    )
    d_tampered = gov.evaluate_ticket_action(
        actor="worker_1",
        capability="deploy.prod",
        resource_scope="/workspace/deploy",
        risk_level="HIGH",
        mandate_capabilities=("deploy.prod",),
        mandate_boundaries=("/workspace",),
        action_payload=tampered_payload,
        approval_token=token,
        approval_engine=approval_engine,
    )
    assert d_tampered.decision == "DENY"

    # 3. Valid token first use -> ALLOW
    d_allow = gov.evaluate_ticket_action(
        actor="worker_1",
        capability="deploy.prod",
        resource_scope="/workspace/deploy",
        risk_level="HIGH",
        mandate_capabilities=("deploy.prod",),
        mandate_boundaries=("/workspace",),
        action_payload=payload,
        approval_token=token,
        approval_engine=approval_engine,
    )
    assert d_allow.decision == "ALLOW"

    # 4. Replay same token -> DENY
    d_replay = gov.evaluate_ticket_action(
        actor="worker_1",
        capability="deploy.prod",
        resource_scope="/workspace/deploy",
        risk_level="HIGH",
        mandate_capabilities=("deploy.prod",),
        mandate_boundaries=("/workspace",),
        action_payload=payload,
        approval_token=token,
        approval_engine=approval_engine,
    )
    assert d_replay.decision == "DENY"


def test_t13_orphaned_idempotent_running_task_recovers_on_resume(tmp_path: Path) -> None:
    """T13: Orphaned RUNNING task with expired lease & is_idempotent=True recovers & completes."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Recoverable idempotent goal")
    tasks = store.get_tasks(goal.id)
    t0 = tasks[0]
    t0.status = TaskStatus.RUNNING
    t0.truth_status = ExecutionTruthStatus.RUNNING
    t0.is_idempotent = True
    t0.side_effect_uncertain = False
    t0.attempts = 1
    t0.max_attempts = 3
    store.save_tasks([t0])

    now = time.time()
    store.acquire_worker_lease(
        WorkerLease(
            worker_id="dead_worker_1",
            lane_kind="AUTONOMOUS",
            ticket_id=goal.id,
            task_id=t0.id,
            lease_expires_at=now - 10.0,
            heartbeat_at=now - 20.0,
            attempt_no=1,
            is_idempotent=True,
            side_effect_uncertain=False,
        ),
        now=now,
    )

    reconciled = store.reconcile_orphaned_running_tasks(goal.id, now=now)
    assert len(reconciled) == 1
    assert reconciled[0].truth_status == ExecutionTruthStatus.RETRY_WAIT

    resumed_task = {t.id: t for t in store.get_tasks(goal.id)}[t0.id]
    assert resumed_task.status == TaskStatus.PENDING
    assert resumed_task.truth_status == ExecutionTruthStatus.RETRY_WAIT

    resumed_goal = engine.resume_goal(goal.id, verification_profile="none", execute_commands=False, now=now)
    assert resumed_goal.status == GoalStatus.SATISFIED
    assert resumed_goal.truth_status == ExecutionTruthStatus.SIMULATED


def test_t14_orphaned_non_idempotent_task_halts_for_approval(tmp_path: Path) -> None:
    """T14: Orphaned RUNNING task with is_idempotent=False transitions to WAITING_APPROVAL."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Non-idempotent payment goal")
    tasks = store.get_tasks(goal.id)
    t0 = tasks[0]
    t0.status = TaskStatus.RUNNING
    t0.truth_status = ExecutionTruthStatus.RUNNING
    t0.is_idempotent = False
    t0.side_effect_uncertain = True
    t0.attempts = 1
    t0.max_attempts = 3
    store.save_tasks([t0])

    now = time.time()
    store.acquire_worker_lease(
        WorkerLease(
            worker_id="dead_worker_2",
            lane_kind="AUTONOMOUS",
            ticket_id=goal.id,
            task_id=t0.id,
            lease_expires_at=now - 10.0,
            heartbeat_at=now - 20.0,
            attempt_no=1,
            is_idempotent=False,
            side_effect_uncertain=True,
        ),
        now=now,
    )

    resumed_goal = engine.resume_goal(goal.id, verification_profile="none", execute_commands=False, now=now)
    resumed_task = {t.id: t for t in store.get_tasks(goal.id)}[t0.id]
    assert resumed_task.status == TaskStatus.BLOCKED
    assert resumed_task.truth_status == ExecutionTruthStatus.WAITING_APPROVAL
    assert resumed_goal.status == GoalStatus.BLOCKED
    assert resumed_goal.truth_status == ExecutionTruthStatus.WAITING_APPROVAL


def test_t15_transactional_report_outbox_deduplication_and_dead_letter(tmp_path: Path) -> None:
    """T15: BuzzAdapter persists to report_outbox, deduplicates, and dead-letters after max_attempts."""
    store, _ = _make_engine(tmp_path)
    failing_calls: list[str] = []

    def _failing_transport(url: str, payload: dict[str, Any]) -> int:
        failing_calls.append(url)
        return 503

    adapter = BuzzAdapter(transport=_failing_transport, outbox_store=store)
    res1 = adapter.send_update(
        "in_progress",
        {"step": 1},
        callback_url="https://buzz.example.com/hook",
        ticket_id="tkt_outbox_1",
        idempotency_key="idem_fixed_01",
        max_attempts=2,
    )
    assert res1["deduplicated"] is False
    assert res1["delivery_status"] == "FAILED_RETRYABLE"
    assert res1["attempts"] == 1

    # Duplicate idempotency_key -> deduplicated without re-enqueueing a new row
    res_dup = adapter.send_update(
        "in_progress",
        {"step": 1},
        callback_url="https://buzz.example.com/hook",
        ticket_id="tkt_outbox_1",
        idempotency_key="idem_fixed_01",
        max_attempts=2,
    )
    assert res_dup["deduplicated"] is True
    assert res_dup["outbox_id"] == res1["outbox_id"]

    # Retry delivery a second time -> hits max_attempts=2 -> transitions to DEAD_LETTER
    res_dlq = store.process_outbox_delivery(res1["outbox_id"], _failing_transport)
    assert res_dlq["delivery_status"] == "DEAD_LETTER"
    assert res_dlq["attempts"] == 2


def test_t16_autonomous_worker_concurrency_cap_enforced(tmp_path: Path) -> None:
    """T16: 3rd autonomous worker lease request is rejected while 2 active leases are held."""
    store, _ = _make_engine(tmp_path)
    now = time.time()
    assert store.acquire_worker_lease(
        WorkerLease(
            worker_id="worker_1",
            lane_kind="AUTONOMOUS",
            ticket_id="tkt_1",
            task_id="task_1",
            lease_expires_at=now + 120.0,
            heartbeat_at=now,
        ),
        now=now,
    )
    assert store.acquire_worker_lease(
        WorkerLease(
            worker_id="worker_2",
            lane_kind="AUTONOMOUS",
            ticket_id="tkt_1",
            task_id="task_2",
            lease_expires_at=now + 120.0,
            heartbeat_at=now,
        ),
        now=now,
    )
    # 3rd autonomous lease must be rejected
    assert (
        store.acquire_worker_lease(
            WorkerLease(
                worker_id="worker_3",
                lane_kind="AUTONOMOUS",
                ticket_id="tkt_1",
                task_id="task_3",
                lease_expires_at=now + 120.0,
                heartbeat_at=now,
            ),
            now=now,
        )
        is False
    )


def test_t17_operator_control_lane_executes_when_autonomous_saturated(tmp_path: Path) -> None:
    """T17: Reserved OPERATOR_CONTROL lane executes immediately while 2 autonomous workers are saturated."""
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Goal to inspect and cancel")
    now = time.time()

    # Saturate both autonomous worker slots
    assert store.acquire_worker_lease(
        WorkerLease(
            worker_id="w1",
            lane_kind="AUTONOMOUS",
            ticket_id=goal.id,
            task_id="t1",
            lease_expires_at=now + 300.0,
            heartbeat_at=now,
        ),
        now=now,
    )
    assert store.acquire_worker_lease(
        WorkerLease(
            worker_id="w2",
            lane_kind="AUTONOMOUS",
            ticket_id=goal.id,
            task_id="t2",
            lease_expires_at=now + 300.0,
            heartbeat_at=now,
        ),
        now=now,
    )

    status_resp = engine.execute_operator_lane("status", lambda: engine.status(goal.id), ticket_id=goal.id)
    assert status_resp["goal"]["id"] == goal.id
    assert len(store.list_active_leases("AUTONOMOUS", now=now)) == 2

    cancelled = engine.execute_operator_lane("cancel", lambda: engine.cancel_goal(goal.id), ticket_id=goal.id)
    assert cancelled.status == GoalStatus.CANCELLED
    assert cancelled.truth_status == ExecutionTruthStatus.CANCELLED


def test_t18_concurrent_worktree_isolation_and_deterministic_cleanup(tmp_path: Path) -> None:
    """T18: WorktreeIsolationManager isolates concurrent task workspaces and cleans up deterministically."""
    wt_manager = WorktreeIsolationManager(repo_root=tmp_path)
    path_a = wt_manager.allocate("tkt_iso", "task_a")
    path_b = wt_manager.allocate("tkt_iso", "task_b")
    try:
        assert path_a != path_b
        assert path_a.exists()
        assert path_b.exists()
        (path_a / "output.txt").write_text("worker A", encoding="utf-8")
        (path_b / "output.txt").write_text("worker B", encoding="utf-8")
        assert (path_a / "output.txt").read_text(encoding="utf-8") == "worker A"
        assert (path_b / "output.txt").read_text(encoding="utf-8") == "worker B"
    finally:
        wt_manager.cleanup(path_a)
        wt_manager.cleanup(path_b)

    assert not path_a.exists()
    assert not path_b.exists()


def test_t19_worktree_path_escape_blocked(tmp_path: Path) -> None:
    """T19: Path escape attempts (../outside) are blocked by WorktreeIsolationManager & LocalExecutor."""
    wt_manager = WorktreeIsolationManager(repo_root=tmp_path)
    wt_path = wt_manager.allocate("tkt_sec", "task_escape")
    try:
        with pytest.raises(WorktreeEscapeError):
            wt_manager.validate_path_within_worktree(wt_path, "../outside_secret.txt")

        executor = LocalExecutor(cwd=wt_path, strict_mode=True, worktree_root=wt_path)
        res = executor.run("cat ../outside_secret.txt")
        assert res.exit_code == 126
        assert "escape" in (res.blocked_reason or res.stderr).lower() or "blocked" in (res.blocked_reason or res.stderr).lower()

        res_flag = executor.run("grep --file=/etc/passwd root")
        assert res_flag.exit_code == 126
        assert "outside isolated worktree" in (res_flag.blocked_reason or res_flag.stderr).lower()
    finally:
        wt_manager.cleanup(wt_path)


def test_t20_honest_cost_accounting_and_budget_exhaustion(tmp_path: Path) -> None:
    """T20: Unmeasured costs report actual_cost=None & cost_status='UNKNOWN' (never 0.0), and budget cap blocks overrun."""
    ledger = UsageLedger(tmp_path / ".mekong" / "usage.sqlite3")
    ledger.record_usage(
        UsageRecord(
            event_id="ev_unk_1",
            run_id="run_unmeasured",
            attempt=1,
            stage=UsageStage.UNKNOWN,
            provider="local_subprocess",
            model="shell",
            tokens=None,
            tool_fee=None,
            amount=None,
            currency="USD",
            payer="workspace",
            pricing_source="unmeasured",
            created_at=int(time.time()),
        )
    )
    summary = ledger.summarize_cost_accounting("run_unmeasured")
    assert summary.actual_cost is None
    assert summary.estimated_cost is None
    assert summary.cost_status == "UNKNOWN"

    # Budget exhaustion check in SQLiteGoalStore & GoalEngine
    store, engine = _make_engine(tmp_path)
    goal = engine.create_goal("Strict budget run")
    mandate = _make_mandate(
        ticket_id="tkt_budget_cap",
        source_id="cli",
        event_id="evt_budget_1",
        cost_budget=1.00,
    )
    store.admit_ticket(goal.id, mandate)
    res_unmeasured = store.record_ticket_cost(
        "tkt_budget_cap",
        measured_tokens=None,
        estimated_tokens=200,
        actual_cost=None,
        estimated_cost=None,
    )
    assert res_unmeasured["actual_cost"] is None
    assert res_unmeasured["cost_status"] == "UNKNOWN"

    store.record_ticket_cost(
        "tkt_budget_cap",
        measured_tokens=5000,
        estimated_tokens=None,
        actual_cost=1.50,
        estimated_cost=None,
    )
    with pytest.raises(RuntimeError, match="cost budget exhausted"):
        engine.run_goal(goal.id, verification_profile="none", execute_commands=False, ticket_id="tkt_budget_cap")
