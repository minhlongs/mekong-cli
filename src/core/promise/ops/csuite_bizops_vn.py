# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts for C-Suite & Business Operations (Wave 3A).

Registers the twelve C-Suite and Business Operations contracts across six commands:

* ``founder.assess-profile`` — assess founder psychometric blueprint and record L0 attestation
* ``founder.analyze-profile`` — synthesize founder strengths, blindspots, and executive pairing
* ``marketing.create-campaign`` — launch marketing campaign and record L1/L3 offer & channel evidence
* ``marketing.seo-audit`` — run SEO/market research audit with verified provenance for L1 gate
* ``sales.add-deal`` — register a new deal opportunity in ``sales.db``
* ``sales.close-deal`` — close deal to WON in ``sales.db`` and record L4 client acceptance
* ``cto.create-adr`` — generate and export ADR in ``cto.db`` and record L5 SOP export & clone attestation
* ``cto.security-review`` — run security/code audit in ``cto.db`` and record L2 deployment proof
* ``ops.health-sweep`` — execute workspace health sweep and persist in ``ops.db``
* ``ops.create-incident`` — create and track an SRE incident in ``ops.db``
* ``billing.record-usage`` — record idempotent billable usage event in ``billing.db``
* ``billing.reconcile-usage`` — reconcile usage events and record variance ledger in ``billing.db``
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_wave3_ops.py"

FOUNDER_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="founder.assess-profile",
        command="founder",
        subcommand="assess_profile",
        title="Đánh giá hồ sơ tâm lý & kiến trúc năng lực Nhà sáng lập (L0 Blueprint)",
        description=(
            "Assess founder psychometric profile (Big Five, Schwartz values, risk appetite, cognitive biases), "
            "persist to workspace founder.db, and record a FOUNDER_BLUEPRINT attestation for the L0 gate."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 120},
                "mission": {
                    "type": "string",
                    "minLength": 5,
                    "maxLength": 500,
                    "default": "Xây dựng doanh nghiệp AI một người tự vận hành chuẩn mực tại Việt Nam",
                },
                "values": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "risk_ratings": {"type": "object"},
                "bias_responses": {"type": "object"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:founder_assess_profile",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/founder.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["id", "name", "archetype", "risk_level", "attestation_id"]},
            ),
            Postcondition("echoes_input", {"param_path": "name", "result_path": "name"}),
            Postcondition("record_persisted", {"table": "founders", "id_path": "id"}),
        ),
        sop_steps=("assess-psychometrics", "classify-archetype", "persist-founder", "attest-l0-blueprint"),
        department_id="ceo-command",
        layer_id="L1",
        gate_id="company-blueprint",
        jurisdiction="VN",
        rule_version="Founder Psychometric Blueprint v1",
        output_contract={"evidence_type": "FOUNDER_INTENT_BLUEPRINT"},
        test_id=f"{TEST_MODULE}::test_founder_assess_and_analyze_profile_seal_l0_gate",
    ),
    OperationSpec(
        op_id="founder.analyze-profile",
        command="founder",
        subcommand="analyze_profile",
        title="Phân tích điểm mạnh, điểm mù & khuyến nghị ghép cặp C-Suite cho Nhà sáng lập",
        description=(
            "Synthesize founder strengths, blindspots, executive pairing recommendations, and "
            "bias mitigations from workspace founder.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name_or_id": {"type": "string", "minLength": 2, "maxLength": 120},
            },
            "required": ["name_or_id"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:founder_analyze_profile",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/founder.db",),
        external_effect="NONE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "success",
                        "id",
                        "name",
                        "archetype",
                        "risk_level",
                        "strengths",
                        "blindspots",
                        "strategic_recommendations",
                    ]
                },
            ),
        ),
        sop_steps=("load-founder", "synthesize-blindspots", "recommend-csuite-pairings"),
        department_id="ceo-command",
        layer_id="L1",
        jurisdiction="VN",
        rule_version="Founder Psychometric Blueprint v1",
        output_contract={"evidence_type": "FOUNDER_ANALYSIS_REPORT"},
        test_id=f"{TEST_MODULE}::test_founder_assess_and_analyze_profile_seal_l0_gate",
    ),
)

