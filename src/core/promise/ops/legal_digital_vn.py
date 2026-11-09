# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts for Vietnamese Digital, E-Commerce & IP Legal Operations (Wave 4B).

Registers six statutory operations across three commands:

* ``privacy.assess-dpia`` — DPIA Form 04-A05 under Article 24 Decree 13/2023/NĐ-CP (PDPD)
* ``privacy.process-dsar`` — Data Subject Request under Art. 9–16 Decree 13/2023/NĐ-CP (gated by ``FOUNDER_CONFIRMATION``)
* ``ecom.assess-platform-filing`` — MOIT e-commerce Notification vs Registration audit under Decree 52/2013 & 85/2021/NĐ-CP
* ``ecom.calculate-withholding-tax`` — Foreign Contractor Tax (FCT: VAT + CIT) under Circular 103/2014 & 80/2021/TT-BTC
* ``ip.assess-trademark`` — Trademark similarity search & filing under Art. 72–74 IP Law 2005 (amended 2022) & Nice 12-2024
* ``ip.register-copyright`` — Software copyright registration dossier under Decree 17/2023/NĐ-CP (COV)
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_wave4_ops.py"

PRIVACY_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="privacy.assess-dpia",
        command="privacy",
        subcommand="assess_dpia",
        title="Lập Hồ sơ Đánh giá tác động xử lý dữ liệu cá nhân (DPIA Mẫu 04-A05 Nghị định 13/2023/NĐ-CP)",
        description=(
            "Synthesize a Data Protection Impact Assessment (Form 04-A05 for Cục A05 - Bộ Công an) "
            "under Article 24 Decree 13/2023/NĐ-CP and persist to workspace privacy.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "activity_name": {"type": "string", "minLength": 3, "maxLength": 200},
                "processing_purpose": {"type": "string", "minLength": 5, "maxLength": 400},
                "data_categories": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "legal_basis": {
                    "type": "string",
                    "enum": ["CONSENT", "CONTRACT_PERFORMANCE", "LEGAL_OBLIGATION", "VITAL_INTEREST"],
                    "default": "CONSENT",
                },
                "security_measures": {
                    "type": "string",
                    "default": "AES-256 Encryption, Role-Based Access Control, TLS 1.3",
                },
            },
            "required": ["activity_name", "processing_purpose"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_digital_vn:privacy_assess_dpia",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/privacy.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "dpia_id",
                        "activity_name",
                        "processing_purpose",
                        "is_sensitive_data_processed",
                        "risk_level",
                        "filing_deadline_days",
                        "form_04_a05",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "activity_name", "result_path": "activity_name"}),
            Postcondition("enum_member", {"path": "risk_level", "allowed": ["LOW_RISK", "MEDIUM_RISK", "HIGH_RISK"]}),
            Postcondition("value_bounds", {"path": "filing_deadline_days", "min": 1, "max": 60}),
            Postcondition(
                "record_persisted",
                {"table": "dpia_assessments", "id_path": "dpia_id", "id_column": "dpia_id"},
            ),
        ),
        sop_steps=("classify-data-categories", "compute-pdpd-risk", "generate-form-04-a05", "persist-dpia"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Nghị định 13/2023/NĐ-CP Điều 24 (Hồ sơ Đánh giá tác động XLDLCN)",
        statutory_basis=("Nghị định 13/2023/NĐ-CP Điều 3, 24, 25",),
        output_contract={"evidence_type": "PDPD_DPIA_DOSSIER"},
        test_id=f"{TEST_MODULE}::test_wave4b_privacy_dpia_and_founder_gated_dsar",
    ),
    OperationSpec(
        op_id="privacy.process-dsar",
        command="privacy",
        subcommand="process_dsar",
        title="Xử lý yêu cầu chủ thể dữ liệu cá nhân (DSAR — Điều 9–16 Nghị định 13/2023/NĐ-CP)",
        description=(
            "Execute a Data Subject Request (RIGHT_TO_ACCESS, RIGHT_TO_DELETE, RIGHT_TO_WITHDRAW_CONSENT, "
            "RIGHT_TO_RESTRICT) with statutory SLA tracking in workspace privacy.db after FOUNDER_CONFIRMATION."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "request_type": {
                    "type": "string",
                    "enum": [
                        "RIGHT_TO_ACCESS",
                        "RIGHT_TO_DELETE",
                        "RIGHT_TO_WITHDRAW_CONSENT",
                        "RIGHT_TO_RESTRICT",
                        "RIGHT_TO_DATA_PORTABILITY",
                    ],
                    "default": "RIGHT_TO_DELETE",
                },
                "subject_id": {"type": "string", "minLength": 2, "maxLength": 160},
                "details": {
                    "type": "string",
                    "default": "Yêu cầu thực hiện quyền của chủ thể dữ liệu theo Điều 9 Nghị định 13/2023/NĐ-CP",
                },
            },
            "required": ["request_type", "subject_id"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_digital_vn:privacy_process_dsar",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/privacy.db",),
        external_effect="WORKSPACE_WRITE",
        approval_policy="FOUNDER_CONFIRMATION",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "request_id",
                        "subject_id",
                        "request_type",
                        "status",
                        "deadline_days",
                        "sla_hours",
                        "statutory_deadline",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "subject_id", "result_path": "subject_id"}),
            Postcondition("value_bounds", {"path": "deadline_days", "min": 1, "max": 30}),
            Postcondition("enum_member", {"path": "status", "allowed": ["PROCESSING", "COMPLETED", "NO_RECORDS_FOUND"]}),
            Postcondition(
                "record_persisted",
                {"table": "dsar_requests", "id_path": "request_id", "id_column": "request_id"},
            ),
        ),
        sop_steps=("founder-approval", "validate-dsar-type", "stamp-statutory-sla", "persist-dsar"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Nghị định 13/2023/NĐ-CP Điều 9–16 (SLA 72 giờ)",
        statutory_basis=("Nghị định 13/2023/NĐ-CP Điều 9, 13, 14, 15, 16",),
        output_contract={"evidence_type": "PDPD_DSAR_RECEIPT"},
        test_id=f"{TEST_MODULE}::test_wave4b_privacy_dpia_and_founder_gated_dsar",
    ),
)

