"""Security, Idempotency, Reconciliation & Honest Usage Tests for OPC Platform (Criteria F, G, H, I, J)."""
from __future__ import annotations

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
        business_name="SecOps Advisory",
        owner_name="Sec Owner",
        language="en",
        locale="en_US",
        timezone="UTC",
        currency="USD",
        services={"security_audit": Decimal("200.00")},
        payment_terms="Net 14",
    )
    intake = ProposalInput(
        request_id="req_sec_01",
        client_name="Vault Corp",
        client_contact="sec@vault.invalid",
        project_title="Penetration Test",
        requested_services=("security_audit",),
        estimated_hours=10,
        currency="USD",
    )
    return profile, intake


def test_criterion_f_payload_tampering_invalidates_approval(tmp_path: Path) -> None:
    """Criterion F: Modifying recipient, amount, content, or connector invalidates approval digest."""
    engine, mock_conn, _ = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)

    token = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.APPROVE)

    # Tamper with recipient
    tampered_recipient = replace(payload, recipient="attacker@evil.invalid")
    with pytest.raises(ApprovalSecurityError, match="Digest mismatch"):
        engine.execute_approved_action(token, tampered_recipient, idempotency_key="k1")

    # Tamper with budget amount
    tampered_budget = replace(payload, budget_amount="9999.00")
    with pytest.raises(ApprovalSecurityError, match="Digest mismatch"):
        engine.execute_approved_action(token, tampered_budget, idempotency_key="k2")

    # Tamper with content
    tampered_content = replace(payload, content="Wire funds to different account")
    with pytest.raises(ApprovalSecurityError, match="Digest mismatch"):
        engine.execute_approved_action(token, tampered_content, idempotency_key="k3")

    # Tamper with connector
    tampered_connector = replace(payload, connector="untrusted_webhook")
    with pytest.raises(ApprovalSecurityError, match="Digest mismatch"):
        engine.execute_approved_action(token, tampered_connector, idempotency_key="k4")

    assert len(mock_conn.dispatched) == 0


def test_criterion_g_denial_and_expiration_block_dispatch(tmp_path: Path) -> None:
    """Criterion G: Rejected, revoked, or expired tokens strictly block external connector dispatch."""
    engine, mock_conn, _ = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)

    # Rejected token
    rejected_token = engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.REJECT)
    with pytest.raises(ApprovalSecurityError, match="non-approved decision"):
        engine.execute_approved_action(rejected_token, payload, idempotency_key="k_rej")

    # Expired token
    expired_token = engine.approval_engine.issue_token(run_id, payload, custom_ttl=-10)
    with pytest.raises(ApprovalSecurityError, match="expired"):
        engine.execute_approved_action(expired_token, payload, idempotency_key="k_exp")

    # Revoked token
    revoked_token = engine.approval_engine.issue_token(run_id, payload)
    engine.approval_engine.revoke_token(revoked_token)
    with pytest.raises(ApprovalSecurityError, match="revoked"):
        engine.execute_approved_action(revoked_token, payload, idempotency_key="k_rev")

    assert len(mock_conn.dispatched) == 0


def test_criterion_h_idempotency_and_single_use_token(tmp_path: Path) -> None:
    """Criterion H: Single-use token blocks replay; duplicate idempotency_key prevents duplicate dispatch."""
    engine, mock_conn, _ = _make_engine(tmp_path)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)

    token1 = engine.approval_engine.issue_token(run_id, payload)
    res1 = engine.execute_approved_action(token1, payload, idempotency_key="idem_fixed_01")
    assert res1["status"] == "completed"
    assert len(mock_conn.dispatched) == 1

    # Replaying the same token must fail
    with pytest.raises(ApprovalSecurityError, match="already been consumed"):
        engine.execute_approved_action(token1, payload, idempotency_key="idem_fixed_02")

    # Even with a fresh token, repeating the same idempotency_key deduplicates at state store
    token2 = engine.approval_engine.issue_token(run_id, payload)
    res2 = engine.execute_approved_action(token2, payload, idempotency_key="idem_fixed_01")
    assert res2["status"] == "deduplicated"
    assert len(mock_conn.dispatched) == 1


def test_criterion_i_uncertain_external_effect_requires_reconciliation(tmp_path: Path) -> None:
    """Criterion I: Interrupted/uncertain connector call is flagged for reconciliation, not silently retried."""
    engine, _, _ = _make_engine(tmp_path, simulate_uncertain=True)
    profile, intake = _sample_inputs()
    run_id, _, payload = engine.generate_draft(profile, intake)

    token = engine.approval_engine.issue_token(run_id, payload)
    res = engine.execute_approved_action(token, payload, idempotency_key="idem_uncertain_01")
    assert res["status"] == "reconciliation_required"


def test_criterion_j_honest_usage_unknown_not_zero_and_deduplicated(tmp_path: Path) -> None:
    """Criterion J: Unknown cost remains unknown (never coerced to 0), and duplicate event_ids are ignored."""
    _, _, usage = _make_engine(tmp_path)
    rec_unknown = UsageRecord(
        event_id="evt_byok_01",
        run_id="run_econ_01",
        attempt=1,
        stage=UsageStage.UNKNOWN,
        provider="custom_byok",
        model="unpriced-model-v1",
        tokens=1500,
        tool_fee=None,
        amount=None,
        currency="USD",
        payer="owner_byok",
        pricing_source="unverified_external",
        created_at=1700000000,
    )
    assert usage.record_usage(rec_unknown) is True
    # Duplicate event_id must not double-count
    assert usage.record_usage(rec_unknown) is False

    summary = usage.aggregate_run_costs("run_econ_01")
    assert summary["has_unknown_costs"] is True
    assert summary["total_tokens"] == 1500
    assert summary["event_count"] == 1
    assert "USD" not in summary["known_amounts"]