MARKETING_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="marketing.create-campaign",
        command="marketing",
        subcommand="create_campaign",
        title="Khởi tạo chiến dịch Marketing & ghi nhận bằng chứng ICP/Kênh lặp lại (L1/L3)",
        description=(
            "Create a marketing campaign in workspace marketing.db and record OFFER_VALIDATED "
            "and CHANNEL_REPEATABLE attestations plus channel_metrics for L1/L3 gates."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 160},
                "channel": {
                    "type": "string",
                    "enum": ["social", "search", "content", "email", "local", "zalo"],
                    "default": "social",
                },
                "budget": {"type": "number", "minimum": 0, "default": 1000.0},
                "target_audience": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 200,
                    "default": "SME Founders & CFOs in Vietnam",
                },
                "period": {"type": "string", "minLength": 4, "maxLength": 32, "default": "2026-Q4"},
                "conversions": {"type": "integer", "minimum": 1, "default": 12},
                "impressions": {"type": "integer", "minimum": 1, "default": 1500},
                "clicks": {"type": "integer", "minimum": 1, "default": 210},
                "revenue": {"type": "string", "default": "25000000"},
                "currency": {"type": "string", "enum": ["VND", "USD"], "default": "VND"},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:marketing_create_campaign",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/marketing.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "id",
                        "name",
                        "channel",
                        "budget",
                        "offer_attestation_id",
                        "channel_metric_id",
                        "channel_attestation_id",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "name", "result_path": "name"}),
            Postcondition("value_bounds", {"path": "conversions", "min": 1}),
            Postcondition("record_persisted", {"table": "campaigns", "id_path": "id"}),
        ),
        sop_steps=("create-campaign", "record-offer-validation", "record-channel-metrics", "attest-channel"),
        department_id="marketing-growth",
        layer_id="L2",
        gate_id="offer-validated",
        jurisdiction="VN",
        rule_version="Marketing Growth Playbook v1",
        output_contract={"evidence_type": "MARKET_ICP_OFFER_CONTRACT"},
        test_id=f"{TEST_MODULE}::test_marketing_campaign_and_seo_audit_seal_l1_and_repeatable_channel_gates",
    ),
    OperationSpec(
        op_id="marketing.seo-audit",
        command="marketing",
        subcommand="seo_audit",
        title="Kiểm toán SEO & nghiên cứu từ khóa thị trường có truy xuất nguồn gốc (L1)",
        description=(
            "Generate a technical SEO keyword & market research report, persist to workspace marketing.db, "
            "and attach provenance metadata (sources, retrieved_at, confidence) required by the L1 gate."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "minLength": 2, "maxLength": 160},
                "domain": {"type": "string", "minLength": 3, "maxLength": 120, "default": "mekong.vn"},
            },
            "required": ["keyword"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:marketing_seo_audit",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/marketing.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "audit_id",
                        "keyword",
                        "domain",
                        "recommended_title",
                        "sources",
                        "retrieved_at",
                        "confidence",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "keyword", "result_path": "keyword"}),
            Postcondition("provenance_recorded", {}),
            Postcondition(
                "record_persisted",
                {"table": "seo_audits", "id_path": "audit_id", "id_column": "audit_id"},
            ),
        ),
        sop_steps=("analyze-serp", "build-seo-audit", "persist-audit", "verify-provenance"),
        department_id="marketing-growth",
        layer_id="L2",
        gate_id="offer-validated",
        jurisdiction="VN",
        rule_version="Marketing SEO Audit v1",
        output_contract={"evidence_type": "MARKET_RESEARCH"},
        test_id=f"{TEST_MODULE}::test_marketing_campaign_and_seo_audit_seal_l1_and_repeatable_channel_gates",
    ),
)

