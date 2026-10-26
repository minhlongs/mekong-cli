"""Security, Idempotency, Reconciliation & Honest Usage Tests for OPC Platform (Criteria F, G, H, I, J)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from src.opc.approval import ApprovalSecurityError
from src.opc.connectors.mock import MockConnector
from src.opc.engine import OPCEngine
from src.opc.manifest import load_pack_manifest
from src.opc.models import (
    ApprovalDecision,
    BusinessProfile,
    ProposalInput,
    UsageRecord,
    UsageStage,
)
from src.opc.state import StateStore
from src.opc.usage import UsageLedger

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PACK = REPO_ROOT / "src" / "opc" / "packs" / "client-proposal-followup"


def _make_engine(tmp_path: Path, simulate_uncertain: bool = False) -> tuple[OPCEngine, MockConnector, UsageLedger]:
    manifest = load_pack_manifest(DEFAULT_PACK / "pack.json")
    db_file = tmp_path / "sec_test.db"
    state = StateStore(db_file)
    usage = UsageLedger(db_file)
    mock_conn = MockConnector(simulate_uncertain=simulate_uncertain)
    engine = OPCEngine(manifest, state, usage, connectors={"mock_followup_draft": mock_conn})
    return engine, mock_conn, usage


def _sample_inputs() -> tuple[BusinessProfile, ProposalInput]:
    profile = BusinessProfile(
        business_name="SecOps Advisory", owner_name="Sec Owner", language="en", locale="en_US",
        timezone="UTC", currency="USD", services={"security_audit": Decimal("200.00")}, payment_terms="Net 14",
    )
    intake = ProposalInput(
        request_id="req_sec_01", client_name="Vault Corp", client_contact="sec@vault.invalid",
        project_title="Penetration Test", requested_services=("security_audit",), estimated_hours=10, currency="USD",
    )
    return profile, intake


def test_criterion_f_payload_tampering_invalidates_approval(tmp_path: Path) -> None:
    """Criterion F: Modifying recipient, amount, content, or connector invalidates approval digest."""
    engine, mock_conn, _ = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)
    token = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.APPROVE)

    for idx, field_update in enumerate([
        {"recipient": "attacker@evil.invalid"},
        {"budget_amount": "9999.00"},
        {"content": "Wire funds to different account"},
        {"connector": "mock_followup_draft", "attachments": ("malware.exe",)},
    ]):
        tampered = replace(payload, **field_update)
        with pytest.raises(ApprovalSecurityError, match="Digest mismatch"):
            engine.execute_approved_action(token, tampered, idempotency_key=f"k_{idx}")
    assert len(mock_conn.dispatched) == 0


def test_criterion_g_denial_revision_and_expiration_block_dispatch(tmp_path: Path) -> None:
    """Criterion G: Rejected, revised, revoked, or expired tokens strictly block external connector dispatch."""
    engine, mock_conn, _ = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)

    rejected = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.REJECT)
    with pytest.raises(ApprovalSecurityError, match="non-approved decision"):
        engine.execute_approved_action(rejected, payload, idempotency_key="k_rej")

    revised = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.REVISE, revision_notes="Adjust scope")
    with pytest.raises(ApprovalSecurityError, match="non-approved decision"):
        engine.execute_approved_action(revised, payload, idempotency_key="k_revise")
    assert "Adjust scope" in engine.build_followup_draft(ApprovalDecision.REVISE, intake.project_title, "en", "Adjust scope")

    expired = engine.approval_engine.issue_token(run_id, payload, custom_ttl=-10)
    with pytest.raises(ApprovalSecurityError, match="expired"):
        engine.execute_approved_action(expired, payload, idempotency_key="k_exp")

    revoked = engine.approval_engine.issue_token(run_id, payload)
    engine.approval_engine.revoke_token(revoked)
    with pytest.raises(ApprovalSecurityError, match="revoked"):
        engine.execute_approved_action(revoked, payload, idempotency_key="k_rev")
    assert len(mock_conn.dispatched) == 0


def test_criterion_h_atomic_multi_worker_consumption_and_idempotency(tmp_path: Path) -> None:
    """Criterion H: Atomic SQLite token consumption prevents 2-worker race; duplicate idempotency_key deduplicates."""
    engine, mock_conn, _ = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)

    token = engine.approval_engine.issue_token(run_id, payload)
    engine.state.save_approval(token)

    def _worker_consume() -> bool:
        return engine.state.consume_approval_atomic(token.token_id, token.action_digest, token.created_at)

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: _worker_consume(), range(2)))
    assert outcomes.count(True) == 1 and outcomes.count(False) == 1

    # Fresh token with duplicate idempotency_key deduplicates at state store
    t2 = engine.approval_engine.issue_token(run_id, payload)
    t3 = engine.approval_engine.issue_token(run_id, payload)
    assert engine.execute_approved_action(t2, payload, idempotency_key="idem_dup_01")["status"] == "completed"
    assert engine.execute_approved_action(t3, payload, idempotency_key="idem_dup_01")["status"] == "deduplicated"
    assert len(mock_conn.dispatched) == 1


def test_criterion_i_uncertain_external_effect_requires_reconciliation(tmp_path: Path) -> None:
    """Criterion I: Interrupted/uncertain connector call is flagged for reconciliation, not silently retried."""
    engine, _, _ = _make_engine(tmp_path, simulate_uncertain=True)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)
    token = engine.approval_engine.issue_token(run_id, payload)
    assert engine.execute_approved_action(token, payload, idempotency_key="idem_uncertain_01")["status"] == "reconciliation_required"


def test_criterion_j_budget_reservation_and_honest_unknown_usage(tmp_path: Path) -> None:
    """Criterion J: Pre-dispatch budget reservation blocks overspend; unknown cost remains unknown and deduplicated."""
    engine, _, usage = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)
    costly_payload = replace(payload, budget_amount="50.00")
    t_over = engine.approval_engine.issue_token(run_id, costly_payload)
    assert engine.execute_approved_action(t_over, costly_payload, idempotency_key="idem_over", hard_budget_limit="10.00")["status"] == "budget_exceeded"

    rec_unknown = UsageRecord(
        event_id="evt_byok_01", run_id="run_econ_01", attempt=1, stage=UsageStage.UNKNOWN,
        provider="custom_byok", model="unpriced-model-v1", tokens=1500, tool_fee=None,
        amount=None, currency="USD", payer="owner_byok", pricing_source="unverified_external", created_at=1700000000,
    )
    assert usage.record_usage(rec_unknown) is True
    assert usage.record_usage(rec_unknown) is False
    summary = usage.aggregate_run_costs("run_econ_01")
    assert summary["has_unknown_costs"] is True and "USD" not in summary["known_amounts"]
