# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Wave-1 acceptance tests for the *shared execution spine*.

``tests/test_promise_finance_ops.py`` proves the business numbers of the
Vietnamese finance operations. This file proves the enforcement around them —
the part that decides whether a green result can be trusted at all:

* authorization is per principal, per role, per cluster, per command and is
  checked before anything is persisted;
* workspaces are isolated for runs, engine databases, evidence facts and gates;
* duplicate submission replays the persisted job instead of re-executing;
* approvals are bound to a payload digest, expire, cannot be replayed and cannot
  be moved to another run;
* a crash leaves an honest state: uncertain external effects become
  ``NEEDS_RECONCILIATION`` and require provider proof to close;
* receipts are signed, and verification distinguishes *handler ran* from
  *artifact integrity* from *business conditions met*;
* milestone gates are measured from persisted facts, so running commands alone
  never seals a gate;
* restart re-reads persisted state.

Every assertion is on measured state (persisted rows, returned statuses,
recomputed digests) — never on a handler's own success flag.
"""

from __future__ import annotations

import sqlite3
import time

import pytest

from src.core.promise.evidence import EvidenceIntegrityError
from src.core.promise.identity import (
    PERM_EXECUTE_IRREVERSIBLE,
    PermissionDeniedError,
    Principal,
    authorize_execution,
)
from src.core.promise.jobs import (
    STATUS_AWAITING_APPROVAL,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_NEEDS_RECONCILIATION,
    STATUS_NOT_IMPLEMENTED,
    STATUS_QUEUED,
    STATUS_REJECTED,
    STATUS_RUNNING,
    new_run_id,
)
from src.core.promise.service import PromiseError, PromiseRunService
from src.core.promise.signing import EvidenceSigner, sha256_of

pytestmark = pytest.mark.unit

WS_A = "ws-spine-a"
WS_B = "ws-spine-b"
SELLER_MST = "0300588569"


def principal(workspace_id: str, *roles: str, tier: str = "SCALE", **kwargs) -> Principal:
    return Principal(
        principal_id=f"usr-{roles[0]}-{workspace_id}",
        workspace_id=workspace_id,
        roles=roles or ("operator",),
        tier=tier,
        display_name=roles[0].title(),
        **kwargs,
    )


FOUNDER = principal(WS_A, "founder")
OPERATOR = principal(WS_A, "operator")
APPROVER = principal(WS_A, "approver")
VIEWER = principal(WS_A, "viewer")
AUDITOR = principal(WS_A, "auditor")
OUTSIDER = principal(WS_B, "founder")
CSUITE_ONLY = principal(WS_A, "operator", cluster_allowlist=("csuite",))
THUE_DENIED = principal(WS_A, "founder", command_denylist=("thue",))


@pytest.fixture()
def service(tmp_path, monkeypatch):
    # A configured signer: receipts are HMAC-signed and verifiable in these tests.
    monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "spine-test-signing-key")
    return PromiseRunService(
        state_dir=tmp_path / "state",
        workspace_root=tmp_path,
        code_version_override="test-code-version",
    )


@pytest.fixture()
def state_dir(tmp_path):
    return tmp_path / "state"


def run(service, who, command, subcommand, params, **kwargs):
    return service.submit(who, command, params, subcommand=subcommand, **kwargs).to_dict()


def checks(outcome):
    return {c["check"]: c for c in (outcome.get("verification") or {}).get("checks", [])}


def assert_completed(outcome, *names):
    assert outcome["status"] == STATUS_COMPLETED, (outcome.get("error_message"), outcome.get("output"))
    assert (outcome.get("verification") or {}).get("business_conditions_met") is True
    present = checks(outcome)
    for name in names:
        assert name in present, f"postcondition '{name}' did not run"
        assert present[name]["status"] == "PASSED", present[name]["detail"]


def revenue_rows(service, workspace_id):
    return service.evidence.query("revenue_transactions", workspace_id)


def issue_invoice(service, who=FOUNDER, amount=20_000_000):
    invoice = run(service, who, "ke-toan", "create_invoice",
                  {"amount": amount, "buyer": "Công ty ABC", "seller_tax_code": SELLER_MST})
    assert_completed(invoice, "invoice_tt78_structure", "record_persisted")
    return invoice["output"]["invoice_id"]


def record_tax_accounting(service, who=FOUNDER, amount=20_000_000):
    """The L3 gate also measures a tax/accounting record, not just the payment."""
    outcome = run(service, who, "thue", "gtgt",
                  {"amount": amount, "rate": 10, "tax_period": "2026-10-01"})
    assert_completed(outcome, "vat_dual_path")
    return outcome


def pause_reconciliation(service, invoice_id, who=FOUNDER, bank_tx_id="MB-SPINE-0001",
                         amount_vnd=20_000_000, **kwargs):
    """Submit the revenue-asserting operation; it must stop at founder approval."""
    paused = run(service, who, "vietqr", "reconcile_payment", {
        "bank_tx_id": bank_tx_id, "amount_vnd": amount_vnd, "memo": "HD SPINE 000001",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00001",
        "invoice_ref": invoice_id,
    }, **kwargs)
    assert paused["status"] == STATUS_AWAITING_APPROVAL, paused
    assert paused["error_code"] == "APPROVAL_REQUIRED"
    assert paused["receipt"] is None
    assert paused["approval_request"]["approval_token_id"]
    # Nothing was written before the approval: no revenue fact, no receipt.
    assert revenue_rows(service, who.workspace_id) == []
    return paused


def decide(service, who, paused, decision="approve", notes="sao kê MB 27/10/2026"):
    outcome = service.decide_approval(
        who, paused["run_id"], paused["approval_request"]["approval_token_id"], decision,
        notes=notes,
    )
    return outcome.to_dict()


# ---------------------------------------------------------------------------
# 1. Validation: bad input is refused before a handler runs
# ---------------------------------------------------------------------------


def test_invalid_input_is_refused_before_dispatch(service):
    outcome = run(service, FOUNDER, "thue", "tncn",
                  {"monthly_income": -5_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    assert outcome["status"] == STATUS_FAILED
    assert outcome["error_code"] == "INPUT_INVALID"
    assert (outcome.get("verification") or {}).get("handler_ran") is not True
    assert outcome["receipt"] is None
    # The refusal is itself persisted, so it is auditable rather than silent.
    failed = service.list_runs(FOUNDER, status=STATUS_FAILED)
    assert [j["run_id"] for j in failed] == [outcome["run_id"]]
    assert failed[0]["error_code"] == "INPUT_INVALID"
    assert service.evidence.get_evidence_for_run(outcome["run_id"], WS_A) == []


def test_schema_rejects_unknown_properties_wrong_types_and_illegal_enums(service):
    unknown = run(service, FOUNDER, "thue", "tncn",
                  {"monthly_income": 35_000_000, "shell": "rm -rf /"})
    assert unknown["status"] == STATUS_FAILED
    assert unknown["error_code"] == "INPUT_INVALID"

    wrong_type = run(service, FOUNDER, "thue", "tncn",
                     {"monthly_income": 35_000_000, "dependents": "many"})
    assert wrong_type["status"] == STATUS_FAILED
    assert wrong_type["error_code"] == "INPUT_INVALID"

    illegal_rate = run(service, FOUNDER, "thue", "gtgt",
                       {"amount": 20_000_000, "rate": 7, "tax_period": "2026-10-01"})
    assert illegal_rate["status"] == STATUS_FAILED
    assert illegal_rate["error_code"] == "INPUT_INVALID"


def test_unbound_advertised_command_is_reported_not_implemented(service):
    """An advertised command with no operation binding must not fake success."""
    outcome = run(service, FOUNDER, "adminlaw", "status", {})
    assert outcome["status"] == STATUS_NOT_IMPLEMENTED
    assert outcome["error_code"] == "NO_OPERATION_BINDING"
    assert outcome["maturity_tier"] == "NOT_IMPLEMENTED"
    assert outcome["receipt"] is None
    assert "docs/cli-promise" in (outcome["error_message"] or "")

    persisted = service.list_runs(FOUNDER, status=STATUS_NOT_IMPLEMENTED)
    assert [j["run_id"] for j in persisted] == [outcome["run_id"]]


# ---------------------------------------------------------------------------
# 2. Authorization: role, cluster, command and effect checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("who", [VIEWER, AUDITOR, APPROVER])
def test_execute_is_denied_without_the_execute_permission(service, who):
    with pytest.raises(PermissionDeniedError) as excinfo:
        run(service, who, "thue", "tncn", {"monthly_income": 35_000_000, "dependents": 1})
    assert excinfo.value.code == "MISSING_PERMISSION"
    # Denied before anything is persisted — no run row is attributed to them.
    assert service.list_runs(who) == []


def test_readers_can_read_but_not_execute_or_approve(service):
    completed = run(service, FOUNDER, "thue", "tncn",
                    {"monthly_income": 35_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    assert_completed(completed, "pit_dual_path")

    assert service.get_run(AUDITOR, completed["run_id"])["job"]["status"] == STATUS_COMPLETED
    assert service.list_runs(VIEWER, command_id="thue")[0]["run_id"] == completed["run_id"]

    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    with pytest.raises(PermissionDeniedError) as excinfo:
        decide(service, OPERATOR, paused)
    assert excinfo.value.code == "MISSING_PERMISSION"
    # The run is still waiting: a denied approver did not resume it.
    assert service.get_run(FOUNDER, paused["run_id"])["job"]["status"] == STATUS_AWAITING_APPROVAL


@pytest.mark.parametrize("who,code", [(OPERATOR, "MISSING_PERMISSION"), (VIEWER, "MISSING_PERMISSION")])
def test_gate_reconciliation_requires_a_gate_approver(service, who, code):
    with pytest.raises(PermissionDeniedError) as excinfo:
        service.reconcile_gate(who, "first-revenue")
    assert excinfo.value.code == code
    # A designated approver may re-measure, but measuring is not sealing.
    measured = service.reconcile_gate(APPROVER, "first-revenue")
    assert measured["status"] != "SEALED_VERIFIED"
    assert measured["reconciled_by"] == APPROVER.principal_id


def test_cluster_allowlist_is_enforced(service):
    with pytest.raises(PermissionDeniedError) as excinfo:
        run(service, CSUITE_ONLY, "thue", "tncn", {"monthly_income": 35_000_000})
    assert excinfo.value.code == "CLUSTER_NOT_ENABLED"
    # The same principal may run a command inside its enabled cluster.
    allowed = service.capabilities(CSUITE_ONLY)
    assert allowed["summary"]["total_command_groups"] == 197


def test_command_denylist_is_enforced(service):
    with pytest.raises(PermissionDeniedError) as excinfo:
        run(service, THUE_DENIED, "thue", "tncn", {"monthly_income": 35_000_000})
    assert excinfo.value.code == "COMMAND_DENIED"
    # A denylisted command does not disable the rest of the workspace.
    other = run(service, THUE_DENIED, "bhxh", "calculate",
                {"salary": 25_000_000, "region": 1, "contribution_period": "2026-08-01"})
    assert_completed(other, "bhxh_dual_path")


def test_irreversible_effects_need_an_explicit_permission():
    """Unit contract: money movement, filings, messages and deploys are gated."""
    assert not OPERATOR.has(PERM_EXECUTE_IRREVERSIBLE)
    assert FOUNDER.has(PERM_EXECUTE_IRREVERSIBLE)
    for effect in ("MOVE_MONEY", "FILE_SUBMISSION", "SEND_MESSAGE", "DEPLOY", "PROVIDER_CALL"):
        with pytest.raises(PermissionDeniedError) as excinfo:
            authorize_execution(OPERATOR, command_id="thue", cluster="vn_statutory",
                                external_effect=effect,
                                irreversible_effects=frozenset({"MOVE_MONEY", "FILE_SUBMISSION",
                                                                "SEND_MESSAGE", "DEPLOY",
                                                                "PROVIDER_CALL"}))
        assert excinfo.value.code == "IRREVERSIBLE_EFFECT_FORBIDDEN"
        authorize_execution(FOUNDER, command_id="thue", cluster="vn_statutory",
                            external_effect=effect,
                            irreversible_effects=frozenset({effect}))


# ---------------------------------------------------------------------------
# 3. Workspace isolation
# ---------------------------------------------------------------------------


def test_runs_are_invisible_across_workspaces(service):
    completed = run(service, FOUNDER, "thue", "tncn",
                    {"monthly_income": 35_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    assert service.list_runs(OUTSIDER) == []
    with pytest.raises(PromiseError) as excinfo:
        service.get_run(OUTSIDER, completed["run_id"])
    assert excinfo.value.code == "RUN_NOT_FOUND"
    assert excinfo.value.http_status == 404


def test_engine_data_evidence_and_gates_are_workspace_scoped(service):
    invoice_id = issue_invoice(service)
    record_tax_accounting(service)
    paused = pause_reconciliation(service, invoice_id)
    approved = decide(service, FOUNDER, paused)
    assert_completed(approved, "revenue_fact_is_verifiable", "invoice_ref_is_issued")
    sealed = service.reconcile_gate(FOUNDER, "first-revenue")
    assert sealed["status"] == "SEALED_VERIFIED"

    # Tenant A's engine ledger lives in A's own directory.
    db_path = approved["verification"]["engine_db_path"]
    assert f"/{WS_A}/" in db_path.replace("\\", "/")

    # Tenant B sees none of it: no revenue facts, no evidence, no sealed gate.
    assert revenue_rows(service, WS_B) == []
    assert service.list_runs(OUTSIDER) == []
    b_gates = service.gates(OUTSIDER)
    assert b_gates["unlocked_count"] == 0
    assert all(g["status"] != "SEALED_VERIFIED" for g in b_gates["gates"])
    b_reconcile = service.reconcile_gate(OUTSIDER, "first-revenue")
    assert b_reconcile["status"] != "SEALED_VERIFIED"


def test_evidence_query_is_limited_to_the_allowlist(service):
    with pytest.raises(EvidenceIntegrityError):
        service.evidence.query("promise_jobs", WS_A)
    with pytest.raises(EvidenceIntegrityError):
        service.evidence.query("revenue_transactions; DROP TABLE attestations", WS_A)


# ---------------------------------------------------------------------------
# 4. Duplicate submission and idempotency
# ---------------------------------------------------------------------------


def test_duplicate_submission_replays_the_persisted_job(service):
    params = {"tax_code": SELLER_MST, "taxpayer_name": "Công ty Mekong",
              "legal_rep": "Nguyễn Văn Sáng Lập", "taxpayer_type": "ENTERPRISE"}
    first = run(service, FOUNDER, "taxadmin", "register", params)
    assert_completed(first, "mst_checksum", "record_persisted", "echoes_input")

    replayed = run(service, FOUNDER, "taxadmin", "register", params)
    assert replayed["idempotent_replay"] is True
    assert replayed["run_id"] == first["run_id"]
    assert replayed["output"] == first["output"]

    # A new run for the same identity still cannot create a second taxpayer.
    forced = run(service, FOUNDER, "taxadmin", "register", params, idempotency_key="client-retry-2")
    assert forced["idempotent_replay"] is False
    with sqlite3.connect(f"file:{forced['verification']['engine_db_path']}?mode=ro", uri=True) as conn:
        rows = conn.execute("SELECT COUNT(*) FROM taxpayers WHERE tax_code = ?", (SELLER_MST,)).fetchone()[0]
    assert rows == 1


# ---------------------------------------------------------------------------
# 5. Approvals: payload binding, expiry, replay, rejection
# ---------------------------------------------------------------------------


def test_approval_is_bound_to_the_submitted_payload(service):
    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    token_id = paused["approval_request"]["approval_token_id"]

    # The approver saw 20,000,000đ. Resuming with 200,000,000đ is a different action.
    tampered = run(service, FOUNDER, "vietqr", "reconcile_payment", {
        "bank_tx_id": "MB-SPINE-0001", "amount_vnd": 200_000_000, "memo": "HD SPINE 000001",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00001",
        "invoice_ref": invoice_id,
    }, approval_token_id=token_id, idempotency_key="tampered-amount")
    assert tampered["status"] == STATUS_FAILED
    assert tampered["error_code"] == "APPROVAL_PAYLOAD_MISMATCH"
    assert revenue_rows(service, WS_A) == []


def test_approval_token_cannot_be_replayed(service):
    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    token_id = paused["approval_request"]["approval_token_id"]
    approved = decide(service, FOUNDER, paused)
    assert_completed(approved, "revenue_fact_is_verifiable")
    assert len(revenue_rows(service, WS_A)) == 1

    reuse = run(service, FOUNDER, "vietqr", "reconcile_payment", {
        "bank_tx_id": "MB-SPINE-0002", "amount_vnd": 20_000_000, "memo": "HD SPINE 000002",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00002",
        "invoice_ref": invoice_id,
    }, approval_token_id=token_id)
    assert reuse["status"] == STATUS_FAILED
    assert reuse["error_code"] in {"APPROVAL_REPLAY_OR_EXPIRED", "APPROVAL_PAYLOAD_MISMATCH"}
    assert len(revenue_rows(service, WS_A)) == 1


def test_expired_approval_token_is_refused(service):
    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    token_id = paused["approval_request"]["approval_token_id"]

    # A short-lived token issued for the same run; the stored expiry is not
    # rewritable by re-saving a token, so the clock is what makes it expire.
    short_lived = service.request_approval(FOUNDER, paused["run_id"], ttl_seconds=1)
    assert short_lived["approval_token_id"] != token_id
    assert short_lived["expires_at"] - int(time.time()) <= 1
    time.sleep(2.0)
    stored = service.opc_state.get_approval(short_lived["approval_token_id"])
    assert stored.expires_at < int(time.time()), "the token must be past its own expiry"
    token_id = short_lived["approval_token_id"]

    resumed = run(service, FOUNDER, "vietqr", "reconcile_payment", {
        "bank_tx_id": "MB-SPINE-0001", "amount_vnd": 20_000_000, "memo": "HD SPINE 000001",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00001",
        "invoice_ref": invoice_id,
    }, approval_token_id=token_id, idempotency_key="after-expiry")
    assert resumed["status"] == STATUS_FAILED
    assert resumed["error_code"] == "APPROVAL_REPLAY_OR_EXPIRED"
    assert revenue_rows(service, WS_A) == []


def test_unknown_approval_token_is_refused(service):
    invoice_id = issue_invoice(service)
    outcome = run(service, FOUNDER, "vietqr", "reconcile_payment", {
        "bank_tx_id": "MB-SPINE-0009", "amount_vnd": 20_000_000, "memo": "HD SPINE 000009",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00009",
        "invoice_ref": invoice_id,
    }, approval_token_id="appr_does_not_exist")
    assert outcome["status"] == STATUS_FAILED
    assert outcome["error_code"] == "APPROVAL_TOKEN_UNKNOWN"


def test_approval_token_is_bound_to_its_own_run(service):
    invoice_id = issue_invoice(service)
    first = pause_reconciliation(service, invoice_id, bank_tx_id="MB-SPINE-0010")
    second = pause_reconciliation(service, invoice_id, bank_tx_id="MB-SPINE-0011")
    with pytest.raises(PromiseError) as excinfo:
        service.decide_approval(FOUNDER, second["run_id"],
                                first["approval_request"]["approval_token_id"], "approve")
    assert excinfo.value.code == "APPROVAL_TOKEN_UNKNOWN"
    assert service.get_run(FOUNDER, second["run_id"])["job"]["status"] == STATUS_AWAITING_APPROVAL


def test_rejection_is_recorded_and_writes_no_business_fact(service):
    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    rejected = decide(service, APPROVER, paused, decision="reject", notes="chưa có sao kê")
    assert rejected["status"] == STATUS_REJECTED
    assert rejected["error_code"] == "APPROVAL_REJECTED"
    assert revenue_rows(service, WS_A) == []
    events = [e["event_type"] for e in service.get_run(FOUNDER, paused["run_id"])["events"]]
    assert "APPROVAL_REJECTED" in events


# ---------------------------------------------------------------------------
# 6. Crash recovery and reconciliation of uncertain effects
# ---------------------------------------------------------------------------


def _simulate_crash(service, who, external_effect, command_id="vietqr", op_id="vietqr.reconcile-payment"):
    """Persist a job as if the process died while the effect was in flight."""
    job = service.jobs.create_job(
        workspace_id=who.workspace_id, principal_id=who.principal_id, command_id=command_id,
        op_id=op_id, subcommand="reconcile_payment", params={"bank_tx_id": "MB-CRASH-0001"},
        params_digest=sha256_of({"bank_tx_id": "MB-CRASH-0001"}), idempotency_key=None,
        status=STATUS_QUEUED, external_effect=external_effect, code_version=service.code_version,
        run_id=new_run_id(),
    )
    return service.jobs.transition(job["run_id"], who.workspace_id, STATUS_RUNNING,
                                   event_type="EXECUTION_STARTED")


def test_restart_recovery_separates_uncertain_effects_from_local_writes(service):
    in_flight = _simulate_crash(service, FOUNDER, "PROVIDER_CALL")
    local_write = _simulate_crash(service, FOUNDER, "WORKSPACE_WRITE", op_id="vietqr.generate")

    recovered = {r["run_id"]: r["status"] for r in service.recover_after_restart()}
    assert recovered[in_flight["run_id"]] == STATUS_NEEDS_RECONCILIATION
    assert recovered[local_write["run_id"]] == STATUS_FAILED

    # Neither outcome is presented as success.
    assert service.jobs.get_job(in_flight["run_id"], WS_A)["error_code"] == "AWAITING_RECONCILIATION"
    assert service.jobs.get_job(local_write["run_id"], WS_A)["error_code"] == "INTERRUPTED_BY_RESTART"


def test_reconciliation_requires_provider_proof(service):
    in_flight = _simulate_crash(service, FOUNDER, "PROVIDER_CALL")
    service.recover_after_restart()
    run_id = in_flight["run_id"]

    with pytest.raises(PromiseError) as no_proof:
        service.reconcile(FOUNDER, run_id, resolution="CONFIRMED_COMPLETED", proof={})
    assert no_proof.value.code == "PROOF_REQUIRED"

    with pytest.raises(PromiseError) as bad_resolution:
        service.reconcile(FOUNDER, run_id, resolution="PROBABLY_FINE",
                          proof={"provider": "MBBANK", "reference": "STMT-1"})
    assert bad_resolution.value.code == "INVALID_RESOLUTION"

    closed = service.reconcile(FOUNDER, run_id, resolution="CONFIRMED_COMPLETED",
                               proof={"provider": "MBBANK", "reference": "STMT-20261027-MB-00001"})
    assert closed["status"] == STATUS_COMPLETED

    attestations = service.evidence.query("attestations", WS_A, where="kind = 'RECONCILIATION'")
    assert len(attestations) == 1
    assert attestations[0]["run_id"] == run_id

    with pytest.raises(PromiseError) as already_closed:
        service.reconcile(FOUNDER, run_id, resolution="CONFIRMED_COMPLETED",
                          proof={"provider": "MBBANK", "reference": "STMT-1"})
    assert already_closed.value.code == "NOT_AWAITING_RECONCILIATION"
    assert already_closed.value.http_status == 409


def test_reconciling_as_not_executed_is_a_failure_not_a_success(service):
    in_flight = _simulate_crash(service, FOUNDER, "FILE_SUBMISSION")
    service.recover_after_restart()
    closed = service.reconcile(FOUNDER, in_flight["run_id"], resolution="CONFIRMED_NOT_EXECUTED",
                               proof={"provider": "GDT", "reference": "TỜ KHAI KHÔNG TỒN TẠI"})
    assert closed["status"] == STATUS_FAILED
    assert closed["error_code"] == "RECONCILED_AS_NOT_COMPLETED"


def test_usage_with_unknown_provider_state_is_never_zeroed(service):
    """Reserved vs actual vs unknown must stay distinguishable (no silent zero)."""
    from src.opc.models import UsageRecord, UsageStage

    run_id = new_run_id()
    service.usage.record_usage(UsageRecord(
        event_id="use_unknown_1", run_id=run_id, attempt=1, stage=UsageStage.UNKNOWN,
        provider="MBBANK", model="n/a", tokens=0, tool_fee=None, amount=None, currency="VND",
        payer="workspace", pricing_source="unknown_provider_state", created_at=int(time.time()),
    ))
    summary = service._usage_summary(run_id)
    assert summary["has_unknown_costs"] is True
    assert summary["known_amounts"] == {}
    assert summary["stages"] == ["unknown"]


# ---------------------------------------------------------------------------
# 7. Receipts: signing, tamper detection, and the three separate claims
# ---------------------------------------------------------------------------


def test_receipt_signature_verifies_and_detects_tampering(service):
    outcome = run(service, FOUNDER, "thue", "tncn",
                  {"monthly_income": 35_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    assert_completed(outcome, "pit_dual_path")
    receipt = outcome["receipt"]
    assert receipt["receipt_version"] == "2.0.0"
    assert receipt["signing"]["status"] == "SIGNED"
    assert service.verify_receipt(receipt)["valid"] is True

    tampered_output = {**receipt, "output_sha256": "0" * 64}
    assert service.verify_receipt(tampered_output)["valid"] is False

    # Rewriting the measured business result — in either direction — is tampering.
    downgraded = {**receipt, "business_conditions_met": False, "run_status": STATUS_FAILED}
    downgraded["domain_verification"] = {**receipt["domain_verification"], "status": "FAILED"}
    assert service.verify_receipt(downgraded)["valid"] is False

    # So is re-stating which code version produced the run, or dropping a citation.
    assert service.verify_receipt({**receipt, "code_version": "v-next"})["valid"] is False
    assert service.verify_receipt({**receipt, "statutory_citations": []})["valid"] is False
    assert service.verify_receipt({**receipt, "workspace_id": WS_B})["valid"] is False

    reattributed = {**receipt, "signing": {**receipt["signing"], "key_id": "key-attacker"}}
    verify = service.verify_receipt(reattributed)
    assert verify["valid"] is False
    assert "key-attacker" in verify["reason"]

    unsigned = {k: v for k, v in receipt.items() if k != "signature"}
    assert service.verify_receipt(unsigned)["valid"] is False


def test_receipt_separates_handler_artifact_and_business_conditions(service):
    """Three distinct claims, so a green one cannot vouch for the others."""
    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    approved = decide(service, FOUNDER, paused)
    receipt = approved["receipt"]
    assert receipt["handler_ran"] is True
    assert receipt["artifact_integrity"] == "VERIFIED"
    assert receipt["business_conditions_met"] is True
    assert receipt["domain_verification"]["status"] == "PASSED"
    assert receipt["statutory_citations"]
    assert receipt["jurisdiction"] == "VN"
    assert receipt["rule_version"]
    assert receipt["code_version"] == "test-code-version"

    # A run whose handler executed but whose business conditions were not met
    # (the same bank transfer pushed through as a second, separately keyed run)
    # keeps the separation: handler_ran True, business_conditions_met False.
    second_paused = run(service, FOUNDER, "vietqr", "reconcile_payment", {
        "bank_tx_id": "MB-SPINE-0001", "amount_vnd": 20_000_000, "memo": "HD SPINE 000001",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00001",
        "invoice_ref": invoice_id,
    }, idempotency_key="second-run-same-transfer")
    assert second_paused["status"] == STATUS_AWAITING_APPROVAL
    duplicate = decide(service, FOUNDER, second_paused)
    assert duplicate["status"] == STATUS_FAILED
    assert duplicate["error_code"] == "BUSINESS_CONDITION_UNMET"
    assert duplicate["verification"]["handler_ran"] is True
    assert duplicate["verification"]["business_conditions_met"] is False
    assert duplicate["receipt"]["business_conditions_met"] is False
    assert duplicate["receipt"]["handler_ran"] is True
    # Still exactly one revenue fact for the whole workspace.
    assert len(revenue_rows(service, WS_A)) == 1


def test_unsigned_signer_degrades_honestly(service, tmp_path, monkeypatch):
    monkeypatch.delenv("MEKONG_EVIDENCE_SIGNING_KEY", raising=False)
    monkeypatch.delenv("MEKONG_EVIDENCE_KEY_FILE", raising=False)
    unsigned_service = PromiseRunService(
        state_dir=tmp_path / "state-unsigned", workspace_root=tmp_path,
        signer=EvidenceSigner(key=None, key_id=None), code_version_override="test",
    )
    assert unsigned_service.signer.is_configured is False
    outcome = run(unsigned_service, FOUNDER, "thue", "tncn",
                  {"monthly_income": 35_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    assert_completed(outcome, "pit_dual_path")
    assert outcome["receipt"]["signature"] is None
    assert outcome["receipt"]["signing"]["status"] == "UNSIGNED"
    assert "no signing key configured" in outcome["receipt"]["signing"]["reason"]
    verified = unsigned_service.verify_receipt(outcome["receipt"])
    assert verified["valid"] is False
    assert "no signing key configured" in verified["reason"]
    # The gate report tells the truth about signing capability too.
    assert unsigned_service.gates(FOUNDER)["signing"]["status"] == "UNSIGNED"


# ---------------------------------------------------------------------------
# 8. Gates are measured, never asserted
# ---------------------------------------------------------------------------


def test_running_commands_alone_never_seals_a_revenue_gate(service):
    """Executing CFO/tax commands creates no revenue fact — the gate stays unmet."""
    run(service, FOUNDER, "thue", "tncn",
        {"monthly_income": 35_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    run(service, FOUNDER, "thue", "gtgt", {"amount": 20_000_000, "rate": 10,
                                           "tax_period": "2026-10-01"})
    issue_invoice(service)

    gates = service.gates(FOUNDER)
    assert gates["gate_tier"] == "TIER_2_COMPANY_MILESTONE"
    assert gates["total_gates"] == 7
    assert gates["unlocked_count"] == 0

    first_revenue = next(g for g in gates["gates"] if g["gate_id"] == "first-revenue")
    assert first_revenue["status"] in {"LOCKED", "PARTIAL_EVIDENCE"}
    assert first_revenue["conditions_met"] < first_revenue["conditions_total"]

    measured = service.reconcile_gate(FOUNDER, "first-revenue")
    assert measured["status"] != "SEALED_VERIFIED"
    assert measured["reason"] == "conditions unmet — gate stays unlocked"
    assert revenue_rows(service, WS_A) == []


def test_gate_seals_only_from_a_reconciled_provider_confirmed_fact(service):
    invoice_id = issue_invoice(service)
    run(service, FOUNDER, "thue", "gtgt", {"amount": 20_000_000, "rate": 10,
                                           "tax_period": "2026-10-01"})
    before = service.reconcile_gate(FOUNDER, "first-revenue")
    assert before["status"] != "SEALED_VERIFIED"

    paused = pause_reconciliation(service, invoice_id)
    approved = decide(service, FOUNDER, paused)
    assert_completed(approved, "revenue_fact_is_verifiable", "invoice_ref_is_issued",
                     "record_persisted")

    rows = revenue_rows(service, WS_A)
    assert len(rows) == 1
    assert rows[0]["status"] == "RECONCILED"
    assert rows[0]["provider_confirmation_json"]
    assert float(rows[0]["amount"]) == 20_000_000
    assert rows[0]["currency"] == "VND"
    assert rows[0]["reconciled_by"]

    sealed = service.reconcile_gate(FOUNDER, "first-revenue")
    assert sealed["status"] == "SEALED_VERIFIED"
    assert all(c["met"] for c in sealed["conditions"])
    assert service.gates(FOUNDER)["unlocked_count"] == 1


def test_revenue_fact_requires_provider_confirmation(service):
    """A revenue row cannot be invented without the provider payload."""
    with pytest.raises(Exception) as excinfo:
        service.evidence.record_revenue_transaction(
            workspace_id=WS_A, run_id=new_run_id(), provider="MBBANK",
            method="vietqr_bank_transfer", amount=20_000_000, currency="VND",
            status="RECONCILED",
        )
    assert "provider confirmation" in str(excinfo.value)
    assert revenue_rows(service, WS_A) == []


# ---------------------------------------------------------------------------
# 9. Cancellation, persistence and restart
# ---------------------------------------------------------------------------


def test_cancellation_before_start_and_illegal_state(service):
    invoice_id = issue_invoice(service)
    paused = pause_reconciliation(service, invoice_id)
    cancelled = service.cancel(OPERATOR, paused["run_id"])
    assert cancelled["status"] == STATUS_CANCELLED

    completed = run(service, FOUNDER, "thue", "tncn",
                    {"monthly_income": 35_000_000, "dependents": 1, "tax_period": "2026-10-01"})
    with pytest.raises(PromiseError) as excinfo:
        service.cancel(OPERATOR, completed["run_id"])
    assert excinfo.value.code == "CANCEL_REJECTED"
    assert excinfo.value.http_status == 409

    with pytest.raises(PromiseError) as missing:
        service.cancel(OUTSIDER, completed["run_id"])
    assert missing.value.code == "RUN_NOT_FOUND"


def test_state_survives_a_process_restart(state_dir, tmp_path, monkeypatch):
    """A restart re-reads persisted state: runs, receipts and sealed gates."""
    monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "spine-test-signing-key")
    first = PromiseRunService(state_dir=state_dir, workspace_root=tmp_path,
                              code_version_override="v1")
    invoice_id = issue_invoice(first)
    record_tax_accounting(first)
    paused = pause_reconciliation(first, invoice_id)
    approved = decide(first, FOUNDER, paused)
    assert_completed(approved, "revenue_fact_is_verifiable")
    assert first.reconcile_gate(FOUNDER, "first-revenue")["status"] == "SEALED_VERIFIED"
    receipt = approved["receipt"]

    restarted = PromiseRunService(state_dir=state_dir, workspace_root=tmp_path,
                                  code_version_override="v1")
    assert restarted is not first

    reloaded = restarted.get_run(FOUNDER, approved["run_id"])
    assert reloaded["job"]["status"] == STATUS_COMPLETED
    assert reloaded["job"]["result"]["status"] == "RECONCILED"
    assert [e["event_type"] for e in reloaded["events"]][:3] == [
        "JOB_CREATED", "APPROVAL_REQUIRED", "APPROVAL_GRANTED"]
    assert restarted.verify_receipt(receipt)["valid"] is True
    assert restarted.gates(FOUNDER)["unlocked_count"] == 1
    assert len(revenue_rows(restarted, WS_A)) == 1
    # Nothing is re-executed by the restart, so no second revenue fact appears.
    assert restarted.recover_after_restart() == []


def test_paused_run_is_recovered_after_restart_not_resumed_silently(state_dir, tmp_path, monkeypatch):
    """An awaiting-approval run survives a restart and still needs its approver."""
    monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "spine-test-signing-key")
    first = PromiseRunService(state_dir=state_dir, workspace_root=tmp_path,
                              code_version_override="v1")
    invoice_id = issue_invoice(first)
    record_tax_accounting(first)
    paused = pause_reconciliation(first, invoice_id)

    restarted = PromiseRunService(state_dir=state_dir, workspace_root=tmp_path,
                                  code_version_override="v1")
    assert restarted.recover_after_restart() == []
    job = restarted.get_run(FOUNDER, paused["run_id"])["job"]
    assert job["status"] == STATUS_AWAITING_APPROVAL

    approved = decide(restarted, FOUNDER, paused)
    assert_completed(approved, "revenue_fact_is_verifiable")
    assert len(revenue_rows(restarted, WS_A)) == 1


# ---------------------------------------------------------------------------
# 10. Error honesty
# ---------------------------------------------------------------------------


def test_handler_errors_are_never_reported_as_success(service):
    """A business refusal inside the handler surfaces as a failed run."""
    outcome = run(service, FOUNDER, "vietqr", "reconcile_payment", {
        "bank_tx_id": "MB-SPINE-0099", "amount_vnd": 20_000_000, "memo": "HD SPINE 000099",
        "provider": "MBBANK", "provider_reference": "STMT-20261027-MB-00099",
        "invoice_ref": "INV-DOES-NOT-EXIST",
    }, idempotency_key="missing-invoice")
    assert outcome["status"] in {STATUS_AWAITING_APPROVAL, STATUS_FAILED}
    if outcome["status"] == STATUS_AWAITING_APPROVAL:
        resumed = decide(service, FOUNDER, outcome)
        assert resumed["status"] == STATUS_FAILED
        assert resumed["error_code"] in {"HANDLER_EXCEPTION", "HANDLER_ERROR",
                                           "BUSINESS_CONDITION_UNMET"}
        assert resumed["receipt"] is None or resumed["receipt"]["business_conditions_met"] is False
    assert revenue_rows(service, WS_A) == []


def test_promise_error_carries_its_http_status(service):
    with pytest.raises(PromiseError) as excinfo:
        service.get_run(FOUNDER, "RUN-MISSING")
    assert excinfo.value.http_status == 404
    assert excinfo.value.code == "RUN_NOT_FOUND"

    with pytest.raises(PromiseError) as unknown_gate:
        service.reconcile_gate(FOUNDER, "not-a-gate")
    assert unknown_gate.value.http_status == 404
    assert unknown_gate.value.code == "UNKNOWN_GATE"

    with pytest.raises(PromiseError) as unknown_command:
        run(service, FOUNDER, "not-a-command", "status", {})
    assert unknown_command.value.http_status == 404
    assert unknown_command.value.code == "UNKNOWN_COMMAND"


def test_capabilities_report_execution_binding_honestly(service):
    caps = service.capabilities(FOUNDER)
    assert caps["integrity"]["valid"] is True
    assert caps["count"] == 197
    executable = [i for i in caps["items"] if i["execution_status"] == "EXECUTABLE"]
    not_implemented = [i for i in caps["items"] if i["execution_status"] == "NOT_IMPLEMENTED"]
    assert len(executable) + len(not_implemented) == 197
    assert caps["executable_operations"] == sum(i["operation_count"] for i in caps["items"])
    assert caps["executable_operations"] >= 20
    bound = {i["name"] for i in executable}
    assert {"thue", "ke-toan", "bhxh", "payroll", "vietqr", "adminsanction", "taxadmin"} <= bound
    # Every executable command names the operation and the test that proves it.
    for item in executable:
        for op in item["executable_operations"]:
            assert op["handler"], op
            assert op["test_id"].startswith("tests/"), op
            assert op["postconditions"], op