SALES_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="sales.add-deal",
        command="sales",
        subcommand="add_deal",
        title="Thêm cơ hội bán hàng (Deal) vào phễu doanh thu",
        description="Register a new B2B sales deal opportunity in workspace sales.db.",
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 2, "maxLength": 160},
                "company": {"type": "string", "minLength": 2, "maxLength": 160},
                "value": {"type": "number", "minimum": 1},
                "stage": {
                    "type": "string",
                    "enum": ["lead", "qualified", "proposal", "negotiation", "won", "lost"],
                    "default": "proposal",
                },
                "contact_email": {"type": "string", "default": "cfo@client.vn"},
                "notes": {"type": "string", "default": ""},
            },
            "required": ["name", "company", "value"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.sales_engine",
            factory="SalesEngine",
            method="add_deal",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/sales.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["id", "name", "company", "value", "stage"]},
            ),
            Postcondition("echoes_input", {"param_path": "company", "result_path": "company"}),
            Postcondition("value_bounds", {"path": "value", "min": 1}),
            Postcondition("record_persisted", {"table": "deals", "id_path": "id"}),
        ),
        sop_steps=("validate-deal", "compute-weighted-value", "persist-deal"),
        department_id="sales-revenue",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="B2B Sales Pipeline v1",
        output_contract={"evidence_type": "SALES_PIPELINE_DEAL"},
        test_id=f"{TEST_MODULE}::test_sales_add_and_close_deal_seal_l4_fulfillment_gate",
    ),
    OperationSpec(
        op_id="sales.close-deal",
        command="sales",
        subcommand="close_deal",
        title="Chốt thành công hợp đồng (WON) & ghi nhận nghiệm thu khách hàng (L4)",
        description=(
            "Transition deal to WON in workspace sales.db, generate onboarding checklist, "
            "and record SLA-verified client acceptance for the L4 fulfillment-stable gate."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "deal_id": {"type": "string", "minLength": 4, "maxLength": 64},
                "sla_met": {"type": "boolean", "default": True},
            },
            "required": ["deal_id"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:sales_close_deal",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/sales.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "deal_id",
                        "company",
                        "final_value",
                        "stage",
                        "onboarding_checklist",
                        "acceptance_id",
                    ]
                },
            ),
            Postcondition("enum_member", {"path": "stage", "allowed": ["won"]}),
            Postcondition("record_persisted", {"table": "deals", "id_path": "deal_id"}),
        ),
        sop_steps=("close-deal-won", "generate-onboarding", "record-client-acceptance"),
        department_id="sales-revenue",
        layer_id="L2",
        gate_id="fulfillment-stable",
        jurisdiction="VN",
        rule_version="B2B Sales Fulfillment v1",
        output_contract={"evidence_type": "FULFILLMENT_DELIVERY"},
        test_id=f"{TEST_MODULE}::test_sales_add_and_close_deal_seal_l4_fulfillment_gate",
    ),
)

