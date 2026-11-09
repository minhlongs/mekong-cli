# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts for Vietnamese Legal & Statutory Operations (Wave 3B).

Registers nine statutory operations across three commands:

* ``corporate.generate-charter`` — 10-chapter Corporate Charter under Art. 24 Law on Enterprises 2020
* ``corporate.generate-resolution`` — Board / Member Council resolution in ``corporate.db``
* ``corporate.incorporate`` — full incorporation dossier under Decree 01/2021/NĐ-CP
* ``labor.assess-work-permit`` — foreign worker work-permit / exemption evaluation under Decree 70/2023/NĐ-CP
* ``labor.calculate-overtime`` — overtime pay & cap validation under Art. 98 & 107 Labor Code 2019
* ``labor.audit-regulations`` — Internal Labor Regulations & DOLAB filing audit under Art. 118 & 119
* ``contract.draft`` — statutory commercial/labor/NDA contract draft in ``contracts.db``
* ``contract.review`` — legal risk & redline assessment (8% penalty cap under Art. 301 Commercial Law)
* ``contract.sign`` — SHA-256 electronic signature under Law on Electronic Transactions 2023 (gated by ``FOUNDER_CONFIRMATION``)
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_wave3_ops.py"

CORPORATE_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="corporate.generate-charter",
        command="corporate",
        subcommand="generate_charter",
        title="Soạn Điều lệ công ty 10 Chương theo Điều 24 Luật Doanh nghiệp 2020",
        description=(
            "Synthesize a complete 10-chapter Corporate Charter complying with Article 24 "
            "Law on Enterprises 2020 and persist to workspace corporate.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "entity_type": {
                    "type": "string",
                    "enum": ["TNHH_1TV", "TNHH_2TV", "JSC"],
                    "default": "TNHH_1TV",
                },
                "charter_capital": {
                    "type": "integer",
                    "minimum": 10_000_000,
                    "default": 1_000_000_000,
                },
                "legal_rep_name": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 120,
                    "default": "Nguyễn Văn A",
                },
                "address": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 240,
                    "default": "Hà Nội, Việt Nam",
                },
                "industry_codes": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["company_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.corporate_engine",
            factory="CorporateEngine",
            method="generate_charter",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/corporate.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "charter_id",
                        "entity_id",
                        "company_name",
                        "chapters_count",
                        "articles_count",
                        "content_markdown",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "company_name", "result_path": "company_name"}),
            Postcondition("value_bounds", {"path": "chapters_count", "min": 10, "max": 10}),
            Postcondition(
                "record_persisted",
                {"table": "statutory_documents", "id_path": "charter_id", "id_column": "doc_id"},
            ),
        ),
        sop_steps=("validate-entity-type", "render-10-chapters", "persist-charter"),
        department_id="legal-compliance",
        layer_id="L1",
        jurisdiction="VN",
        rule_version="Luật Doanh nghiệp 59/2020/QH14 Điều 24",
        statutory_basis=("Luật Doanh nghiệp 59/2020/QH14", "Nghị định 01/2021/NĐ-CP"),
        output_contract={"evidence_type": "CORPORATE_CHARTER"},
        test_id=f"{TEST_MODULE}::test_corporate_charter_resolution_and_incorporation_persist",
    ),
    OperationSpec(
        op_id="corporate.generate-resolution",
        command="corporate",
        subcommand="generate_resolution",
        title="Soạn Nghị quyết Hội đồng thành viên / Đại hội đồng cổ đông",
        description=(
            "Synthesize a statutory Board or Member Council resolution (Appointment, Capital Increase, "
            "or Branch Establishment) and persist to workspace corporate.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "resolution_type": {
                    "type": "string",
                    "enum": ["APPOINTMENT", "CAPITAL_INCREASE", "BRANCH"],
                    "default": "APPOINTMENT",
                },
                "title": {"type": "string", "default": ""},
                "decisions": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["company_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.corporate_engine",
            factory="CorporateEngine",
            method="generate_resolution",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/corporate.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "resolution_id",
                        "company_name",
                        "resolution_type",
                        "decisions_count",
                        "content_markdown",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "company_name", "result_path": "company_name"}),
            Postcondition("value_bounds", {"path": "decisions_count", "min": 1}),
            Postcondition(
                "record_persisted",
                {"table": "statutory_documents", "id_path": "resolution_id", "id_column": "doc_id"},
            ),
        ),
        sop_steps=("draft-decisions", "format-resolution", "persist-resolution"),
        department_id="legal-compliance",
        layer_id="L1",
        jurisdiction="VN",
        rule_version="Luật Doanh nghiệp 59/2020/QH14",
        statutory_basis=("Luật Doanh nghiệp 59/2020/QH14",),
        output_contract={"evidence_type": "CORPORATE_RESOLUTION"},
        test_id=f"{TEST_MODULE}::test_corporate_charter_resolution_and_incorporation_persist",
    ),
    OperationSpec(
        op_id="corporate.incorporate",
        command="corporate",
        subcommand="incorporate",
        title="Tổng hợp bộ hồ sơ đăng ký thành lập doanh nghiệp theo Nghị định 01/2021/NĐ-CP",
        description=(
            "Synthesize full incorporation filing dossier (Application Form, 10-chapter Charter, "
            "Member List, and Legal Rep Appointment Resolution) in workspace corporate.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "entity_type": {
                    "type": "string",
                    "enum": ["TNHH_1TV", "TNHH_2TV", "JSC"],
                    "default": "TNHH_1TV",
                },
                "charter_capital": {
                    "type": "integer",
                    "minimum": 10_000_000,
                    "default": 1_000_000_000,
                },
                "legal_rep_name": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 120,
                    "default": "Nguyễn Văn A",
                },
                "address": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 240,
                    "default": "Hà Nội, Việt Nam",
                },
                "main_industry": {"type": "string", "minLength": 4, "maxLength": 10, "default": "6201"},
            },
            "required": ["company_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_vn:corporate_incorporate",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/corporate.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "dossier_id",
                        "company_name",
                        "documents",
                        "documents_count",
                        "filing_portal",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "company_name", "result_path": "company_name"}),
            Postcondition("value_bounds", {"path": "documents_count", "min": 4}),
            Postcondition(
                "record_persisted",
                {"table": "statutory_documents", "id_path": "dossier_id", "id_column": "doc_id"},
            ),
        ),
        sop_steps=("generate-charter", "generate-appointment", "assemble-dossier", "persist-dossier"),
        department_id="legal-compliance",
        layer_id="L1",
        jurisdiction="VN",
        rule_version="Nghị định 01/2021/NĐ-CP & Thông tư 01/2021/TT-BKHĐT",
        statutory_basis=("Luật Doanh nghiệp 59/2020/QH14", "Nghị định 01/2021/NĐ-CP"),
        output_contract={"evidence_type": "INCORPORATION_DOSSIER"},
        test_id=f"{TEST_MODULE}::test_corporate_charter_resolution_and_incorporation_persist",
    ),
)

