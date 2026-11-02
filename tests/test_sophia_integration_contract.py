# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for Sophia Integration Contract v1.0 (`mekong.sophia.execution_contract.v1`)."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import pytest

from src.core.buzz_adapter import BuzzSecurityError
from src.core.contracts import (
    CONTRACT_VERSION,
    SOPHIA_CONTRACT_OPERATIONS,
    SophiaContractValidationError,
    SophiaExecutionContractV1,
    SophiaOutcomeEnvelope,
    validate_sophia_handoff_fixture,
)
from src.mekongcli.core.goal_engine.models import (
    ExecutionTruthStatus,
    WorkerLease,
)
from src.mekongcli.core.goal_engine.service import GoalEngine
from src.mekongcli.core.goal_engine.store import SQLiteGoalStore


def _make_contract(tmp_path: Path, transport: Any | None = None) -> tuple[SQLiteGoalStore, GoalEngine, SophiaExecutionContractV1]:
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "main.py").write_text("import sys\nprint('smoke ok')\n", encoding="utf-8")
    (tmp_path / "write_artifact.py").write_text(
        "from pathlib import Path\nPath('artifact_out.txt').write_text('hello sophia', encoding='utf-8')\nprint('artifact written')\n",
        encoding="utf-8",
    )
    db_path = tmp_path / ".mekong" / "goals.sqlite3"
    store = SQLiteGoalStore(db_path)
    engine = GoalEngine(cwd=tmp_path, store=store)
    contract = SophiaExecutionContractV1(
        store=store,
        engine=engine,
        transport=transport or (lambda _url, _payload: 200),
    )
    return store, engine, contract


def test_sophia_contract_version_and_10_operations_exposed() -> None:
    assert CONTRACT_VERSION == "mekong.sophia.execution_contract.v1"
    assert len(SOPHIA_CONTRACT_OPERATIONS) == 10
    for op in SOPHIA_CONTRACT_OPERATIONS:
        assert hasattr(SophiaExecutionContractV1, op)


def test_sophia_submit_task_get_ticket_get_status_and_idempotency(tmp_path: Path) -> None:
    _, _, contract = _make_contract(tmp_path)
    req_payload = {
        "contract_version": CONTRACT_VERSION,
        "source_id": "sophia_factory",
        "event_id": "evt_sophia_001",
        "requester": "sophia_orchestrator",
        "goal": "Generate campaign landing scaffold",
        "verification_profile": "smoke",
        "execute_immediately": True,
        "simulated_run": False,
        "isolate_worktree": True,
        "commands_by_role": {
            "architect": "python3 write_artifact.py",
            "backend": "python3 -m src.main --help",
            "qa": "python3 -m src.main --help",
        },
        "callback_url": "https://buzz.example/sophia/callback",
    }

    res1 = contract.submit_task(req_payload)
    assert res1["contract_version"] == CONTRACT_VERSION
    assert res1["deduplicated"] is False
    ticket_id = res1["ticket"]["ticket_id"]

    status1 = res1["status"]
    assert status1["truth_status"] == ExecutionTruthStatus.VERIFIED_SUCCESS.value
    assert status1["execution_outcome"] == "EXECUTED"
    assert status1["verification_outcome"] == "VERIFIED_SUCCESS"
    assert status1["delivery_outcome"] == "SENT"
    assert status1["business_outcome"] == "NOT_EVALUATED"
    assert status1["verified_success_claim_permitted"] is True

    # Replay identical (source_id, event_id) -> deduplicated
    res2 = contract.submit_task(req_payload)
    assert res2["deduplicated"] is True
    assert res2["ticket"]["ticket_id"] == ticket_id

    # Verify get_verification_evidence and get_artifacts
    evidence = contract.get_verification_evidence(ticket_id)
    assert evidence["verification_run"]["passed"] is True
    assert all(t["truth_status"] == "VERIFIED_SUCCESS" for t in evidence["tasks"])

    artifacts = contract.get_artifacts(ticket_id)
    assert artifacts["manifest_count"] >= 1
    assert any(a["relative_path"] == "artifact_out.txt" for a in artifacts["artifacts"])

    # Verify list_durable_reports and get_cost_usage
    reports = contract.list_durable_reports(ticket_id=ticket_id)
    assert reports["count"] == 1
    assert reports["reports"][0]["delivery_status"] == "SENT"

    cost = contract.get_cost_usage(ticket_id)
    assert cost["cost_status"] == "UNKNOWN"
    assert cost["actual_cost"] is None