CTO_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="cto.create-adr",
        command="cto",
        subcommand="create_adr",
        title="Khởi tạo quyết định kiến trúc (ADR) & xuất bản gói SOP nhân bản (L5)",
        description=(
            "Generate an Architectural Decision Record, export markdown artifact, persist to cto.db, "
            "and record SOP export + CLONE_READY attestation for the L5 scale-ready gate."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 180},
                "decision": {"type": "string", "default": ""},
                "consequences": {"type": "string", "default": ""},
                "clone_target": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 80,
                    "default": "opc-clone-template",
                },
            },
            "required": ["title"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:cto_create_adr",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/cto.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "adr_id",
                        "title",
                        "status",
                        "artifact_path",
                        "artifact_digest",
                        "sop_export_id",
                        "clone_attestation_id",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "title", "result_path": "title"}),
            Postcondition("artifact_written", {"path_from_result": "artifact_path", "min_bytes": 10}),
            Postcondition(
                "record_persisted",
                {"table": "adrs", "id_path": "adr_id", "id_column": "adr_id"},
            ),
        ),
        sop_steps=("draft-adr", "export-markdown", "persist-adr", "record-sop-export", "attest-clone-ready"),
        department_id="engineering-factory",
        layer_id="L3",
        gate_id="scale-ready",
        jurisdiction="VN",
        rule_version="CTO Architecture ADR & Clone SOP v1",
        output_contract={"evidence_type": "ENTERPRISE_SOP_CLONE_SYNC"},
        test_id=f"{TEST_MODULE}::test_cto_adr_and_security_review_seal_l2_and_l5_gates",
    ),
    OperationSpec(
        op_id="cto.security-review",
        command="cto",
        subcommand="security_review",
        title="Kiểm toán bảo mật mã nguồn & ghi nhận bằng chứng triển khai MVP (L2)",
        description=(
            "Execute deterministic code and security audit, persist to cto.db, and record a "
            "HEALTHY deployment proof for the L2 mvp-live gate."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "target_url": {
                    "type": "string",
                    "minLength": 8,
                    "maxLength": 200,
                    "default": "https://app.mekong.vn/health",
                },
                "environment": {
                    "type": "string",
                    "enum": ["production", "staging"],
                    "default": "production",
                },
                "max_findings": {"type": "integer", "minimum": 1, "maximum": 200, "default": 20},
            },
            "required": [],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:cto_security_review",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/cto.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "audit_id",
                        "files_scanned",
                        "passed",
                        "build_digest",
                        "test_digest",
                        "proof_id",
                    ]
                },
            ),
            Postcondition("value_bounds", {"path": "files_scanned", "min": 1}),
            Postcondition(
                "record_persisted",
                {"table": "security_audits", "id_path": "audit_id", "id_column": "audit_id"},
            ),
        ),
        sop_steps=("scan-codebase", "evaluate-findings", "persist-security-audit", "record-deployment-proof"),
        department_id="engineering-factory",
        layer_id="L3",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="CTO Security Gate v1",
        output_contract={"evidence_type": "SECURITY_AUDIT"},
        test_id=f"{TEST_MODULE}::test_cto_adr_and_security_review_seal_l2_and_l5_gates",
    ),
)

OPS_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="ops.health-sweep",
        command="ops",
        subcommand="health_sweep",
        title="Quét tổng thể sức khỏe vận hành hệ thống & toàn vẹn cơ sở dữ liệu",
        description="Run SRE health sweep across runtime, disk, SQLite databases, and git status in ops.db.",
        input_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_csuite_bizops:ops_health_sweep",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/ops.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["sweep_id", "overall_status", "score", "checks", "summary"]},
            ),
            Postcondition(
                "enum_member",
                {"path": "overall_status", "allowed": ["HEALTHY", "DEGRADED", "CRITICAL"]},
            ),
            Postcondition("value_bounds", {"path": "score", "min": 0, "max": 100}),
            Postcondition("record_persisted", {"table": "health_sweeps", "id_path": "sweep_id"}),
        ),
        sop_steps=("probe-runtime", "verify-sqlite-integrity", "score-health", "persist-sweep"),
        department_id="reliability-ops",
        layer_id="L4",
        jurisdiction="VN",
        rule_version="Mekong SRE Health Sweep v1",
        output_contract={"evidence_type": "SRE_HEALTH_SWEEP"},
        test_id=f"{TEST_MODULE}::test_ops_health_sweep_and_incident_persist_to_workspace_db",
    ),
    OperationSpec(
        op_id="ops.create-incident",
        command="ops",
        subcommand="create_incident",
        title="Khởi tạo và theo dõi sự cố vận hành (SRE Incident)",
        description="Create and track an SRE operational incident in workspace ops.db.",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 180},
                "severity": {
                    "type": "string",
                    "enum": ["SEV1", "SEV2", "SEV3", "SEV4"],
                    "default": "SEV3",
                },
                "service": {"type": "string", "minLength": 2, "maxLength": 80, "default": "api-gateway"},
                "summary": {"type": "string", "default": ""},
            },
            "required": ["title"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.ops_engine",
            factory="OpsEngine",
            method="create_incident",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/ops.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["id", "title", "severity", "service", "status", "created_at"]},
            ),
            Postcondition("echoes_input", {"param_path": "title", "result_path": "title"}),
            Postcondition("enum_member", {"path": "status", "allowed": ["OPEN"]}),
            Postcondition("record_persisted", {"table": "incidents", "id_path": "id"}),
        ),
        sop_steps=("classify-severity", "open-incident", "persist-incident"),
        department_id="reliability-ops",
        layer_id="L4",
        jurisdiction="VN",
        rule_version="Mekong SRE Incident Response v1",
        output_contract={"evidence_type": "SRE_INCIDENT_RECORD"},
        test_id=f"{TEST_MODULE}::test_ops_health_sweep_and_incident_persist_to_workspace_db",
    ),
)