LABOR_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="labor.assess-work-permit",
        command="labor",
        subcommand="assess_work_permit",
        title="Đánh giá điều kiện cấp/miễn Giấy phép lao động nước ngoài (Nghị định 70/2023/NĐ-CP)",
        description=(
            "Evaluate foreign worker work-permit eligibility or statutory exemption under "
            "Decree 152/2020/NĐ-CP and Decree 70/2023/NĐ-CP and persist to workspace labor.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "worker_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "nationality": {"type": "string", "minLength": 2, "maxLength": 80},
                "position_category": {
                    "type": "string",
                    "enum": ["EXPERT", "EXECUTIVE_DIRECTOR", "MANAGING_DIRECTOR", "TECHNICAL_WORKER"],
                    "default": "EXPERT",
                },
                "job_title": {"type": "string", "minLength": 2, "maxLength": 160},
                "education_degree": {"type": "string", "default": "BACHELOR"},
                "experience_years": {"type": "number", "minimum": 0, "default": 3.0},
                "capital_contribution_vnd": {"type": "number", "minimum": 0, "default": 0.0},
                "is_wto_internal_transfer": {"type": "boolean", "default": False},
                "married_to_vietnamese": {"type": "boolean", "default": False},
                "passport_number": {"type": "string", "minLength": 3, "default": "PASS-DEFAULT"},
            },
            "required": ["worker_name", "nationality", "job_title"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.labor_engine",
            factory="LaborEngine",
            method="evaluate_work_permit_eligibility",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/labor.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "worker_id",
                        "application_id",
                        "worker_name",
                        "eligibility_status",
                        "statutory_dossier_checklist",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "worker_name", "result_path": "worker_name"}),
            Postcondition(
                "enum_member",
                {"path": "eligibility_status", "allowed": ["QUALIFIED", "DISQUALIFIED"]},
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "work_permit_applications",
                    "id_path": "application_id",
                    "id_column": "application_id",
                },
            ),
        ),
        sop_steps=("check-exemptions", "verify-qualifications", "persist-application"),
        department_id="legal-compliance",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Nghị định 152/2020/NĐ-CP & Nghị định 70/2023/NĐ-CP",
        statutory_basis=("Bộ luật Lao động 45/2019/QH14", "Nghị định 70/2023/NĐ-CP"),
        output_contract={"evidence_type": "WORK_PERMIT_ASSESSMENT"},
        test_id=f"{TEST_MODULE}::test_labor_work_permit_overtime_and_regulations_persist",
    ),
    OperationSpec(
        op_id="labor.calculate-overtime",
        command="labor",
        subcommand="calculate_overtime",
        title="Tính lương làm thêm giờ & kiểm định trần OT theo Điều 98, 107 Bộ luật Lao động 2019",
        description=(
            "Calculate statutory overtime and night-shift pay (150%/200%/300% + 30%/20% night premiums) "
            "and verify 40h/month and 200h–300h/year caps in workspace labor.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "employee_name": {"type": "string", "minLength": 2, "default": "Nguyễn Văn B"},
                "month_year": {"type": "string", "minLength": 4, "default": "2026-11"},
                "hourly_rate_vnd": {"type": "number", "minimum": 1000.0},
                "normal_day_ot_hours": {"type": "number", "minimum": 0, "default": 0.0},
                "weekend_ot_hours": {"type": "number", "minimum": 0, "default": 0.0},
                "holiday_ot_hours": {"type": "number", "minimum": 0, "default": 0.0},
                "night_shift_regular_hours": {"type": "number", "minimum": 0, "default": 0.0},
                "night_shift_ot_hours": {"type": "number", "minimum": 0, "default": 0.0},
                "yearly_cumulative_hours": {"type": "number", "minimum": 0, "default": 100.0},
                "is_extended_industry": {"type": "boolean", "default": False},
            },
            "required": ["hourly_rate_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_vn:labor_calculate_overtime",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/labor.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "record_id",
                        "employee_name",
                        "total_overtime_hours",
                        "total_overtime_pay_vnd",
                        "is_compliant",
                        "governing_article",
                    ]
                },
            ),
            Postcondition("value_bounds", {"path": "total_overtime_pay_vnd", "min": 0}),
            Postcondition(
                "record_persisted",
                {"table": "overtime_records", "id_path": "record_id", "id_column": "record_id"},
            ),
        ),
        sop_steps=("compute-multipliers", "check-ot-caps", "persist-overtime"),
        department_id="legal-compliance",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Bộ luật Lao động 2019 Điều 98 & Điều 107",
        statutory_basis=("Bộ luật Lao động 45/2019/QH14 Điều 98, 107",),
        output_contract={"evidence_type": "OVERTIME_COMPLIANCE_LEDGER"},
        test_id=f"{TEST_MODULE}::test_labor_work_permit_overtime_and_regulations_persist",
    ),
    OperationSpec(
        op_id="labor.audit-regulations",
        command="labor",
        subcommand="audit_regulations",
        title="Kiểm toán Nội quy lao động & đăng ký Sở LĐ-TB&XH (Điều 118, 119 BLLĐ 2019)",
        description=(
            "Audit corporate Internal Labor Regulations and DOLAB registration compliance for "
            "enterprises with >= 10 employees and persist to workspace labor.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "enterprise_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "total_employees": {"type": "integer", "minimum": 1},
                "has_written_regulations": {"type": "boolean", "default": True},
                "is_registered_with_dolab": {"type": "boolean", "default": True},
                "has_dialogue_mechanism": {"type": "boolean", "default": True},
                "has_safety_council": {"type": "boolean", "default": True},
                "dolab_filing_number": {"type": "string", "default": "NQLD-2026-DOLAB"},
            },
            "required": ["enterprise_name", "total_employees"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.labor_engine",
            factory="LaborEngine",
            method="audit_internal_regulations",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/labor.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "regulation_id",
                        "enterprise_name",
                        "total_employees",
                        "compliance_status",
                        "statutory_notes",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "enterprise_name", "result_path": "enterprise_name"}),
            Postcondition(
                "enum_member",
                {"path": "compliance_status", "allowed": ["FULLY_COMPLIANT", "NON_COMPLIANT"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "internal_regulations", "id_path": "regulation_id", "id_column": "regulation_id"},
            ),
        ),
        sop_steps=("check-headcount-threshold", "verify-dolab-filing", "persist-regulation-audit"),
        department_id="legal-compliance",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Bộ luật Lao động 2019 Điều 118 & Điều 119",
        statutory_basis=("Bộ luật Lao động 45/2019/QH14 Điều 118, 119",),
        output_contract={"evidence_type": "LABOR_REGULATION_AUDIT"},
        test_id=f"{TEST_MODULE}::test_labor_work_permit_overtime_and_regulations_persist",
    ),
)

