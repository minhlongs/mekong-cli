# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable promise verification for Wave 4 Department, C-Suite & VN Digital/IP Legal operations.

Every test here is referenced by ``test_id`` in
``src/core/promise/ops/departments_wave4_vn.py`` and
``src/core/promise/ops/legal_digital_vn.py``, and exercises the shared execution spine:
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
    workspace_id="ws-wave4",
    roles=("founder",),
    tier="SCALE",
    display_name="Founder",
)
OPERATOR = Principal(
    principal_id="usr-operator",
    workspace_id="ws-wave4",
    roles=("operator",),
    tier="SCALE",
    display_name="Operator",
)
OTHER_WS_FOUNDER = Principal(
    principal_id="usr-other-founder",
    workspace_id="ws-other-wave4",
    roles=("founder",),
    tier="SCALE",
    display_name="Other Tenant Founder",
)


@pytest.fixture()
def service(tmp_path, monkeypatch):
    monkeypatch.setenv("MEKONG_EVIDENCE_SIGNING_KEY", "wave4-test-signing-key")
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


def test_wave4_capabilities_33_commands_78_ops_and_all_10_departments_executable(service):
    """All 10 departments have >= 2 executable commands, totaling 51 commands and 114 operations."""
    registry = load_default_registry()
    assert len(registry.commands()) == 51
    assert len(registry) == 114

    caps = service.capabilities(FOUNDER)
    assert caps["executable_commands"] == 51
    assert caps["executable_operations"] == 114
    by_id = {c["name"]: c for c in caps["items"]}

    wave4_expected = {
        "build": 2,
        "code": 2,
        "support": 2,
        "collab": 2,
        "memory": 2,
        "recall": 2,
        "benchmark": 2,
        "eval-agent": 2,
        "company": 2,
        "cfo": 2,
        "cmo": 2,
        "cso": 2,
        "privacy": 2,
        "ecom": 2,
        "ip": 2,
    }
    for cmd_name, op_count in wave4_expected.items():
        assert by_id[cmd_name]["execution_status"] == "EXECUTABLE", cmd_name
        assert by_id[cmd_name]["operation_count"] == op_count, cmd_name
        assert len(by_id[cmd_name]["executable_operations"]) == op_count, cmd_name

    ledger = CapabilityLedger()
    claims = ledger.list_all()
    executable_cmds = set(registry.commands())
    by_dept: dict[str, list[str]] = {}
    for c in claims:
        dept_id = c["department_id"]
        by_dept.setdefault(dept_id, [])
        if c["name"] in executable_cmds:
            by_dept[dept_id].append(c["name"])
    assert len(by_dept) == 10
    for dept_id, exec_list in by_dept.items():
        assert len(exec_list) >= 2, (
            f"Department {dept_id} has only {len(exec_list)} executable commands: {exec_list}"
        )