BILLING_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="billing.record-usage",
        command="billing",
        subcommand="record_usage",
        title="Ghi nhận sự kiện tiêu thụ tài nguyên (Metered Billing Usage)",
        description=(
            "Ingest a billable usage event with idempotency deduplication and tier rate pricing in billing.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "license_key": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 120,
                    "default": "mekong_lic_scale_01",
                },
                "event_type": {
                    "type": "string",
                    "enum": ["llm_tokens", "agent_minutes", "api_calls", "storage_mb", "mcu_credits"],
                    "default": "agent_minutes",
                },
                "quantity": {"type": "number", "minimum": 0.01},
                "idempotency_key": {"type": "string", "default": ""},
                "tier": {
                    "type": "string",
                    "enum": ["free", "developer", "pro", "enterprise"],
                    "default": "pro",
                },
            },
            "required": ["license_key", "event_type", "quantity"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.billing_engine",
            factory="BillingEngine",
            method="record_usage",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/billing.db",),
        external_effect="RECORD_AUDIT_LEDGER",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "id",
                        "license_key",
                        "event_type",
                        "quantity",
                        "unit_cost",
                        "total_cost",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "license_key", "result_path": "license_key"}),
            Postcondition("value_bounds", {"path": "quantity", "min": 0.01}),
            Postcondition("record_persisted", {"table": "billing_events", "id_path": "id"}),
        ),
        sop_steps=("check-idempotency", "price-usage", "persist-billing-event"),
        department_id="finance-legal",
        layer_id="L4",
        jurisdiction="VN",
        rule_version="Mekong Usage Metering v1",
        output_contract={"evidence_type": "BILLING_USAGE_EVENT"},
        test_id=f"{TEST_MODULE}::test_billing_record_and_reconcile_usage_persist_to_workspace_db",
    ),
    OperationSpec(
        op_id="billing.reconcile-usage",
        command="billing",
        subcommand="reconcile_usage",
        title="Đối soát sản lượng tiêu thụ & kiểm toán chênh lệch cước phí",
        description="Audit recorded usage events for anomalies and persist a reconciliation record in billing.db.",
        input_schema={
            "type": "object",
            "properties": {
                "license_key": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 120,
                    "default": "mekong_lic_scale_01",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.billing_engine",
            factory="BillingEngine",
            method="reconcile_usage",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/billing.db",),
        external_effect="RECORD_AUDIT_LEDGER",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "reconciliation_id",
                        "license_key",
                        "events_reconciled",
                        "total_accrued_usd",
                        "status",
                    ]
                },
            ),
            Postcondition("enum_member", {"path": "status", "allowed": ["clean", "variance_detected"]}),
            Postcondition(
                "record_persisted",
                {"table": "reconciliations", "id_path": "reconciliation_id"},
            ),
        ),
        sop_steps=("aggregate-usage", "detect-anomalies", "persist-reconciliation"),
        department_id="finance-legal",
        layer_id="L4",
        jurisdiction="VN",
        rule_version="Mekong Usage Reconciliation v1",
        output_contract={"evidence_type": "BILLING_RECONCILIATION"},
        test_id=f"{TEST_MODULE}::test_billing_record_and_reconcile_usage_persist_to_workspace_db",
    ),
)

CSUITE_BIZOPS_OPERATIONS: tuple[OperationSpec, ...] = (
    *FOUNDER_OPS,
    *MARKETING_OPS,
    *SALES_OPS,
    *CTO_OPS,
    *OPS_OPS,
    *BILLING_OPS,
)

__all__ = [
    "BILLING_OPS",
    "CSUITE_BIZOPS_OPERATIONS",
    "CTO_OPS",
    "FOUNDER_OPS",
    "MARKETING_OPS",
    "OPS_OPS",
    "SALES_OPS",
]