ECOM_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="ecom.assess-platform-filing",
        command="ecom",
        subcommand="assess_platform_filing",
        title="Kiểm toán thủ tục Thông báo / Đăng ký Bộ Công Thương (Nghị định 52/2013 & 85/2021/NĐ-CP)",
        description=(
            "Audit e-commerce website or marketplace compliance, classify MOIT Notification vs "
            "Registration procedure, and persist filing assessment to workspace ecommerce.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "platform_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "domain_url": {"type": "string", "minLength": 4, "maxLength": 240},
                "platform_type": {
                    "type": "string",
                    "enum": ["SALES_WEBSITE", "MARKETPLACE", "SOCIAL_COMMERCE", "PROMOTION_APP"],
                    "default": "MARKETPLACE",
                },
                "enterprise_tax_id": {"type": "string", "minLength": 8, "default": "0109998881"},
                "has_operating_regulations": {"type": "boolean", "default": True},
                "has_dispute_mechanism": {"type": "boolean", "default": True},
                "has_seller_kyc": {"type": "boolean", "default": True},
                "has_data_retention_3yr": {"type": "boolean", "default": True},
                "has_tax_reporting_system": {"type": "boolean", "default": True},
            },
            "required": ["platform_name", "domain_url"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_digital_vn:ecom_assess_platform_filing",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/ecommerce.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "registration_id",
                        "platform_name",
                        "domain_url",
                        "statutory_procedure",
                        "compliance_score",
                        "compliance_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "platform_name", "result_path": "platform_name"}),
            Postcondition(
                "enum_member",
                {
                    "path": "statutory_procedure",
                    "allowed": ["REGISTRATION", "NOTIFICATION"],
                },
            ),
            Postcondition("value_bounds", {"path": "compliance_score", "min": 0, "max": 100}),
            Postcondition(
                "record_persisted",
                {
                    "table": "platform_registrations",
                    "id_path": "registration_id",
                    "id_column": "registration_id",
                },
            ),
        ),
        sop_steps=("classify-moit-procedure", "audit-mandatory-policies", "persist-platform-filing"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="VN",
        rule_version="Nghị định 52/2013/NĐ-CP & Nghị định 85/2021/NĐ-CP",
        statutory_basis=("Nghị định 52/2013/NĐ-CP Điều 27–35", "Nghị định 85/2021/NĐ-CP"),
        output_contract={"evidence_type": "MOIT_ECOMMERCE_COMPLIANCE"},
        test_id=f"{TEST_MODULE}::test_wave4b_ecom_platform_filing_and_fct_withholding_tax",
    ),
    OperationSpec(
        op_id="ecom.calculate-withholding-tax",
        command="ecom",
        subcommand="calculate_withholding_tax",
        title="Tính Thuế nhà thầu nước ngoài (FCT — GTGT + TNDN theo Thông tư 103/2014 & 80/2021/TT-BTC)",
        description=(
            "Calculate Foreign Contractor Tax (VAT + CIT withholding) for cross-border digital, "
            "SaaS, advertising, or brokerage payments and persist declaration to workspace ecommerce.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "foreign_supplier_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "service_category": {
                    "type": "string",
                    "enum": [
                        "DIGITAL_SERVICES",
                        "ONLINE_ADVERTISING",
                        "CLOUD_SAAS",
                        "STREAMING_MEDIA",
                        "ECOMMERCE_COMMISSION",
                    ],
                    "default": "CLOUD_SAAS",
                },
                "supplier_etax_code": {"type": "string", "default": ""},
                "revenue_usd": {"type": "number", "minimum": 0, "default": 0.0},
                "revenue_vnd": {"type": "number", "minimum": 0, "default": 0.0},
                "quarter": {"type": "string", "minLength": 4, "default": "Q4-2026"},
            },
            "required": ["foreign_supplier_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_digital_vn:ecom_calculate_withholding_tax",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/ecommerce.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "declaration_id",
                        "foreign_supplier_name",
                        "service_category",
                        "vat_amount_vnd",
                        "cit_amount_vnd",
                        "total_fct_liability_vnd",
                        "filing_status",
                    ]
                },
            ),
            Postcondition(
                "echoes_input",
                {"param_path": "foreign_supplier_name", "result_path": "foreign_supplier_name"},
            ),
            Postcondition("value_bounds", {"path": "total_fct_liability_vnd", "min": 0}),
            Postcondition(
                "record_persisted",
                {
                    "table": "fct_tax_declarations",
                    "id_path": "declaration_id",
                    "id_column": "declaration_id",
                },
            ),
        ),
        sop_steps=("resolve-fct-rates", "calculate-vat-and-cit", "persist-fct-declaration"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="VN",
        rule_version="Thông tư 103/2014/TT-BTC Điều 12, 13 & Thông tư 80/2021/TT-BTC",
        statutory_basis=("Thông tư 103/2014/TT-BTC", "Thông tư 80/2021/TT-BTC Mẫu 01/NTNN"),
        output_contract={"evidence_type": "FCT_WITHHOLDING_TAX_DECLARATION"},
        test_id=f"{TEST_MODULE}::test_wave4b_ecom_platform_filing_and_fct_withholding_tax",
    ),
)