CONTRACT_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="contract.draft",
        command="contract",
        subcommand="draft",
        title="Soạn thảo hợp đồng thương mại / lao động / NDA chuẩn pháp luật Việt Nam",
        description=(
            "Draft a bilingual-ready commercial, SaaS, NDA, labor, or partnership contract "
            "with SHA-256 content digest and initial statutory risk score in workspace contracts.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "template_type": {
                    "type": "string",
                    "enum": ["SOFTWARE_DEV", "COMMERCIAL_SALE", "NDA", "DISTRIBUTION"],
                    "default": "COMMERCIAL_SALE",
                },
                "party_a_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "party_b_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "contract_value_vnd": {"type": "number", "minimum": 0, "default": 120_000_000.0},
                "party_a_tax_id": {"type": "string", "minLength": 8, "default": "0109998881"},
                "party_b_tax_id": {"type": "string", "minLength": 8, "default": "0318887772"},
                "scope_summary": {"type": "string", "default": ""},
                "penalty_rate_pct": {"type": "number", "minimum": 0, "maximum": 100, "default": 8.0},
                "dispute_forum": {"type": "string", "minLength": 2, "default": "VIAC"},
            },
            "required": ["party_a_name", "party_b_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_vn:contract_draft",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/contracts.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "contract_id",
                        "contract_number",
                        "party_a_name",
                        "party_b_name",
                        "content_sha256",
                        "risk_level",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "party_a_name", "result_path": "party_a_name"}),
            Postcondition("enum_member", {"path": "status", "allowed": ["DRAFTED"]}),
            Postcondition(
                "record_persisted",
                {"table": "contracts", "id_path": "contract_id", "id_column": "contract_id"},
            ),
        ),
        sop_steps=("select-template", "synthesize-clauses", "hash-sha256", "persist-contract"),
        department_id="legal-compliance",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Bộ luật Dân sự 91/2015/QH13 & Luật Thương mại 36/2005/QH11",
        statutory_basis=("Bộ luật Dân sự 91/2015/QH13", "Luật Thương mại 36/2005/QH11"),
        output_contract={"evidence_type": "COMMERCIAL_CONTRACT_DRAFT"},
        test_id=f"{TEST_MODULE}::test_contract_draft_review_and_founder_gated_signature",
    ),
    OperationSpec(
        op_id="contract.review",
        command="contract",
        subcommand="review",
        title="Rà soát rủi ro pháp lý hợp đồng (trần phạt 8% Điều 301 LTM, Bất khả kháng, Nghị định 13)",
        description=(
            "Scan contract clauses for Vietnamese statutory violations (penalty > 8% cap under "
            "Art. 301 Commercial Law 2005, missing Force Majeure, IP ownership, Decree 13/2023 PDPD) "
            "and persist review to workspace contracts.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "default": ""},
                "contract_text": {"type": "string", "default": ""},
                "penalty_pct": {"type": "number", "minimum": 0, "maximum": 100},
            },
            "required": [],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_vn:contract_review",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/contracts.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "review_id",
                        "contract_id",
                        "risk_score",
                        "risk_level",
                        "red_flags",
                        "recommendations",
                    ]
                },
            ),
            Postcondition("enum_member", {"path": "risk_level", "allowed": ["LOW", "MEDIUM", "HIGH"]}),
            Postcondition("value_bounds", {"path": "risk_score", "min": 0, "max": 100}),
            Postcondition(
                "record_persisted",
                {"table": "contract_reviews", "id_path": "review_id", "id_column": "review_id"},
            ),
        ),
        sop_steps=("scan-penalty-cap", "check-force-majeure", "check-pdpd", "persist-review"),
        department_id="legal-compliance",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Luật Thương mại 2005 Điều 301 & Nghị định 13/2023/NĐ-CP",
        statutory_basis=("Luật Thương mại 36/2005/QH11 Điều 294, 301, 317", "Nghị định 13/2023/NĐ-CP"),
        output_contract={"evidence_type": "CONTRACT_RISK_REVIEW"},
        test_id=f"{TEST_MODULE}::test_contract_draft_review_and_founder_gated_signature",
    ),
    OperationSpec(
        op_id="contract.sign",
        command="contract",
        subcommand="sign",
        title="Ký số điện tử SHA-256 hợp đồng theo Luật Giao dịch điện tử 2023 (cổng phê duyệt Founder)",
        description=(
            "Sign a contract electronically with SHA-256 cryptographic digest and TSA timestamp "
            "under Law on Electronic Transactions 20/2023/QH15 after FOUNDER_CONFIRMATION."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "minLength": 3, "maxLength": 80},
                "signer_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "signer_title": {"type": "string", "default": "Giám đốc điều hành"},
                "signer_tax_id": {"type": "string", "minLength": 8, "default": "0109998881"},
                "organization_name": {"type": "string", "default": ""},
            },
            "required": ["contract_id", "signer_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_vn:contract_sign",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/contracts.db",),
        external_effect="FILE_SUBMISSION",
        approval_policy="FOUNDER_CONFIRMATION",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "signature_id",
                        "contract_id",
                        "signer_name",
                        "signature_hash",
                        "tsa_timestamp",
                        "legal_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "signer_name", "result_path": "signer_name"}),
            Postcondition(
                "enum_member",
                {"path": "legal_status", "allowed": ["VALID_ELECTRONIC_SIGNATURE"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "e_signatures", "id_path": "signature_id", "id_column": "signature_id"},
            ),
        ),
        sop_steps=("founder-approval", "compute-sha256-signature", "stamp-tsa", "persist-signature"),
        department_id="legal-compliance",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Luật Giao dịch điện tử 20/2023/QH15 & Nghị định 130/2018/NĐ-CP",
        statutory_basis=("Luật Giao dịch điện tử 20/2023/QH15", "Nghị định 130/2018/NĐ-CP"),
        output_contract={"evidence_type": "ELECTRONIC_SIGNATURE_RECEIPT"},
        test_id=f"{TEST_MODULE}::test_contract_draft_review_and_founder_gated_signature",
    ),
)

LEGAL_VN_OPERATIONS: tuple[OperationSpec, ...] = (
    *CORPORATE_OPS,
    *LABOR_OPS,
    *CONTRACT_OPS,
)

__all__ = [
    "CONTRACT_OPS",
    "CORPORATE_OPS",
    "LABOR_OPS",
    "LEGAL_VN_OPERATIONS",
]
