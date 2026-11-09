# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable promise verification for Wave 5 C-Suite/BizOps & VN Commercial/Financial/Cyber operations.

Every test here is referenced by ``test_id`` in
``src/core/promise/ops/csuite_bizops_wave5_vn.py`` and
``src/core/promise/ops/legal_commercial_cyber_vn.py``, and exercises the shared execution spine:
authz -> schema validation -> approval gate -> runtime -> workspace SQLite ->
postconditions -> evidence -> signed receipt.
"""

from __future__ import annotations

import sqlite3

import pytest

from src.core.capability_ledger import CapabilityLedger
from src.core.promise.contracts import load_default_registry
from src.core.promise.identity import PermissionDeniedError, Principal
from src.core.promise.service import PromiseRunService

pytestmark = pytest.mark.unit

FOUNDER = Principal(
    principal_id="usr-founder",
    workspace_id="ws-wave5",
    roles=("founder",),
    tier="SCALE",
    display_name="Founder",
)
OPERATOR = Principal(
    principal_id="usr-operator",
    workspace_id="ws-wave5",
    roles=("operator",),
    tier="SCALE",
    display_name="Operator",
)
OTHER_WS_FOUNDER = Principal(
    principal_id="usr-other-founder",
    workspace_id="ws-other-wave5",
    roles=("founder",),
    tier="SCALE",
    display_name="Other Tenant Founder",
)


@pytest.fixture()
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "wave5-test-signing-key")
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


def test_wave5_capabilities_51_commands_114_ops_registered(service):
    """Wave 5 advances the executable surface to 51 commands and 114 OperationSpecs."""
    registry = load_default_registry()
    assert len(registry.commands()) == 51
    assert len(registry) == 114

    caps = service.capabilities(FOUNDER)
    assert caps["executable_commands"] == 51
    assert caps["executable_operations"] == 114
    by_id = {c["name"]: c for c in caps["items"]}

    wave5_expected = {
        "idea": 2,
        "goal": 2,
        "governance": 2,
        "binh-phap": 2,
        "csuite": 2,
        "zenpay": 2,
        "revenue": 2,
        "usage": 2,
        "consulting": 2,
        "content": 2,
        "copywriting": 2,
        "vendor": 2,
        "etransaction": 2,
        "cyber": 2,
        "fdi": 2,
        "customs": 2,
        "banking": 2,
        "aml": 2,
    }
    for cmd_name, op_count in wave5_expected.items():
        assert by_id[cmd_name]["execution_status"] == "EXECUTABLE", cmd_name
        assert by_id[cmd_name]["operation_count"] == op_count, cmd_name
        assert len(by_id[cmd_name]["executable_operations"]) == op_count, cmd_name

    ledger = CapabilityLedger()
    claims = ledger.list_all()
    executable_cmds = set(registry.commands())
    assert sum(1 for c in claims if c["name"] in executable_cmds) == 51


def test_idea_synthesize_blueprint_and_founder_gated_charter(service):
    """idea.synthesize-blueprint and idea.approve-charter persist to idea.db with founder approval."""
    blueprint = run(
        service,
        "idea",
        "synthesize_blueprint",
        {
            "venture_name": "Mekong Autonomous CFO",
            "problem_statement": "SMEs lose 20 hours/week reconciling e-invoices and CIT/VAT filings.",
            "target_segment": "Vietnamese SMEs & One-Person Companies",
            "monetization_model": "DUAL_RAIL_SAAS",
        },
        principal=OPERATOR,
    )
    assert_passed(
        blueprint,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert blueprint["output"]["viability_score"] == 88
    assert blueprint["output"]["readiness_tier"] == "READY_FOR_CHARTER"

    paused = run(
        service,
        "idea",
        "approve_charter",
        {
            "venture_name": "Mekong Autonomous CFO",
            "initial_capital_vnd": 3_000_000_000.0,
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    with pytest.raises(PermissionDeniedError):
        service.decide_approval(OPERATOR, paused["run_id"], token_id, "approve")

    approved = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder ratifies venture charter",
    ).to_dict()
    assert_passed(
        approved,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert approved["output"]["status"] == "CHARTER_APPROVED"


def test_goal_decompose_mission_and_founder_locked_targets(service):
    """goal.decompose-mission and goal.lock-quarterly-targets persist to goal.db with founder gate."""
    mission = run(
        service,
        "goal",
        "decompose_mission",
        {
            "objective_title": "Reach $1M ARR across Vietnam & Singapore SMEs",
            "target_metric_name": "ARR_USD",
            "target_metric_value": 1_000_000.0,
            "quarter": "Q4/2026",
        },
        principal=OPERATOR,
    )
    assert_passed(
        mission,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert mission["output"]["key_results_count"] == 3
    assert mission["output"]["lock_status"] == "DECOMPOSED_DRAFT"

    paused = run(
        service,
        "goal",
        "lock_quarterly_targets",
        {
            "objective_title": "Reach $1M ARR across Vietnam & Singapore SMEs",
            "quarter": "Q4/2026",
            "target_mrr_usd": 85_000.0,
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    locked = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder locks Q4 OKR targets",
    ).to_dict()
    assert_passed(
        locked,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert locked["output"]["lock_status"] == "LOCKED_COMMITTED"


def test_governance_propose_amendment_and_ballot_tally(service):
    """governance.propose-amendment and governance.tally-ballot execute via GovernanceEngine in governance.db."""
    prop = run(
        service,
        "governance",
        "propose_amendment",
        {
            "title": "Nâng hạn mức tự động duyệt chi CFO lên 50 triệu VNĐ",
            "description": "Cho phép CFO Agent tự động duyệt chi phí hạ tầng dưới 50 triệu VNĐ.",
            "amendment_text": "Điều 14.2: Ủy quyền CFO Agent duyệt chi tự động dưới 50.000.000 VNĐ.",
            "proposer": "founder",
            "tier": "soft",
        },
        principal=OPERATOR,
    )
    assert_passed(prop, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert prop["output"]["status"] == "voting"

    tallied = run(
        service,
        "governance",
        "tally_ballot",
        {
            "title": "Ban hành quy chuẩn kiểm toán bảo mật hàng quý",
            "amendment_text": "Điều 18.1: Bắt buộc kiểm toán chữ ký HMAC-SHA256 mỗi quý.",
            "voter": "founder",
            "choice": "yes",
            "weight": 3.0,
            "tier": "soft",
        },
        principal=OPERATOR,
    )
    assert_passed(
        tallied,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert tallied["output"]["status"] == "passed"
    assert tallied["output"]["quorum_met"] is True


def test_binh_phap_assess_terrain_and_founder_committed_maneuver(service):
    """binh-phap.assess-terrain and binh-phap.commit-maneuver persist to binh_phap.db with founder confirmation."""
    terrain = run(
        service,
        "binh-phap",
        "assess_terrain",
        {
            "competitor_name": "Legacy On-Premise Accounting Suite",
            "market_segment": "Vietnam E-Invoice & Tax Compliance SaaS",
            "terrain_type": "ACCESSIBLE_GROUND",
            "relative_strength_ratio": 1.5,
        },
        principal=OPERATOR,
    )
    assert_passed(
        terrain,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert terrain["output"]["posture_status"] == "TERRAIN_ASSESSED"

    paused = run(
        service,
        "binh-phap",
        "commit_maneuver",
        {
            "competitor_name": "Legacy On-Premise Accounting Suite",
            "market_segment": "Vietnam E-Invoice & Tax Compliance SaaS",
            "capital_budget_vnd": 250_000_000.0,
            "maneuver_doctrine": "ORTHODOX_HOLD_UNORTHODOX_STRIKE",
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    committed = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder authorizes strategic wedge maneuver",
    ).to_dict()
    assert_passed(
        committed,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert committed["output"]["posture_status"] == "MANEUVER_COMMITTED"


def test_csuite_convene_council_and_founder_ratified_directive(service):
    """csuite.convene-council and csuite.ratify-directive persist to csuite.db with founder confirmation."""
    council = run(
        service,
        "csuite",
        "convene_council",
        {
            "agenda_title": "Chuyển đổi kiến trúc sang Multi-Tenant Workspace SQLite",
            "directive_summary": "Cách ly toàn bộ cơ sở dữ liệu theo từng workspace_id và ký số biên lai.",
            "participating_officers": ["CEO", "CTO", "CFO", "CSO"],
        },
        principal=OPERATOR,
    )
    assert_passed(
        council,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert council["output"]["board_status"] == "COUNCIL_DELIBERATED"

    paused = run(
        service,
        "csuite",
        "ratify_directive",
        {
            "agenda_title": "Chuẩn hóa chữ ký số biên lai giao dịch",
            "directive_summary": "Áp dụng bắt buộc chữ ký HMAC-SHA256 cho mọi biên lai giao dịch",
            "budget_impact_vnd": 120_000_000.0,
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    ratified = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder ratifies executive directive",
    ).to_dict()
    assert_passed(
        ratified,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert ratified["output"]["board_status"] == "DIRECTIVE_RATIFIED"


def test_zenpay_allocate_budget_and_founder_settled_disbursement(service):
    """zenpay.allocate-budget and zenpay.settle-disbursement persist to zenpay.db with founder confirmation."""
    budget = run(
        service,
        "zenpay",
        "allocate_budget",
        {
            "department_id": "platform-operations",
            "purpose": "Cloudflare & Viettel IDC Infrastructure",
            "amount_vnd": 180_000_000.0,
        },
        principal=OPERATOR,
    )
    assert_passed(
        budget,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert budget["output"]["treasury_status"] == "ALLOCATED"

    paused = run(
        service,
        "zenpay",
        "settle_disbursement",
        {
            "department_id": "platform-operations",
            "recipient_account": "VCB-0071009988776-VIETTEL-CHT",
            "amount_vnd": 85_000_000.0,
            "purpose": "Thanh toán hạ tầng máy chủ Quý 4/2026",
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    settled = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder approves treasury disbursement",
    ).to_dict()
    assert_passed(
        settled,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert settled["output"]["treasury_status"] == "DISBURSED_SETTLED"


def test_revenue_record_subscription_and_reconcile_mrr(service):
    """revenue.record-subscription and revenue.reconcile-mrr persist to revenue.db."""
    sub = run(
        service,
        "revenue",
        "record_subscription",
        {
            "customer_id": "cust-saigon-retail-01",
            "customer_name": "Công ty CP Bán Lẻ Sài Gòn",
            "tier": "pro",
            "amount_usd": 399.0,
            "gateway": "vietqr",
        },
        principal=OPERATOR,
    )
    assert_passed(
        sub,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert sub["output"]["status"] == "succeeded"

    recon = run(
        service,
        "revenue",
        "reconcile_mrr",
        {
            "customer_id": "cust-saigon-retail-02",
            "amount_usd": 399.0,
            "tier": "pro",
            "auto_fix": True,
        },
        principal=OPERATOR,
    )
    assert_passed(
        recon,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "record_persisted",
    )
    assert recon["output"]["total_collected"] >= 399.0


def test_usage_meter_consumption_and_founder_enforced_quota_cap(service):
    """usage.meter-consumption and usage.enforce-quota-cap persist to usage.db with founder confirmation."""
    meter = run(
        service,
        "usage",
        "meter_consumption",
        {
            "tenant_id": "tenant-mekong-pro-01",
            "feature_key": "einvoice_xml_signing",
            "mcu_consumed": 1800,
            "quota_cap_mcu": 4000,
        },
        principal=OPERATOR,
    )
    assert_passed(
        meter,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert meter["output"]["enforcement_action"] == "WITHIN_QUOTA"

    paused = run(
        service,
        "usage",
        "enforce_quota_cap",
        {
            "tenant_id": "tenant-mekong-pro-01",
            "quota_cap_mcu": 5000,
            "enforcement_mode": "HARD_THROTTLE_402",
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    enforced = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder enforces hard MCU quota cap",
    ).to_dict()
    assert_passed(
        enforced,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert enforced["output"]["enforcement_action"] == "HARD_THROTTLE_402"


def test_consulting_create_engagement_and_generate_proposal(service):
    """consulting.create-engagement and consulting.generate-proposal persist to consulting.db."""
    eng = run(
        service,
        "consulting",
        "create_engagement",
        {
            "client_name": "Tập đoàn Logistics Đông Nam Á",
            "service_tier": "full_stack",
            "price_usd": 8500.0,
        },
        principal=OPERATOR,
    )
    assert_passed(eng, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert eng["output"]["price_usd"] == 8500.0

    prop = run(
        service,
        "consulting",
        "generate_proposal",
        {
            "prospect_name": "Công ty CP Dược Phẩm Cửu Long",
            "service_tier": "custom_agent",
            "requirements": "Tự động hóa kiểm tra GDP/GMP và đối soát hóa đơn điện tử",
            "industry": "Pharma",
        },
        principal=OPERATOR,
    )
    assert_passed(prop, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert prop["output"]["price_usd"] > 0


def test_content_produce_asset_and_schedule_publication(service):
    """content.produce-asset and content.schedule-publication persist to content.db."""
    asset = run(
        service,
        "content",
        "produce_asset",
        {
            "pillar": "ai_automation",
            "format_type": "blog",
            "topic": "Hướng dẫn quyết toán thuế TNDN tự động cho SME Việt Nam 2026",
            "channel": "linkedin",
        },
        principal=OPERATOR,
    )
    assert_passed(asset, "output_fields", "echoes_input", "record_persisted")

    pub = run(
        service,
        "content",
        "schedule_publication",
        {
            "topic": "Checklist tuân thủ Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân",
            "channel": "linkedin",
            "new_status": "published",
        },
        principal=OPERATOR,
    )
    assert_passed(pub, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert pub["output"]["status"] == "published"


def test_copywriting_generate_and_audit_conversion_copy(service):
    """copywriting.generate-campaign-copy and copywriting.audit-conversion-copy persist to copywriting.db."""
    gen = run(
        service,
        "copywriting",
        "generate_campaign_copy",
        {
            "product_name": "Mekong CLI Tax & E-Invoice Autopilot",
            "target_audience": "Kế toán trưởng & Founder SME Việt Nam",
            "formula": "pas",
            "copy_type": "landing_page",
        },
        principal=OPERATOR,
    )
    assert_passed(gen, "output_fields", "echoes_input", "enum_member", "record_persisted")

    audit = run(
        service,
        "copywriting",
        "audit_conversion_copy",
        {
            "product_name": "Mekong CLI Tax & E-Invoice Autopilot",
            "target_audience": "Kế toán trưởng & Founder SME Việt Nam",
            "formula": "aida",
        },
        principal=OPERATOR,
    )
    assert_passed(
        audit,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert audit["output"]["grade"] in ("A", "B")


def test_vendor_onboard_and_security_audit_partner(service):
    """vendor.onboard-partner and vendor.audit-partner persist to vendor.db."""
    onboard = run(
        service,
        "vendor",
        "onboard_partner",
        {
            "name": "VNPT-CA Digital Signature Gateway",
            "vendor_type": "infra",
            "version": "2.4.0",
            "trust_score": 92.0,
        },
        principal=OPERATOR,
    )
    assert_passed(onboard, "output_fields", "echoes_input", "value_bounds", "record_persisted")

    audit = run(
        service,
        "vendor",
        "audit_partner",
        {
            "name": "VNPT-CA Digital Signature Gateway",
            "audit_type": "security",
            "vendor_type": "infra",
        },
        principal=OPERATOR,
    )
    assert_passed(audit, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert audit["output"]["audit_score"] >= 50.0


def test_etransaction_create_and_ceca_certify_contract(service):
    """etransaction.create-contract and etransaction.certify-ceca persist under Law 20/2023/QH15."""
    created = run(
        service,
        "etransaction",
        "create_contract",
        {
            "contract_number": "HD-ETX-2026-001",
            "title": "Hợp đồng cung cấp nền tảng AI Kế toán & Hóa đơn điện tử",
            "contract_value": 165_000_000.0,
        },
        principal=OPERATOR,
    )
    assert_passed(created, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert len(created["output"]["content_hash"]) == 64

    certified = run(
        service,
        "etransaction",
        "certify_ceca",
        {
            "contract_number": "HD-ETX-2026-002",
            "title": "Hợp đồng đại lý phân phối giải pháp Mekong CLI",
            "ceca_authority": "CeCA-Vietnam-Post",
            "license_number": "BCT-CeCA-008/GP",
            "contract_value": 240_000_000.0,
        },
        principal=OPERATOR,
    )
    assert_passed(certified, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert certified["output"]["ceca_verified"] is True
    assert certified["output"]["status"] == "CECA_CERTIFIED"


def test_cyber_assess_system_level_and_audit_data_localization(service):
    """cyber.assess-system-level and cyber.audit-data-localization persist under Decree 85 & Decree 53."""
    level = run(
        service,
        "cyber",
        "assess_system_level",
        {
            "system_name": "Mekong Sovereign Evidence & Tax Ledger",
            "organization": "Công ty TNHH Mekong AI",
            "data_classification": "CONFIDENTIAL_MAT",
            "service_scale": "NATIONAL",
        },
        principal=OPERATOR,
    )
    assert_passed(level, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert 1 <= level["output"]["recommended_level"] <= 5

    loc = run(
        service,
        "cyber",
        "audit_data_localization",
        {
            "service_name": "Mekong Cloud Tenant Workspace Store",
            "provider_type": "DOMESTIC_ENTERPRISE",
            "local_storage_active": True,
            "retention_months": 36,
            "has_local_branch": True,
        },
        principal=OPERATOR,
    )
    assert_passed(
        loc,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert loc["output"]["is_compliant"] is True


def test_fdi_generate_irc_dossier_and_evaluate_foreign_loan(service):
    """fdi.generate-irc-dossier and fdi.evaluate-foreign-loan persist under Investment Law 61/2020/QH14."""
    irc = run(
        service,
        "fdi",
        "generate_irc_dossier",
        {
            "project_name": "Trung tâm R&D Trí tuệ Nhân tạo Mekong Việt Nam",
            "capital_usd": 750_000.0,
            "investor_country": "SG",
            "sector_code": "IT_SOFTWARE",
            "location": "Khu Công Nghệ Cao Hòa Lạc, Hà Nội",
        },
        principal=OPERATOR,
    )
    assert_passed(irc, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert irc["output"]["required_documents_count"] >= 5

    loan = run(
        service,
        "fdi",
        "evaluate_foreign_loan",
        {
            "borrower_name": "Công ty TNHH Mekong AI Việt Nam",
            "lender_name": "OCBC Bank Singapore",
            "lender_country": "SG",
            "amount_usd": 1_200_000.0,
            "tenor_months": 36,
            "interest_rate_pct": 5.5,
        },
        principal=OPERATOR,
    )
    assert_passed(loan, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert loan["output"]["sbv_registration_required"] is True
    assert loan["output"]["is_compliant"] is True


def test_customs_create_declaration_and_verify_origin_co(service):
    """customs.create-declaration and customs.verify-origin-co persist under Customs Law 54/2014/QH13."""
    decl = run(
        service,
        "customs",
        "create_declaration",
        {
            "enterprise_tax_id": "0101234567",
            "commodity_name": "Máy chủ xử lý AI chuyên dụng NVIDIA L40S",
            "invoice_value_usd": 45_000.0,
            "hs_code": "8471.50.10",
            "origin_country": "SG",
            "declaration_type": "IMPORT_BUSINESS",
        },
        principal=OPERATOR,
    )
    assert_passed(decl, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert decl["output"]["channel"] in ("GREEN", "YELLOW", "RED")

    co = run(
        service,
        "customs",
        "verify_origin_co",
        {
            "exporter_name": "Công ty CP Thiết bị Số Mekong",
            "fob_value_usd": 100_000.0,
            "non_originating_value_usd": 45_000.0,
            "form_type": "FORM_D",
            "hs_code": "8471.30.20",
            "importer_country": "SG",
        },
        principal=OPERATOR,
    )
    assert_passed(
        co,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert co["output"]["rvc_pct"] == 55.0
    assert co["output"]["is_eligible"] is True
    assert co["output"]["status"] in ("ISSUED", "QUALIFIED_FOR_PREFERENTIAL_TARIFF")


def test_banking_audit_car_and_classify_credit_debt(service):
    """banking.audit-capital-adequacy and banking.classify-credit-debt persist under Law 32/2024/QH15."""
    car = run(
        service,
        "banking",
        "audit_capital_adequacy",
        {
            "institution_name": "Ngân hàng TMCP Số Mekong",
            "tier1_capital_vnd": 18_000_000_000_000.0,
            "tier2_capital_vnd": 4_000_000_000_000.0,
            "credit_rwa_vnd": 120_000_000_000_000.0,
            "market_rwa_vnd": 10_000_000_000_000.0,
            "operational_rwa_vnd": 10_000_000_000_000.0,
            "reporting_quarter": "Q4/2026",
        },
        principal=OPERATOR,
    )
    assert_passed(
        car,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert car["output"]["is_compliant"] is True
    assert car["output"]["car_ratio_pct"] >= 8.0

    debt = run(
        service,
        "banking",
        "classify_credit_debt",
        {
            "contract_number": "TD-2026-8899",
            "borrower_name": "Công ty TNHH Thương mại Tân Cảng",
            "outstanding_balance_vnd": 2_000_000_000.0,
            "overdue_days": 20,
            "deductible_collateral_vnd": 800_000_000.0,
        },
        principal=OPERATOR,
    )
    assert_passed(debt, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert debt["output"]["debt_group"] == 2
    assert debt["output"]["total_provision_vnd"] > 0


def test_aml_perform_cdd_and_founder_confirmed_str_filing(service, tmp_path):
    """aml.perform-cdd and aml.file-str-report persist under AML Law 14/2022/QH15 with tenant isolation."""
    cdd = run(
        service,
        "aml",
        "perform_cdd",
        {
            "customer_name": "Nguyễn Minh Hoàng",
            "identifier": "079090001234",
            "customer_type": "INDIVIDUAL",
            "industry": "FINTECH",
            "nationality": "VN",
            "is_pep": False,
        },
        principal=OPERATOR,
    )
    assert_passed(cdd, "output_fields", "echoes_input", "enum_member", "record_persisted")
    assert cdd["output"]["status"] == "APPROVED"

    paused = run(
        service,
        "aml",
        "file_str_report",
        {
            "customer_name": "Công ty TNHH Đầu tư Xuyên Biên Giới",
            "suspicion_type": "STRUCTURING",
            "amount": 780_000_000.0,
            "urgency": "HIGH",
        },
        principal=OPERATOR,
    )
    assert paused["status"] == "AWAITING_APPROVAL"
    token_id = paused["approval_request"]["approval_token_id"]

    with pytest.raises(PermissionDeniedError):
        service.decide_approval(OPERATOR, paused["run_id"], token_id, "approve")

    filed = service.decide_approval(
        FOUNDER,
        paused["run_id"],
        token_id,
        "approve",
        notes="Founder authorizes STR filing to PCRT (NHNN)",
    ).to_dict()
    assert_passed(filed, "output_fields", "echoes_input", "value_bounds", "record_persisted")
    assert filed["output"]["urgency"] == "HIGH"

    # Verify cross-workspace SQLite isolation
    other_cdd = run(
        service,
        "aml",
        "perform_cdd",
        {
            "customer_name": "Trần Thanh Tâm",
            "identifier": "079091009999",
            "customer_type": "INDIVIDUAL",
        },
        principal=OTHER_WS_FOUNDER,
    )
    assert_passed(other_cdd, "output_fields", "record_persisted")

    ws1_db = tmp_path / ".mekong" / "workspaces" / "ws-wave5" / "aml.db"
    ws2_db = tmp_path / ".mekong" / "workspaces" / "ws-other-wave5" / "aml.db"
    assert ws1_db.exists() and ws2_db.exists()
    with sqlite3.connect(ws1_db) as conn1, sqlite3.connect(ws2_db) as conn2:
        c1_names = {r[0] for r in conn1.execute("SELECT customer_name FROM aml_cdd_profiles")}
        c2_names = {r[0] for r in conn2.execute("SELECT customer_name FROM aml_cdd_profiles")}
    assert c1_names == {"Nguyễn Minh Hoàng"}
    assert c2_names == {"Trần Thanh Tâm"}