def test_wave4a_engineering_factory_build_and_code_ops(service):
    """build.verify-artifact, build.record-release, code.audit-module, and code.scaffold-component persist and pass postconditions."""
    verify_res = run(
        service,
        "build",
        "verify_artifact",
        {
            "artifact_name": "mekong-cli-wave4-wheel",
            "target_path": "src/core/promise",
            "max_files": 25,
        },
    )
    assert_passed(
        verify_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert verify_res["output"]["artifact_name"] == "mekong-cli-wave4-wheel"
    assert verify_res["output"]["files_scanned"] >= 1
    assert verify_res["output"]["build_status"] in ("VERIFIED", "WARNING")

    release_res = run(
        service,
        "build",
        "record_release",
        {
            "environment": "production",
            "artifact_digest": "sha256:9f86d081884c7d659a2feaa0c55ad015",
            "health_url": "https://app.mekongcli.vn/healthz",
            "http_status": 200,
        },
    )
    assert_passed(
        release_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert release_res["output"]["release_status"] == "RELEASED"
    assert release_res["output"]["health_status"] == "HEALTHY"

    audit_res = run(
        service,
        "code",
        "audit_module",
        {
            "module_name": "promise-execution-spine",
            "target_path": "src/core/promise",
            "max_files": 20,
        },
    )
    assert_passed(
        audit_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert audit_res["output"]["module_name"] == "promise-execution-spine"
    assert audit_res["output"]["audit_verdict"] in ("PASS", "NEEDS_REFACTOR")

    scaffold_res = run(
        service,
        "code",
        "scaffold_component",
        {
            "component_name": "invoice_reconciler",
            "module_type": "service",
            "with_test": True,
        },
    )
    assert_passed(
        scaffold_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert scaffold_res["output"]["component_name"] == "invoice_reconciler"
    assert scaffold_res["output"]["files_created_count"] >= 2
    assert scaffold_res["output"]["status"] == "SCAFFOLDED"


def test_wave4a_customer_success_support_and_collab_ops(service):
    """support.submit-bug, support.submit-feedback, collab.create-handoff, and founder-gated collab.accept-deliverable."""
    bug_res = run(
        service,
        "support",
        "submit_bug",
        {
            "title": "VietQR webhook timeout khi tải cao",
            "severity": "critical",
            "description": "Timeout > 5s khi đối soát đồng thời 200 giao dịch",
        },
    )
    assert_passed(
        bug_res,
        "output_fields",
        "echoes_input",
        "enum_member",
        "record_persisted",
    )
    assert bug_res["output"]["severity"] == "critical"
    assert bug_res["output"]["triage_urgency"]

    fb_res = run(
        service,
        "support",
        "submit_feedback",
        {
            "user_id": "cust_vn_001",
            "nps_score": 10,
            "feedback_text": "Tốc độ kê khai thuế và BHXH rất chính xác.",
            "category": "tax_automation",
        },
    )
    assert_passed(
        fb_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "record_persisted",
    )
    assert fb_res["output"]["nps_score"] == 10
    assert fb_res["output"]["total_responses"] >= 1

    handoff_res = run(
        service,
        "collab",
        "create_handoff",
        {
            "task_summary": "Bàn giao gói kiểm toán hợp đồng lao động sang bộ phận Review",
            "deliverable_ref": "docs/deliverables/labor-audit-q4.json",
            "sender_role": "implementer",
            "recipient_role": "reviewer",
        },
    )
    assert_passed(
        handoff_res,
        "output_fields",
        "echoes_input",
        "enum_member",
        "record_persisted",
    )
    assert handoff_res["output"]["is_valid"] is True
    assert handoff_res["output"]["status"] == "DISPATCHED"

    # collab.accept-deliverable is gated by FOUNDER_CONFIRMATION
    accept_params = {
        "client_name": "Công ty Cổ phần Thương mại Đông Á",
        "deliverable_ref": "release://mekong-enterprise-v4.0",
        "accepted_by": "Founder & Đại diện Đông Á",
        "nps_score": 9,
    }
    paused = run(service, "collab", "accept_deliverable", accept_params, principal=OPERATOR)
    assert paused["status"] == "AWAITING_APPROVAL"
    tok = paused["approval_request"]["approval_token_id"]

    with pytest.raises(PermissionDeniedError):
        service.decide_approval(OPERATOR, paused["run_id"], tok, "approve")

    accepted = service.decide_approval(FOUNDER, paused["run_id"], tok, "approve").to_dict()
    assert_passed(
        accepted,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert accepted["output"]["acceptance_status"] == "ACCEPTED"
    assert accepted["output"]["client_name"] == "Công ty Cổ phần Thương mại Đông Á"


def test_wave4a_knowledge_memory_and_recall_ops(service):
    """memory.store-note, memory.export-sop-pack, recall.query-knowledge, and recall.attest-clone-readiness."""
    note_res = run(
        service,
        "memory",
        "store_note",
        {
            "topic": "Quy trình đối soát thuế nhà thầu FCT Thông tư 103/2014",
            "outcome": "Khấu trừ 5% GTGT + 5% TNDN trước khi thanh toán đối tác SaaS nước ngoài.",
            "agent_id": "tax-specialist",
            "tags": ["fct", "tax", "sop"],
        },
    )
    assert_passed(
        note_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert note_res["output"]["status"] == "STORED"
    assert note_res["output"]["tags_count"] == 3

    sop_res = run(
        service,
        "memory",
        "export_sop_pack",
        {
            "pack_name": "vn-sme-statutory-ops-pack-v4",
            "sop_count": 18,
            "exported_by": "Founder",
        },
    )
    assert_passed(
        sop_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert sop_res["output"]["status"] == "EXPORTED"
    assert len(sop_res["output"]["bundle_sha256"]) == 64

    recall_res = run(
        service,
        "recall",
        "query_knowledge",
        {
            "query": "FCT",
            "limit": 5,
        },
    )
    assert_passed(
        recall_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert recall_res["output"]["matches_count"] >= 1
    assert recall_res["output"]["recall_status"] == "MATCHED"

    attest_res = run(
        service,
        "recall",
        "attest_clone_readiness",
        {
            "clone_profile_name": "mekong-vn-agency-clone-v4",
            "founder_name": "Minh Long",
            "readiness_score": 95,
        },
    )
    assert_passed(
        attest_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert attest_res["output"]["status"] == "ATTESTED"
    assert attest_res["output"]["readiness_score"] == 95


def test_wave4a_market_intelligence_benchmark_and_eval_agent_ops(service):
    """benchmark.run-suite, benchmark.compare-competitors, eval-agent.evaluate-quality, and eval-agent.audit-safety."""
    bench_res = run(
        service,
        "benchmark",
        "run_suite",
        {
            "suite": "pev",
            "iterations": 2,
            "chaos_level": "none",
        },
    )
    assert_passed(
        bench_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert bench_res["output"]["suite"] == "pev"
    assert bench_res["output"]["verdict"] in ("EXCELLENT", "PASS", "DEGRADED")

    comp_res = run(
        service,
        "benchmark",
        "compare_competitors",
        {
            "segment_name": "AI Business Operations CLI for Vietnam SMEs",
            "competitors": ["Generic Chatbots", "Legacy ERP", "Manual Spreadsheets"],
            "our_strength_score": 91,
        },
    )
    assert_passed(
        comp_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert comp_res["output"]["positioning_verdict"] == "CATEGORY_LEADER"
    assert comp_res["output"]["competitors_evaluated"] == 3

    eval_res = run(
        service,
        "eval-agent",
        "evaluate_quality",
        {
            "agent_id": "vn-legal-counsel-agent",
            "goal": "Thẩm định hợp đồng lao động theo Bộ luật Lao động 2019",
            "duration_ms": 980,
            "credits_used": 0.12,
            "quality_score": 96,
        },
    )
    assert_passed(
        eval_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert eval_res["output"]["quality_grade"] == "A"

    safety_res = run(
        service,
        "eval-agent",
        "audit_safety",
        {
            "agent_id": "vn-legal-counsel-agent",
            "policy_profile": "VN_STATUTORY_STRICT",
            "redaction_verified": True,
            "boundary_verified": True,
        },
    )
    assert_passed(
        safety_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert safety_res["output"]["safety_verdict"] == "SAFE_APPROVED"
    assert safety_res["output"]["safety_score"] == 100


def test_wave4a_csuite_company_cfo_cmo_cso_ops(service):
    """company, cfo (including founder-gated approve-budget), cmo, and cso operations."""
    bp_res = run(
        service,
        "company",
        "init_blueprint",
        {
            "company_name": "Công ty TNHH Công nghệ Mekong AI",
            "product_type": "saas",
            "scenario": "hybrid",
            "budget_tier": "minimal",
            "primary_language": "vi",
        },
    )
    assert_passed(
        bp_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert bp_res["output"]["status"] == "INITIALIZED"
    assert bp_res["output"]["files_generated_count"] >= 1

    ready_res = run(
        service,
        "company",
        "audit_readiness",
        {
            "company_name": "Công ty TNHH Công nghệ Mekong AI",
            "departments_ready_count": 10,
        },
    )
    assert_passed(
        ready_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert ready_res["output"]["readiness_score"] == 100
    assert ready_res["output"]["readiness_status"] == "READY_FOR_EXECUTION"

    runway_res = run(
        service,
        "cfo",
        "forecast_runway",
        {
            "scenario_name": "Kế hoạch dòng tiền Q4-2026",
            "cash_balance_vnd": 1_800_000_000.0,
            "monthly_burn_vnd": 160_000_000.0,
            "monthly_revenue_vnd": 100_000_000.0,
        },
    )
    assert_passed(
        runway_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert runway_res["output"]["runway_months"] == 30.0
    assert runway_res["output"]["risk_tier"] == "HEALTHY"

    # cfo.approve-budget requires FOUNDER_CONFIRMATION
    budget_params = {
        "department_name": "engineering-factory",
        "approved_amount_vnd": 250_000_000.0,
        "fiscal_period": "Q4-2026",
    }
    paused_budget = run(service, "cfo", "approve_budget", budget_params, principal=FOUNDER)
    assert paused_budget["status"] == "AWAITING_APPROVAL"
    budget_tok = paused_budget["approval_request"]["approval_token_id"]

    with pytest.raises(PermissionDeniedError):
        service.decide_approval(OPERATOR, paused_budget["run_id"], budget_tok, "approve")

    approved_budget = service.decide_approval(
        FOUNDER, paused_budget["run_id"], budget_tok, "approve"
    ).to_dict()
    assert_passed(
        approved_budget,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert approved_budget["output"]["approval_status"] == "APPROVED"
    assert approved_budget["output"]["approved_amount_vnd"] == 250_000_000.0

    funnel_res = run(
        service,
        "cmo",
        "plan_funnel",
        {
            "funnel_name": "Phễu Zalo OA B2B Tháng 11",
            "primary_channel": "zalo",
            "budget_usd": 3000.0,
        },
    )
    assert_passed(
        funnel_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "record_persisted",
    )
    assert funnel_res["output"]["primary_channel"] == "zalo"

    cac_res = run(
        service,
        "cmo",
        "audit_channel_cac",
        {
            "channel": "zalo-oa-b2b",
            "period": "2026-11",
            "spend_vnd": 20_000_000.0,
            "leads": 100,
            "conversions": 10,
            "avg_ltv_vnd": 15_000_000.0,
        },
    )
    assert_passed(
        cac_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert cac_res["output"]["cac_vnd"] == 2_000_000.0
    assert cac_res["output"]["ltv_cac_ratio"] == 7.5
    assert cac_res["output"]["efficiency_verdict"] == "REPEATABLE_PROFITABLE"

    lead_res = run(
        service,
        "cso",
        "qualify_lead",
        {
            "company": "Tập đoàn Logistics Cửu Long",
            "deal_name": "Triển khai AI Ops toàn diện",
            "estimated_value_usd": 24_000.0,
            "bant_score": 88,
        },
    )
    assert_passed(
        lead_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert lead_res["output"]["qualification_verdict"] == "SQL_QUALIFIED"

    pipe_res = run(
        service,
        "cso",
        "review_pipeline",
        {
            "review_period": "Q4-2026",
            "target_quota_usd": 20_000.0,
        },
    )
    assert_passed(
        pipe_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert pipe_res["output"]["total_deals"] >= 1
    assert pipe_res["output"]["pipeline_health"] in ("STRONG_COVERAGE", "BUILDING_PIPELINE")


def test_wave4b_privacy_dpia_and_founder_gated_dsar(service):
    """privacy.assess-dpia (Decree 13/2023 Form 04-A05) and founder-gated privacy.process-dsar (72h SLA)."""
    dpia_res = run(
        service,
        "privacy",
        "assess_dpia",
        {
            "activity_name": "Xử lý dữ liệu bảng lương và BHXH nhân sự",
            "processing_purpose": "Kê khai thuế TNCN và bảo hiểm xã hội bắt buộc theo luật định",
            "data_categories": ["FULL_NAME", "TAX_ID", "BANKING_FINANCIAL", "HEALTH_MEDICAL_RECORDS"],
            "legal_basis": "LEGAL_OBLIGATION",
        },
    )
    assert_passed(
        dpia_res,
        "output_fields",
        "echoes_input",
        "enum_member",
        "value_bounds",
        "record_persisted",
    )
    assert dpia_res["output"]["is_sensitive_data_processed"] is True
    assert dpia_res["output"]["risk_level"] == "HIGH_RISK"
    assert dpia_res["output"]["filing_deadline_days"] == 60

    dsar_params = {
        "request_type": "RIGHT_TO_DELETE",
        "subject_id": "emp_vn_2048",
        "details": "Yêu cầu xóa dữ liệu cá nhân sau khi chấm dứt hợp đồng lao động theo Điều 16 Nghị định 13/2023/NĐ-CP",
    }
    paused_dsar = run(service, "privacy", "process_dsar", dsar_params, principal=FOUNDER)
    assert paused_dsar["status"] == "AWAITING_APPROVAL"
    dsar_tok = paused_dsar["approval_request"]["approval_token_id"]

    with pytest.raises(PermissionDeniedError):
        service.decide_approval(OPERATOR, paused_dsar["run_id"], dsar_tok, "approve")

    completed_dsar = service.decide_approval(
        FOUNDER, paused_dsar["run_id"], dsar_tok, "approve"
    ).to_dict()
    assert_passed(
        completed_dsar,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert completed_dsar["output"]["subject_id"] == "emp_vn_2048"
    assert completed_dsar["output"]["deadline_days"] == 3
    assert completed_dsar["output"]["sla_hours"] == 72


def test_wave4b_ecom_platform_filing_and_fct_withholding_tax(service):
    """ecom.assess-platform-filing (Decree 52/2013 & 85/2021) and ecom.calculate-withholding-tax (Circular 103/2014 & 80/2021)."""
    filing_res = run(
        service,
        "ecom",
        "assess_platform_filing",
        {
            "platform_name": "Sàn TMĐT B2B MekongMart",
            "domain_url": "https://mekongmart.vn",
            "platform_type": "MARKETPLACE",
            "enterprise_tax_id": "0318889991",
            "has_operating_regulations": True,
            "has_dispute_mechanism": True,
            "has_seller_kyc": True,
            "has_data_retention_3yr": True,
            "has_tax_reporting_system": True,
        },
    )
    assert_passed(
        filing_res,
        "output_fields",
        "echoes_input",
        "enum_member",
        "value_bounds",
        "record_persisted",
    )
    assert filing_res["output"]["statutory_procedure"] == "REGISTRATION"
    assert filing_res["output"]["compliance_score"] == 100

    fct_res = run(
        service,
        "ecom",
        "calculate_withholding_tax",
        {
            "foreign_supplier_name": "CloudInfra Global Inc.",
            "service_category": "DIGITAL_SERVICES",
            "revenue_vnd": 200_000_000.0,
            "quarter": "Q4-2026",
        },
    )
    assert_passed(
        fct_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "record_persisted",
    )
    # 5% VAT (10,000,000) + 5% CIT (10,000,000) = 20,000,000 VND
    assert fct_res["output"]["vat_amount_vnd"] == 10_000_000.0
    assert fct_res["output"]["cit_amount_vnd"] == 10_000_000.0
    assert fct_res["output"]["total_fct_liability_vnd"] == 20_000_000.0


def test_wave4b_ip_trademark_and_software_copyright(service):
    """ip.assess-trademark (IP Law 2022 + Nice 12) and ip.register-copyright (Decree 17/2023 COV) with tenant DB isolation."""
    tm_res = run(
        service,
        "ip",
        "assess_trademark",
        {
            "mark_name": "MEKONG PROMISE SPINE",
            "nice_class": "09",
            "applicant_name": "Công ty TNHH Công nghệ Mekong AI",
        },
    )
    assert_passed(
        tm_res,
        "output_fields",
        "echoes_input",
        "enum_member",
        "value_bounds",
        "record_persisted",
    )
    assert tm_res["output"]["mark_name"] == "MEKONG PROMISE SPINE"
    assert tm_res["output"]["official_fee_vnd"] == 1_000_000
    assert tm_res["output"]["overall_conflict_risk"] in ("LOW", "MEDIUM", "HIGH")

    cov_res = run(
        service,
        "ip",
        "register_copyright",
        {
            "software_name": "Mekong CLI Promise Execution Engine v4.0",
            "author_name": "Minh Long",
            "version": "4.0.0",
            "lines_of_code": 28_500,
        },
    )
    assert_passed(
        cov_res,
        "output_fields",
        "echoes_input",
        "value_bounds",
        "enum_member",
        "record_persisted",
    )
    assert cov_res["output"]["official_fee_vnd"] == 100_000
    assert cov_res["output"]["dossier_items_count"] == 5
    assert cov_res["output"]["status"] == "DOSSIER_COMPILED"

    # Verify tenant workspace isolation for ip.db
    other_tm = run(
        service,
        "ip",
        "assess_trademark",
        {
            "mark_name": "OTHER TENANT BRAND",
            "nice_class": "42",
        },
        principal=OTHER_WS_FOUNDER,
    )
    assert_passed(other_tm, "record_persisted")
    db1 = tm_res["verification"]["engine_db_path"]
    db2 = other_tm["verification"]["engine_db_path"]
    assert db1 != db2
    with sqlite3.connect(db1) as conn1:
        names1 = {r[0] for r in conn1.execute("SELECT mark_name FROM trademarks").fetchall()}
    with sqlite3.connect(db2) as conn2:
        names2 = {r[0] for r in conn2.execute("SELECT mark_name FROM trademarks").fetchall()}
    assert "MEKONG PROMISE SPINE" in names1 and "OTHER TENANT BRAND" not in names1
    assert "OTHER TENANT BRAND" in names2 and "MEKONG PROMISE SPINE" not in names2
