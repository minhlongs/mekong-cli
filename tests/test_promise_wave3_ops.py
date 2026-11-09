# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable promise verification for Wave 3 C-Suite/BizOps and VN Legal/Statutory operations.

Every test here is referenced by ``test_id`` in
``src/core/promise/ops/csuite_bizops_vn.py`` and ``src/core/promise/ops/legal_vn.py``,
and exercises the shared execution spine:
authz -> schema validation -> approval gate -> runtime -> workspace SQLite ->
postconditions -> evidence -> signed receipt -> L0–L5 milestone gate sealing.
"""

from __future__ import annotations

import sqlite3

import pytest

from src.core.promise.gates import STATUS_SEALED
from src.core.promise.identity import PermissionDeniedError, Principal
from src.core.promise.service import PromiseRunService

pytestmark = pytest.mark.unit

FOUNDER = Principal(
    principal_id="usr-founder",
    workspace_id="ws-wave3",
    roles=("founder",),
    tier="SCALE",
    display_name="Founder",
)
OPERATOR = Principal(
    principal_id="usr-operator",
    workspace_id="ws-wave3",
    roles=("operator",),
    tier="SCALE",
    display_name="Operator",
)
OTHER_WS_FOUNDER = Principal(
    principal_id="usr-other-founder",
    workspace_id="ws-other-wave3",
    roles=("founder",),
    tier="SCALE",
    display_name="Other Tenant Founder",
)


@pytest.fixture()
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "wave3-test-signing-key")
    return PromiseRunService(state_dir=tmp_path / "state", workspace_root=tmp_path)


def run(service, command, subcommand, params, principal=FOUNDER, **kwargs):
    return service.submit(principal, command, params, subcommand=subcommand, **kwargs).to_dict()


def checks(outcome):
    return {c["check"]: c for c in (outcome.get("verification") or {}).get("checks", [])}


def assert_passed(outcome, *names):
    assert outcome["status"] == "COMPLETED", (
        outcome.get("error_code"),
        outcome.get("error_message"),
        outcome.get("output"),
    )
    assert (outcome.get("verification") or {}).get("business_conditions_met") is True
    present = checks(outcome)
    for name in names:
        assert name in present, f"postcondition '{name}' did not run"
        assert present[name]["status"] == "PASSED", present[name]["detail"]


def test_capabilities_report_18_executable_commands_and_48_operations(service):
    """Capabilities ledger marks all Wave 1–5 commands (51) and operations (114) as EXECUTABLE."""
    caps = service.capabilities(FOUNDER)
    assert caps["executable_commands"] == 51
    assert caps["executable_operations"] == 114
    by_id = {c["name"]: c for c in caps["items"]}
    expected_counts = {
        "founder": 2,
        "marketing": 2,
        "sales": 2,
        "cto": 2,
        "ops": 2,
        "billing": 2,
        "corporate": 3,
        "labor": 3,
        "contract": 3,
    }
    for cmd_name, op_count in expected_counts.items():
        assert by_id[cmd_name]["execution_status"] == "EXECUTABLE", cmd_name
        assert by_id[cmd_name]["operation_count"] == op_count, cmd_name
        assert len(by_id[cmd_name]["executable_operations"]) == op_count, cmd_name


def test_founder_assess_and_analyze_profile_seal_l0_gate(service):
    """founder.assess-profile and founder.analyze-profile persist to founder.db and seal L0 gate."""
    assess = run(
        service,
        "founder",
        "assess_profile",
        {
            "name": "Trần Minh Long",
            "mission": "Xây dựng hệ điều hành AI một người chuẩn mực tại Việt Nam",
            "values": ["self_direction", "achievement", "security"],
        },
    )
    assert_passed(assess, "output_fields", "echoes_input", "record_persisted")
    assert assess["output"]["name"] == "Trần Minh Long"
    assert assess["output"]["attestation_id"].startswith("ATT-")

    analyze = run(
        service,
        "founder",
        "analyze_profile",
        {"name_or_id": "Trần Minh Long"},
    )
    assert_passed(analyze, "output_fields")
    assert analyze["output"]["success"] is True
    assert analyze["output"]["name"] == "trần minh long"
    assert len(analyze["output"]["strategic_recommendations"]) >= 1

    gate_l0 = service.reconcile_gate(FOUNDER, "company-blueprint")
    assert gate_l0["status"] == STATUS_SEALED
    assert gate_l0["conditions_met"] == gate_l0["conditions_total"] == 2


def test_marketing_campaign_and_seo_audit_seal_l1_and_repeatable_channel_gates(service):
    """marketing.create-campaign and marketing.seo-audit seal L1 offer-validated and L3 repeatable-channel."""
    camp_q3 = run(
        service,
        "marketing",
        "create_campaign",
        {
            "name": "Mekong CFO Automation Q3",
            "channel": "social",
            "budget": 1500.0,
            "target_audience": "SME CFOs in HCMC & Hanoi",
            "period": "2026-Q3",
            "conversions": 14,
        },
    )
    assert_passed(camp_q3, "output_fields", "echoes_input", "value_bounds", "record_persisted")

    camp_q4 = run(
        service,
        "marketing",
        "create_campaign",
        {
            "name": "Mekong CFO Automation Q4",
            "channel": "zalo",
            "budget": 2000.0,
            "target_audience": "SME Founders in Vietnam",
            "period": "2026-Q4",
            "conversions": 19,
        },
    )
    assert_passed(camp_q4, "output_fields", "echoes_input", "value_bounds", "record_persisted")

    seo = run(
        service,
        "marketing",
        "seo_audit",
        {"keyword": "phan mem ke toan thue ai", "domain": "mekong.vn"},
    )
    assert_passed(seo, "output_fields", "echoes_input", "provenance_recorded", "record_persisted")
    assert seo["output"]["confidence"] >= 0.8
    assert len(seo["output"]["sources"]) >= 2

    gate_l1 = service.reconcile_gate(FOUNDER, "offer-validated")
    assert gate_l1["status"] == STATUS_SEALED
    assert gate_l1["conditions_met"] == gate_l1["conditions_total"] == 3

    gate_l3_channel = service.reconcile_gate(FOUNDER, "repeatable-channel")
    assert gate_l3_channel["status"] == STATUS_SEALED
    assert gate_l3_channel["conditions_met"] == gate_l3_channel["conditions_total"] == 2


def test_sales_add_and_close_deal_seal_l4_fulfillment_gate(service):
    """sales.add-deal and sales.close-deal persist to sales.db and seal L4 fulfillment-stable gate."""
    added = run(
        service,
        "sales",
        "add_deal",
        {
            "name": "Triển khai gói Scale AI ERP",
            "company": "Công ty Cổ phần Logistics Cửu Long",
            "value": 180_000_000,
            "stage": "negotiation",
        },
    )
    assert_passed(added, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    deal_id = added["output"]["id"]

    closed = run(
        service,
        "sales",
        "close_deal",
        {"deal_id": deal_id, "sla_met": True},
    )
    assert_passed(closed, "output_fields", "enum_member", "record_persisted")
    assert closed["output"]["stage"] == "won"
    assert closed["output"]["acceptance_id"].startswith("ACC-")

    gate_l4 = service.reconcile_gate(FOUNDER, "fulfillment-stable")
    assert gate_l4["status"] == STATUS_SEALED
    assert gate_l4["conditions_met"] == gate_l4["conditions_total"] == 2


def test_cto_adr_and_security_review_seal_l2_and_l5_gates(service):
    """cto.security-review seals L2 mvp-live and cto.create-adr seals L5 scale-ready."""
    sec = run(
        service,
        "cto",
        "security_review",
        {
            "target_url": "https://app.mekong.vn/health",
            "environment": "production",
            "max_findings": 20,
        },
    )
    assert_passed(sec, "output_fields", "value_bounds", "record_persisted")
    assert sec["output"]["passed"] is True
    assert sec["output"]["proof_id"].startswith("DEP-")

    adr = run(
        service,
        "cto",
        "create_adr",
        {
            "title": "Workspace-Isolated SQLite Promise Execution Spine",
            "decision": "Enforce per-workspace SQLite databases and HMAC-SHA256 evidence receipts.",
            "consequences": "Zero cross-tenant data leakage and deterministic L0-L5 milestone gating.",
            "clone_target": "opc-clone-v2",
        },
    )
    assert_passed(adr, "output_fields", "echoes_input", "artifact_written", "record_persisted")
    assert adr["output"]["sop_export_id"].startswith("SOP-")
    assert adr["output"]["clone_attestation_id"].startswith("ATT-")

    gate_l2 = service.reconcile_gate(FOUNDER, "mvp-live")
    assert gate_l2["status"] == STATUS_SEALED
    assert gate_l2["conditions_met"] == gate_l2["conditions_total"] == 3

    gate_l5 = service.reconcile_gate(FOUNDER, "scale-ready")
    assert gate_l5["status"] == STATUS_SEALED
    assert gate_l5["conditions_met"] == gate_l5["conditions_total"] == 2


def test_ops_health_sweep_and_incident_persist_to_workspace_db(service):
    """ops.health-sweep and ops.create-incident persist records in workspace ops.db."""
    sweep = run(service, "ops", "health_sweep", {})
    assert_passed(sweep, "output_fields", "enum_member", "value_bounds", "record_persisted")
    assert sweep["output"]["overall_status"] in ("HEALTHY", "DEGRADED", "CRITICAL")

    inc = run(
        service,
        "ops",
        "create_incident",
        {
            "title": "High latency on e-invoice TVAN sandbox gateway",
            "severity": "SEV2",
            "service": "einvoice-gateway",
            "summary": "Upstream sandbox responded in 4.2s; circuit breaker engaged.",
        },
    )
    assert_passed(inc, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert inc["output"]["status"] == "OPEN"
    assert inc["output"]["severity"] == "SEV2"


def test_billing_record_and_reconcile_usage_persist_to_workspace_db(service):
    """billing.record-usage and billing.reconcile-usage persist usage and reconciliation rows in billing.db."""
    usage = run(
        service,
        "billing",
        "record_usage",
        {
            "license_key": "mekong_lic_ent_99",
            "event_type": "agent_minutes",
            "quantity": 45.0,
            "idempotency_key": "idem-wave3-001",
            "tier": "enterprise",
        },
    )
    assert_passed(usage, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert usage["output"]["status"] == "recorded"
    assert usage["output"]["total_cost"] > 0

    reconcile = run(
        service,
        "billing",
        "reconcile_usage",
        {"license_key": "mekong_lic_ent_99"},
    )
    assert_passed(reconcile, "output_fields", "enum_member", "record_persisted")
    assert reconcile["output"]["status"] == "clean"
    assert reconcile["output"]["events_reconciled"] == 1


def test_corporate_charter_resolution_and_incorporation_persist(service):
    """corporate.generate-charter, generate-resolution, and incorporate persist to workspace corporate.db."""
    charter = run(
        service,
        "corporate",
        "generate_charter",
        {
            "company_name": "Công ty TNHH Trí Tuệ Nhân Tạo Cửu Long",
            "entity_type": "TNHH_1TV",
            "charter_capital": 2_000_000_000,
            "legal_rep_name": "Nguyễn Minh Quân",
            "address": "Quận 1, TP. Hồ Chí Minh",
        },
    )
    assert_passed(charter, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert charter["output"]["chapters_count"] == 10
    assert charter["output"]["articles_count"] == 18

    resolution = run(
        service,
        "corporate",
        "generate_resolution",
        {
            "company_name": "Công ty TNHH Trí Tuệ Nhân Tạo Cửu Long",
            "resolution_type": "CAPITAL_INCREASE",
            "decisions": [
                "Tăng vốn điều lệ từ 2.000.000.000 VNĐ lên 5.000.000.000 VNĐ.",
                "Sửa đổi khoản 1 Điều 7 Điều lệ công ty tương ứng.",
            ],
        },
    )
    assert_passed(resolution, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert resolution["output"]["decisions_count"] == 2

    dossier = run(
        service,
        "corporate",
        "incorporate",
        {
            "company_name": "Công ty Cổ phần Công Nghệ Số Mekong",
            "entity_type": "JSC",
            "charter_capital": 5_000_000_000,
            "legal_rep_name": "Lê Hoàng Nam",
            "address": "Quận Hải Châu, Đà Nẵng",
            "main_industry": "6201",
        },
    )
    assert_passed(dossier, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert dossier["output"]["documents_count"] == 4


def test_labor_work_permit_overtime_and_regulations_persist(service):
    """labor.assess-work-permit, calculate-overtime, and audit-regulations persist to workspace labor.db."""
    wp = run(
        service,
        "labor",
        "assess_work_permit",
        {
            "worker_name": "Kenji Takahashi",
            "nationality": "Japan",
            "position_category": "EXPERT",
            "job_title": "Principal AI Architect",
            "education_degree": "MASTER",
            "experience_years": 6.0,
            "passport_number": "JP99887766",
        },
    )
    assert_passed(wp, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert wp["output"]["eligibility_status"] == "QUALIFIED"

    ot = run(
        service,
        "labor",
        "calculate_overtime",
        {
            "employee_name": "Phạm Thị Lan",
            "month_year": "2026-11",
            "hourly_rate_vnd": 120_000.0,
            "normal_day_ot_hours": 12.0,
            "weekend_ot_hours": 8.0,
            "holiday_ot_hours": 4.0,
            "night_shift_regular_hours": 6.0,
            "night_shift_ot_hours": 4.0,
            "yearly_cumulative_hours": 140.0,
        },
    )
    assert_passed(ot, "output_fields", "value_bounds", "record_persisted")
    assert ot["output"]["is_compliant"] is True
    assert ot["output"]["total_overtime_hours"] == 28.0
    assert ot["output"]["total_overtime_pay_vnd"] > 0

    reg = run(
        service,
        "labor",
        "audit_regulations",
        {
            "enterprise_name": "Công ty TNHH Trí Tuệ Nhân Tạo Cửu Long",
            "total_employees": 25,
            "has_written_regulations": True,
            "is_registered_with_dolab": True,
            "has_dialogue_mechanism": True,
            "has_safety_council": True,
        },
    )
    assert_passed(reg, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert reg["output"]["compliance_status"] == "FULLY_COMPLIANT"


def test_contract_draft_review_and_founder_gated_signature(service, tmp_path):
    """contract.draft and contract.review run directly; contract.sign enforces FOUNDER_CONFIRMATION."""
    drafted = run(
        service,
        "contract",
        "draft",
        {
            "template_type": "COMMERCIAL_SALE",
            "party_a_name": "Công ty TNHH Mekong AI",
            "party_b_name": "Công ty Cổ phần Bán Lẻ Việt",
            "contract_value_vnd": 240_000_000.0,
            "penalty_rate_pct": 8.0,
            "dispute_forum": "VIAC",
        },
    )
    assert_passed(drafted, "output_fields", "echoes_input", "enum_member", "record_persisted")
    contract_id = drafted["output"]["contract_id"]

    reviewed = run(
        service,
        "contract",
        "review",
        {"contract_id": contract_id},
    )
    assert_passed(reviewed, "output_fields", "enum_member", "value_bounds", "record_persisted")
    assert reviewed["output"]["risk_level"] == "LOW"
    assert reviewed["output"]["risk_score"] <= 15

    pending = run(
        service,
        "contract",
        "sign",
        {
            "contract_id": contract_id,
            "signer_name": "Trần Minh Long",
            "signer_title": "Giám đốc",
            "signer_tax_id": "0109998881",
        },
    )
    assert pending["status"] == "AWAITING_APPROVAL"
    token_id = pending["approval_request"]["approval_token_id"]

    contracts_db = tmp_path / ".mekong" / "workspaces" / FOUNDER.workspace_id / "contracts.db"
    with sqlite3.connect(contracts_db) as conn:
        sig_count = conn.execute("SELECT COUNT(*) FROM e_signatures").fetchone()[0]
    assert sig_count == 0

    with pytest.raises(PermissionDeniedError):
        service.decide_approval(
            OPERATOR,
            pending["run_id"],
            token_id,
            "approve",
            notes="Operator cannot approve founder signature",
        )

    approved = service.decide_approval(
        FOUNDER,
        pending["run_id"],
        token_id,
        "approve",
        notes="Founder confirmed electronic contract signature under Law on Electronic Transactions 2023",
    ).to_dict()
    assert_passed(approved, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert approved["output"]["legal_status"] == "VALID_ELECTRONIC_SIGNATURE"
    assert approved["output"]["signature_hash"] == "[REDACTED]"
    with sqlite3.connect(contracts_db) as conn:
        persisted_hash = conn.execute(
            "SELECT signature_hash FROM e_signatures WHERE contract_id = ?",
            (contract_id,),
        ).fetchone()[0]
    assert len(persisted_hash) == 64

    other_draft = run(
        service,
        "contract",
        "draft",
        {
            "template_type": "NDA",
            "party_a_name": "Tenant B Corp",
            "party_b_name": "Partner X",
        },
        principal=OTHER_WS_FOUNDER,
    )
    assert_passed(other_draft, "output_fields", "record_persisted")
    other_db = tmp_path / ".mekong" / "workspaces" / OTHER_WS_FOUNDER.workspace_id / "contracts.db"
    with sqlite3.connect(other_db) as conn:
        other_sigs = conn.execute("SELECT COUNT(*) FROM e_signatures").fetchone()[0]
    assert other_sigs == 0


def test_all_seven_l0_to_l5_milestone_gates_seal_end_to_end(service):
    """Executing Wave 1 + Wave 3 operations seals all 7 L0–L5 milestone gates in one workspace."""
    # L0: company-blueprint
    assert_passed(
        run(service, "founder", "assess_profile", {"name": "Nguyễn Sáng Lập"}),
        "record_persisted",
    )
    # L1: offer-validated & L3: repeatable-channel
    assert_passed(
        run(
            service,
            "marketing",
            "create_campaign",
            {"name": "Campaign P1", "channel": "social", "period": "2026-M10", "conversions": 9},
        ),
        "record_persisted",
    )
    assert_passed(
        run(
            service,
            "marketing",
            "create_campaign",
            {"name": "Campaign P2", "channel": "zalo", "period": "2026-M11", "conversions": 15},
        ),
        "record_persisted",
    )
    assert_passed(
        run(service, "marketing", "seo_audit", {"keyword": "ai erp vietnam", "domain": "mekong.vn"}),
        "provenance_recorded",
    )
    # L2: mvp-live
    assert_passed(
        run(service, "cto", "security_review", {"environment": "production"}),
        "record_persisted",
    )
    # L3: first-revenue (Wave 1 finance ops: invoice + tax + reconciled payment)
    inv = run(
        service,
        "ke-toan",
        "create_invoice",
        {
            "amount": 50_000_000,
            "buyer": "Công ty TNHH Khách Hàng Đầu Tiên",
            "seller_tax_code": "0100109106-505",
        },
    )
    assert_passed(inv, "invoice_tt78_structure")
    inv_id = inv["output"]["invoice_id"]

    vat = run(
        service,
        "thue",
        "gtgt",
        {"amount": 50_000_000, "rate": 10, "tax_period": "2026-10-01"},
    )
    assert_passed(vat, "vat_dual_path")

    pay_paused = run(
        service,
        "vietqr",
        "reconcile_payment",
        {
            "bank_tx_id": "MB-WAVE3-0001",
            "amount_vnd": 55_000_000,
            "memo": "HD C25TAA 000001",
            "provider": "MBBANK",
            "provider_reference": "STMT-20261109-MB-99001",
            "invoice_ref": inv_id,
        },
    )
    assert pay_paused["status"] == "AWAITING_APPROVAL"
    pay_tok = pay_paused["approval_request"]["approval_token_id"]
    pay_done = service.decide_approval(FOUNDER, pay_paused["run_id"], pay_tok, "approve").to_dict()
    assert_passed(pay_done, "record_persisted")

    # L4: fulfillment-stable
    deal = run(
        service,
        "sales",
        "add_deal",
        {"name": "Hợp đồng Enterprise Đầu Tiên", "company": "Công ty TNHH Khách Hàng Đầu Tiên", "value": 55_000_000},
    )
    assert_passed(deal, "record_persisted")
    assert_passed(
        run(service, "sales", "close_deal", {"deal_id": deal["output"]["id"], "sla_met": True}),
        "record_persisted",
    )

    # L5: scale-ready
    assert_passed(
        run(service, "cto", "create_adr", {"title": "Standard Operating Procedure Clone Architecture"}),
        "record_persisted",
    )

    gates_summary = service.gates(FOUNDER)
    assert gates_summary["total_gates"] == 7
    assert gates_summary["unlocked_count"] == 7
    unsealed = [g for g in gates_summary["gates"] if g["status"] != STATUS_SEALED]
    assert not unsealed, f"Expected all 7 gates SEALED_VERIFIED, got unsealed: {unsealed}"