def test_sophia_simulated_and_unverified_runs_forbid_verified_claim(tmp_path: Path) -> None:
    _, _, contract = _make_contract(tmp_path)
    res_sim = contract.submit_task(
        {
            "source_id": "sophia_factory",
            "event_id": "evt_sophia_sim_01",
            "requester": "sophia_orchestrator",
            "goal": "Dry run campaign plan",
            "verification_profile": "smoke",
            "execute_immediately": True,
            "simulated_run": True,
        }
    )
    status_sim = res_sim["status"]
    assert status_sim["simulated"] is True
    assert status_sim["execution_outcome"] == "SIMULATED"
    assert status_sim["verified_success_claim_permitted"] is False

    with pytest.raises(SophiaContractValidationError):
        SophiaOutcomeEnvelope(
            ticket_id="tkt_1",
            goal_id="goal_1",
            truth_status="SIMULATED",
            simulated=True,
            execution_outcome="SIMULATED",
            verification_outcome="NOT_RUN",
            delivery_outcome="NOT_REQUESTED",
            verified_success_claim_permitted=True,
        )


def test_sophia_approval_cancel_and_resume_reconcile_operations(tmp_path: Path) -> None:
    store, _, contract = _make_contract(tmp_path)
    res = contract.submit_task(
        {
            "source_id": "sophia_factory",
            "event_id": "evt_sophia_ctrl_01",
            "requester": "sophia_orchestrator",
            "goal": "Controlled deployment task",
            "execute_immediately": False,
        }
    )
    ticket_id = res["ticket"]["ticket_id"]
    goal_id = res["ticket"]["goal_id"]

    approval_res = contract.report_approval_required(
        ticket_id,
        reason="external_publish_requires_founder_signoff",
    )
    assert approval_res["truth_status"] == ExecutionTruthStatus.WAITING_APPROVAL.value
    assert contract.get_status(ticket_id)["verification_outcome"] == "WAITING_APPROVAL"

    # Simulate an expired lease on a RUNNING task and run resume_reconcile
    tasks = store.get_tasks(goal_id)
    first_task = tasks[0]
    first_task.status = first_task.status.__class__("running")
    store.save_tasks([first_task])
    now = time.time()
    store.acquire_worker_lease(
        WorkerLease(
            worker_id="w_sophia_1",
            lane_kind="AUTONOMOUS",
            ticket_id=ticket_id,
            task_id=first_task.id,
            lease_expires_at=now - 10.0,
            heartbeat_at=now - 20.0,
            is_idempotent=False,
            side_effect_uncertain=True,
        ),
        now=now - 30.0,
    )
    reconcile_res = contract.resume_reconcile(ticket_id, now=now)
    assert len(reconcile_res["reconciled"]) == 1

    cancel_res = contract.request_cancel(ticket_id, reason="aborted_by_founder")
    assert cancel_res["cancelled"] is True
    assert contract.get_status(ticket_id)["execution_outcome"] == "CANCELLED"


def test_sophia_handoff_fixture_validation_rejects_forgery_and_ssrf(tmp_path: Path) -> None:
    _, _, contract = _make_contract(tmp_path)

    with pytest.raises(SophiaContractValidationError):
        validate_sophia_handoff_fixture({"contract_version": "wrong.v0"})

    with pytest.raises(BuzzSecurityError):
        validate_sophia_handoff_fixture(
            {
                "contract_version": CONTRACT_VERSION,
                "source_id": "sophia",
                "event_id": "evt_ssrf",
                "goal": "Test SSRF",
                "callback_url": "http://169.254.169.254/latest/meta-data/",
            }
        )

    with pytest.raises(BuzzSecurityError):
        contract.submit_task(
            {
                "source_id": "sophia",
                "event_id": "evt_unauth_cap",
                "requester": "sophia_orchestrator",
                "goal": "Escalation attempt",
                "requested_capabilities": ["root_shell_exec"],
            }
        )