IP_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="ip.assess-trademark",
        command="ip",
        subcommand="assess_trademark",
        title="Tra cứu khả năng phân biệt nhãn hiệu & lập hồ sơ đăng ký Cục SHTT (Luật SHTT 2022 & Nice 12-2024)",
        description=(
            "Perform orthographic and phonetic trademark conflict analysis under Art. 72–74 Law on IP "
            "and register a Nice Classification application in workspace ip.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "mark_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "nice_class": {
                    "type": "string",
                    "enum": ["09", "35", "36", "38", "41", "42", "45"],
                    "default": "09",
                },
                "applicant_name": {"type": "string", "minLength": 2, "default": "Công ty TNHH Mekong AI"},
                "goods_services_spec": {"type": "string", "default": ""},
            },
            "required": ["mark_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_digital_vn:ip_assess_trademark",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/ip.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "mark_id",
                        "mark_name",
                        "nice_class",
                        "official_fee_vnd",
                        "highest_similarity_score",
                        "overall_conflict_risk",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "mark_name", "result_path": "mark_name"}),
            Postcondition("enum_member", {"path": "overall_conflict_risk", "allowed": ["LOW", "MEDIUM", "HIGH"]}),
            Postcondition("value_bounds", {"path": "official_fee_vnd", "min": 100000}),
            Postcondition(
                "record_persisted",
                {"table": "trademarks", "id_path": "mark_id", "id_column": "mark_id"},
            ),
        ),
        sop_steps=("search-similarity", "classify-nice-12", "compute-noip-fees", "persist-trademark"),
        department_id="product-strategy",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="VN",
        rule_version="Luật Sở hữu trí tuệ 07/2022/QH15 Điều 72–74 & Thông tư 263/2016/TT-BTC",
        statutory_basis=("Luật Sở hữu trí tuệ 2005 (sửa đổi 2022)", "Nghị định 65/2023/NĐ-CP"),
        output_contract={"evidence_type": "TRADEMARK_APPLICATION_DOSSIER"},
        test_id=f"{TEST_MODULE}::test_wave4b_ip_trademark_and_software_copyright",
    ),
    OperationSpec(
        op_id="ip.register-copyright",
        command="ip",
        subcommand="register_copyright",
        title="Lập hồ sơ đăng ký Quyền tác giả phần mềm máy tính (Nghị định 17/2023/NĐ-CP Cục Bản quyền)",
        description=(
            "Compile a statutory software copyright registration dossier under Decree 17/2023/NĐ-CP "
            "and persist to workspace ip.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "software_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "author_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "version": {"type": "string", "minLength": 1, "default": "1.0.0"},
                "repository_url": {"type": "string", "default": ""},
                "lines_of_code": {"type": "integer", "minimum": 1, "default": 10000},
            },
            "required": ["software_name", "author_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_digital_vn:ip_register_copyright",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/ip.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "copyright_id",
                        "software_name",
                        "author_name",
                        "version",
                        "official_fee_vnd",
                        "dossier_items_count",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "software_name", "result_path": "software_name"}),
            Postcondition("value_bounds", {"path": "dossier_items_count", "min": 5}),
            Postcondition("enum_member", {"path": "status", "allowed": ["DOSSIER_COMPILED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "software_copyrights",
                    "id_path": "copyright_id",
                    "id_column": "copyright_id",
                },
            ),
        ),
        sop_steps=("prepare-form-01-cov", "package-source-extracts", "persist-copyright"),
        department_id="product-strategy",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="VN",
        rule_version="Nghị định 17/2023/NĐ-CP & Thông tư 263/2016/TT-BTC",
        statutory_basis=("Luật Sở hữu trí tuệ 2005 (sửa đổi 2022)", "Nghị định 17/2023/NĐ-CP"),
        output_contract={"evidence_type": "SOFTWARE_COPYRIGHT_DOSSIER"},
        test_id=f"{TEST_MODULE}::test_wave4b_ip_trademark_and_software_copyright",
    ),
)

LEGAL_DIGITAL_VN_OPERATIONS: tuple[OperationSpec, ...] = (
    *PRIVACY_OPS,
    *ECOM_OPS,
    *IP_OPS,
)

__all__ = [
    "ECOM_OPS",
    "IP_OPS",
    "LEGAL_DIGITAL_VN_OPERATIONS",
    "PRIVACY_OPS",
]
