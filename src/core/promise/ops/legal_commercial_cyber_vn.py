# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Wave 5B Vietnamese Commercial, Financial & Cyber Statutory OperationSpecs.

Covers 6 Vietnamese statutory commands across 12 executable operations:
- ``etransaction`` (2 ops — Law on Electronic Transactions 20/2023/QH15 & Decree 130/2018/NĐ-CP)
- ``cyber``        (2 ops — Cybersecurity Law 24/2018/QH14, Decree 85/2016/NĐ-CP & Decree 53/2022/NĐ-CP)
- ``fdi``          (2 ops — Investment Law 61/2020/QH14, Decree 31/2021/NĐ-CP & Circular 12/2022/TT-NHNN)
- ``customs``      (2 ops — Customs Law 54/2014/QH13, VNACCS/VCIS & ATIGA/EVFTA Rules of Origin)
- ``banking``      (2 ops — Law on Credit Institutions 32/2024/QH15, Circular 41/2016 & 31/2024/TT-NHNN)
- ``aml``          (2 ops — Law on Anti-Money Laundering 14/2022/QH15, Decree 19/2023/NĐ-CP & QĐ 11/2023/QĐ-TTg)
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_wave5_ops.py"

ETRANSACTION_CYBER_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="etransaction.create-contract",
        command="etransaction",
        subcommand="create_contract",
        title="Khởi tạo hợp đồng giao dịch điện tử có băm SHA-256 (Electronic Contract Law 20/2023/QH15)",
        description=(
            "Create a statutory electronic contract with SHA-256 integrity hash and party "
            "tax codes under Law on Electronic Transactions 20/2023/QH15 in workspace etransaction.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "contract_number": {"type": "string", "minLength": 3, "maxLength": 120},
                "title": {"type": "string", "minLength": 3, "maxLength": 240},
                "provider_name": {"type": "string", "default": "Công ty TNHH Mekong AI"},
                "provider_tax_id": {"type": "string", "default": "0101234567"},
                "client_name": {"type": "string", "default": "Công ty CP Bán Lẻ Số"},
                "client_tax_id": {"type": "string", "default": "0107654321"},
                "contract_value": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 1_000_000_000_000,
                    "default": 120_000_000.0,
                },
            },
            "required": ["contract_number", "title"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:etransaction_create_contract",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/etransaction.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "contract_id",
                        "contract_number",
                        "title",
                        "content_hash",
                        "contract_value",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "contract_number", "result_path": "contract_number"}),
            Postcondition("value_bounds", {"path": "contract_value", "min": 1}),
            Postcondition(
                "record_persisted",
                {
                    "table": "electronic_contracts",
                    "id_path": "contract_id",
                    "id_column": "contract_id",
                },
            ),
        ),
        sop_steps=("validate-party-tax-codes", "compute-sha256-data-message", "persist-electronic-contract"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Luật Giao dịch điện tử 20/2023/QH15 (Điều 8–12 & Điều 34)",
        output_contract={"evidence_type": "VN_ETRANSACTION_CONTRACT"},
        test_id=f"{TEST_MODULE}::test_etransaction_create_and_ceca_certify_contract",
    ),
    OperationSpec(
        op_id="etransaction.certify-ceca",
        command="etransaction",
        subcommand="certify_ceca",
        title="Ký số chuyên dùng & chứng thực hợp đồng điện tử CeCA Bộ Công Thương (MOIT CeCA Certification)",
        description=(
            "Execute qualified CA digital signatures for both parties and issue an MOIT CeCA "
            "trust token under Decree 130/2018/NĐ-CP & Law 20/2023/QH15 in workspace etransaction.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "contract_number": {"type": "string", "minLength": 3, "maxLength": 120},
                "title": {"type": "string", "minLength": 3, "maxLength": 240},
                "provider_name": {"type": "string", "default": "Công ty TNHH Mekong AI"},
                "client_name": {"type": "string", "default": "Công ty CP Bán Lẻ Số"},
                "ceca_authority": {"type": "string", "default": "CeCA-Vietnam-Post"},
                "license_number": {"type": "string", "default": "BCT-CeCA-008/GP"},
                "contract_value": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 1_000_000_000_000,
                    "default": 150_000_000.0,
                },
            },
            "required": ["contract_number", "title"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:etransaction_certify_ceca",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/etransaction.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "contract_id",
                        "contract_number",
                        "ceca_verified",
                        "ceca_token_id",
                        "authority_name",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "contract_number", "result_path": "contract_number"}),
            Postcondition("enum_member", {"path": "status", "allowed": ["CECA_CERTIFIED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "trust_tokens",
                    "id_path": "ceca_token_id",
                    "id_column": "token_id",
                },
            ),
        ),
        sop_steps=("sign-qualified-ca-certificates", "issue-ceca-trust-token", "seal-certified-contract"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Nghị định 130/2018/NĐ-CP & Luật 20/2023/QH15 (Trục CeCA Bộ Công Thương)",
        output_contract={"evidence_type": "VN_CECA_TRUST_TOKEN"},
        test_id=f"{TEST_MODULE}::test_etransaction_create_and_ceca_certify_contract",
    ),
    OperationSpec(
        op_id="cyber.assess-system-level",
        command="cyber",
        subcommand="assess_system_level",
        title="Thẩm định cấp độ an toàn hệ thống thông tin Cấp độ 1–5 (Decree 85/2016/NĐ-CP & Circular 12/2022/TT-BTTTT)",
        description=(
            "Assess information system security level (Cấp độ 1–5) and approving authority "
            "under Decree 85/2016/NĐ-CP in workspace cyber.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "system_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "organization": {"type": "string", "minLength": 2, "maxLength": 200},
                "data_classification": {
                    "type": "string",
                    "enum": ["PUBLIC", "INTERNAL", "CONFIDENTIAL_MAT", "SECRET_TOI_MAT", "TOP_SECRET_TUYET_MAT"],
                    "default": "CONFIDENTIAL_MAT",
                },
                "service_scale": {
                    "type": "string",
                    "enum": ["INTERNAL_ONLY", "PROVINCIAL", "NATIONAL", "CRITICAL_INFRASTRUCTURE"],
                    "default": "NATIONAL",
                },
            },
            "required": ["system_name", "organization"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:cyber_assess_system_level",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/cyber.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "assessment_id",
                        "system_name",
                        "organization",
                        "recommended_level",
                        "audit_frequency_months",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "system_name", "result_path": "system_name"}),
            Postcondition("value_bounds", {"path": "recommended_level", "min": 1, "max": 5}),
            Postcondition(
                "record_persisted",
                {
                    "table": "security_level_assessments",
                    "id_path": "assessment_id",
                    "id_column": "assessment_id",
                },
            ),
        ),
        sop_steps=("classify-data-and-scale", "determine-cap-do-1-to-5", "persist-security-assessment"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Nghị định 85/2016/NĐ-CP & Thông tư 12/2022/TT-BTTTT (Cấp độ ATTT 1–5)",
        output_contract={"evidence_type": "VN_CYBER_LEVEL_ASSESSMENT"},
        test_id=f"{TEST_MODULE}::test_cyber_assess_system_level_and_audit_data_localization",
    ),
    OperationSpec(
        op_id="cyber.audit-data-localization",
        command="cyber",
        subcommand="audit_data_localization",
        title="Kiểm toán lưu trữ dữ liệu tại Việt Nam tối thiểu 24 tháng (Art. 26 Cybersecurity Law & Decree 53/2022/NĐ-CP)",
        description=(
            "Audit data localization and >= 24-month retention compliance under Article 26 "
            "Cybersecurity Law 24/2018/QH14 and Article 26–27 Decree 53/2022/NĐ-CP in workspace cyber.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "service_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "provider_type": {
                    "type": "string",
                    "enum": ["DOMESTIC_ENTERPRISE", "FOREIGN_CROSS_BORDER"],
                    "default": "DOMESTIC_ENTERPRISE",
                },
                "local_storage_active": {"type": "boolean", "default": True},
                "retention_months": {"type": "integer", "minimum": 1, "maximum": 240, "default": 24},
                "has_local_branch": {"type": "boolean", "default": True},
            },
            "required": ["service_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:cyber_audit_data_localization",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/cyber.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "audit_id",
                        "service_name",
                        "provider_type",
                        "retention_months",
                        "is_compliant",
                        "compliance_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "service_name", "result_path": "service_name"}),
            Postcondition("value_bounds", {"path": "retention_months", "min": 24}),
            Postcondition("enum_member", {"path": "compliance_status", "allowed": ["COMPLIANT"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "data_localization_audits",
                    "id_path": "audit_id",
                    "id_column": "audit_id",
                },
            ),
        ),
        sop_steps=("verify-data-categories", "check-24-month-vietnam-retention", "persist-localization-audit"),
        department_id="platform-operations",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Luật An ninh mạng 24/2018/QH14 (Điều 26) & Nghị định 53/2022/NĐ-CP (Điều 26–27)",
        output_contract={"evidence_type": "VN_DATA_LOCALIZATION_AUDIT"},
        test_id=f"{TEST_MODULE}::test_cyber_assess_system_level_and_audit_data_localization",
    ),
)

FDI_CUSTOMS_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="fdi.generate-irc-dossier",
        command="fdi",
        subcommand="generate_irc_dossier",
        title="Lập hồ sơ Giấy chứng nhận đăng ký đầu tư IRC & ưu đãi CIT (Investment Law 61/2020/QH14 & Decree 31/2021/NĐ-CP)",
        description=(
            "Generate an Investment Registration Certificate (IRC) dossier with market-access "
            "and CIT incentive screening under Investment Law 61/2020/QH14 in workspace fdi.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "minLength": 3, "maxLength": 240},
                "capital_usd": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 10_000_000_000,
                    "default": 500_000.0,
                },
                "investor_country": {"type": "string", "default": "SG"},
                "sector_code": {"type": "string", "default": "IT_SOFTWARE"},
                "location": {"type": "string", "default": "Khu Công Nghệ Cao Hòa Lạc, Hà Nội"},
            },
            "required": ["project_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:fdi_generate_irc_dossier",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/fdi.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "project_id",
                        "project_name",
                        "investor_country",
                        "sector_code",
                        "capital_usd",
                        "required_documents_count",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "project_name", "result_path": "project_name"}),
            Postcondition("value_bounds", {"path": "required_documents_count", "min": 5}),
            Postcondition(
                "record_persisted",
                {
                    "table": "fdi_projects",
                    "id_path": "project_id",
                    "id_column": "project_id",
                },
            ),
        ),
        sop_steps=("screen-market-access-list", "compute-cit-incentives", "persist-irc-dossier"),
        department_id="product-strategy",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="VN",
        rule_version="Luật Đầu tư 61/2020/QH14 (Điều 37–38) & Nghị định 31/2021/NĐ-CP",
        output_contract={"evidence_type": "VN_FDI_IRC_DOSSIER"},
        test_id=f"{TEST_MODULE}::test_fdi_generate_irc_dossier_and_evaluate_foreign_loan",
    ),
    OperationSpec(
        op_id="fdi.evaluate-foreign-loan",
        command="fdi",
        subcommand="evaluate_foreign_loan",
        title="Thẩm định khoản vay nước ngoài & nghĩa vụ đăng ký NHNN (Circular 12/2022/TT-NHNN & Circular 06/2019/TT-NHNN)",
        description=(
            "Evaluate offshore loan tenor (> 12 months requires SBV registration) and DICA "
            "settlement compliance under Circular 12/2022/TT-NHNN in workspace fdi.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "borrower_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "lender_name": {"type": "string", "default": "DBS Bank Ltd"},
                "lender_country": {"type": "string", "default": "SG"},
                "amount_usd": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "maximum": 1_000_000_000,
                    "default": 1_000_000.0,
                },
                "tenor_months": {"type": "integer", "minimum": 1, "maximum": 360, "default": 24},
                "interest_rate_pct": {"type": "number", "minimum": 0, "maximum": 15, "default": 5.8},
            },
            "required": ["borrower_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:fdi_evaluate_foreign_loan",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/fdi.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "loan_id",
                        "borrower_name",
                        "lender_name",
                        "amount_usd",
                        "tenor_months",
                        "sbv_registration_required",
                        "is_compliant",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "borrower_name", "result_path": "borrower_name"}),
            Postcondition("value_bounds", {"path": "amount_usd", "min": 1}),
            Postcondition(
                "record_persisted",
                {
                    "table": "foreign_loans",
                    "id_path": "loan_id",
                    "id_column": "loan_id",
                },
            ),
        ),
        sop_steps=("classify-loan-tenor", "assess-sbv-registration-duty", "persist-foreign-loan-evaluation"),
        department_id="product-strategy",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="VN",
        rule_version="Thông tư 12/2022/TT-NHNN & Thông tư 06/2019/TT-NHNN (Quản lý vay trả nợ nước ngoài & DICA)",
        output_contract={"evidence_type": "VN_FDI_FOREIGN_LOAN_EVALUATION"},
        test_id=f"{TEST_MODULE}::test_fdi_generate_irc_dossier_and_evaluate_foreign_loan",
    ),
    OperationSpec(
        op_id="customs.create-declaration",
        command="customs",
        subcommand="create_declaration",
        title="Khai báo tờ khai hải quan VNACCS/VCIS & phân luồng Xanh/Vàng/Đỏ (Customs Law 54/2014/QH13)",
        description=(
            "Create an import/export customs declaration with HS code tariff calculation and "
            "Green/Yellow/Red channeling under Customs Law 54/2014/QH13 in workspace customs.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "enterprise_tax_id": {"type": "string", "minLength": 10, "maxLength": 14},
                "commodity_name": {"type": "string", "minLength": 2, "maxLength": 240},
                "invoice_value_usd": {"type": "number", "exclusiveMinimum": 0, "maximum": 100_000_000},
                "hs_code": {"type": "string", "default": "8471.30.20"},
                "origin_country": {"type": "string", "default": "SG"},
                "declaration_type": {
                    "type": "string",
                    "enum": ["IMPORT_BUSINESS", "EXPORT_BUSINESS", "EPE_PROCESSING"],
                    "default": "IMPORT_BUSINESS",
                },
            },
            "required": ["enterprise_tax_id", "commodity_name", "invoice_value_usd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:customs_create_declaration",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/customs.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "declaration_id",
                        "enterprise_tax_id",
                        "commodity_name",
                        "hs_code",
                        "channel",
                        "total_tax_vnd",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "enterprise_tax_id", "result_path": "enterprise_tax_id"}),
            Postcondition("enum_member", {"path": "channel", "allowed": ["GREEN", "YELLOW", "RED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "customs_declarations",
                    "id_path": "declaration_id",
                    "id_column": "declaration_id",
                },
            ),
        ),
        sop_steps=("lookup-hs-tariff-schedule", "assign-vnaccs-channel", "persist-customs-declaration"),
        department_id="quality-compliance",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Luật Hải quan 54/2014/QH13 & Nghị định 08/2015/NĐ-CP (VNACCS/VCIS)",
        output_contract={"evidence_type": "VN_CUSTOMS_DECLARATION"},
        test_id=f"{TEST_MODULE}::test_customs_create_declaration_and_verify_origin_co",
    ),
    OperationSpec(
        op_id="customs.verify-origin-co",
        command="customs",
        subcommand="verify_origin_co",
        title="Thẩm định xuất xứ hàng hóa C/O Form D/EUR.1 theo tỷ lệ RVC >= 40% (Decree 31/2018/NĐ-CP)",
        description=(
            "Calculate Regional Value Content (RVC) and issue Certificate of Origin (C/O) "
            "eligibility under Decree 31/2018/NĐ-CP in workspace customs.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "exporter_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "fob_value_usd": {"type": "number", "exclusiveMinimum": 0, "maximum": 100_000_000},
                "non_originating_value_usd": {"type": "number", "minimum": 0, "maximum": 100_000_000},
                "form_type": {
                    "type": "string",
                    "enum": ["FORM_D", "FORM_E", "FORM_AK", "FORM_CPTPP", "EUR_1"],
                    "default": "FORM_D",
                },
                "hs_code": {"type": "string", "default": "8471.30.20"},
                "importer_country": {"type": "string", "default": "SG"},
            },
            "required": ["exporter_name", "fob_value_usd", "non_originating_value_usd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:customs_verify_origin_co",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/customs.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "co_id",
                        "exporter_name",
                        "form_type",
                        "rvc_pct",
                        "is_eligible",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "exporter_name", "result_path": "exporter_name"}),
            Postcondition("value_bounds", {"path": "rvc_pct", "min": 40.0, "max": 100.0}),
            Postcondition(
                "enum_member",
                {"path": "status", "allowed": ["ISSUED", "QUALIFIED_FOR_PREFERENTIAL_TARIFF"]},
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "co_certificates",
                    "id_path": "co_id",
                    "id_column": "co_id",
                },
            ),
        ),
        sop_steps=("calculate-rvc-percentage", "verify-fta-threshold", "persist-co-certificate"),
        department_id="quality-compliance",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Nghị định 31/2018/NĐ-CP & Hiệp định ATIGA/EVFTA/CPTPP (RVC >= 40%)",
        output_contract={"evidence_type": "VN_CUSTOMS_CO_CERTIFICATE"},
        test_id=f"{TEST_MODULE}::test_customs_create_declaration_and_verify_origin_co",
    ),
)

BANKING_AML_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="banking.audit-capital-adequacy",
        command="banking",
        subcommand="audit_capital_adequacy",
        title="Kiểm toán hệ số an toàn vốn tối thiểu CAR >= 8% theo Basel II (Circular 41/2016/TT-NHNN)",
        description=(
            "Audit Tier 1 + Tier 2 Capital Adequacy Ratio (CAR >= 8%) against Credit, Market "
            "and Operational RWA under Circular 41/2016/TT-NHNN in workspace banking.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "institution_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "tier1_capital_vnd": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "default": 15_000_000_000_000.0,
                },
                "tier2_capital_vnd": {"type": "number", "minimum": 0, "default": 3_000_000_000_000.0},
                "credit_rwa_vnd": {"type": "number", "exclusiveMinimum": 0, "default": 100_000_000_000_000.0},
                "market_rwa_vnd": {"type": "number", "minimum": 0, "default": 10_000_000_000_000.0},
                "operational_rwa_vnd": {"type": "number", "minimum": 0, "default": 10_000_000_000_000.0},
                "reporting_quarter": {"type": "string", "default": "Q4/2026"},
            },
            "required": ["institution_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:banking_audit_capital_adequacy",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/banking.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "audit_id",
                        "institution_name",
                        "car_ratio_pct",
                        "car_status",
                        "is_compliant",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "institution_name", "result_path": "institution_name"}),
            Postcondition("value_bounds", {"path": "car_ratio_pct", "min": 8.0}),
            Postcondition(
                "enum_member",
                {"path": "car_status", "allowed": ["COMPLIANT", "STRONG", "ADEQUATE"]},
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "car_audits",
                    "id_path": "audit_id",
                    "id_column": "audit_id",
                },
            ),
        ),
        sop_steps=("cap-tier2-at-tier1", "compute-total-rwa-and-car", "persist-car-audit"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="VN",
        rule_version="Luật Các tổ chức tín dụng 32/2024/QH15 (Điều 138) & Thông tư 41/2016/TT-NHNN",
        output_contract={"evidence_type": "VN_BANKING_CAR_AUDIT"},
        test_id=f"{TEST_MODULE}::test_banking_audit_car_and_classify_credit_debt",
    ),
    OperationSpec(
        op_id="banking.classify-credit-debt",
        command="banking",
        subcommand="classify_credit_debt",
        title="Phân loại nợ Nhóm 1–5 & trích lập dự phòng rủi ro tín dụng (Circular 31/2024/TT-NHNN & Decree 86/2024/NĐ-CP)",
        description=(
            "Classify credit debt into Groups 1–5 by overdue days and compute specific + general "
            "(0.75%) risk provisions under Circular 31/2024/TT-NHNN in workspace banking.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "contract_number": {"type": "string", "minLength": 2, "maxLength": 120},
                "borrower_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "outstanding_balance_vnd": {"type": "number", "exclusiveMinimum": 0},
                "overdue_days": {"type": "integer", "minimum": 0, "maximum": 3650, "default": 15},
                "deductible_collateral_vnd": {"type": "number", "minimum": 0, "default": 0.0},
            },
            "required": ["contract_number", "borrower_name", "outstanding_balance_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:banking_classify_credit_debt",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/banking.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "record_id",
                        "contract_number",
                        "borrower_name",
                        "debt_group",
                        "total_provision_vnd",
                        "is_npl",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "contract_number", "result_path": "contract_number"}),
            Postcondition("value_bounds", {"path": "debt_group", "min": 1, "max": 5}),
            Postcondition(
                "record_persisted",
                {
                    "table": "debt_classifications",
                    "id_path": "record_id",
                    "id_column": "record_id",
                },
            ),
        ),
        sop_steps=("map-overdue-days-to-nhom-1-5", "calculate-specific-and-general-provision", "persist-debt-record"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="VN",
        rule_version="Thông tư 31/2024/TT-NHNN & Nghị định 86/2024/NĐ-CP (Phân loại nợ Nhóm 1–5)",
        output_contract={"evidence_type": "VN_BANKING_DEBT_CLASSIFICATION"},
        test_id=f"{TEST_MODULE}::test_banking_audit_car_and_classify_credit_debt",
    ),
    OperationSpec(
        op_id="aml.perform-cdd",
        command="aml",
        subcommand="perform_cdd",
        title="Nhận biết khách hàng CDD/EDD & chấm điểm rủi ro rửa tiền (AML Law 14/2022/QH15 & Decree 19/2023/NĐ-CP)",
        description=(
            "Perform Customer Due Diligence (CDD/EDD), PEP screening, and risk scoring under "
            "Law on Anti-Money Laundering 14/2022/QH15 in workspace aml.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "identifier": {"type": "string", "minLength": 5, "maxLength": 64},
                "customer_type": {"type": "string", "enum": ["INDIVIDUAL", "CORPORATE"], "default": "INDIVIDUAL"},
                "industry": {"type": "string", "default": "FINTECH"},
                "nationality": {"type": "string", "default": "VN"},
                "is_pep": {"type": "boolean", "default": False},
                "senior_mgmt_approved": {"type": "boolean", "default": False},
            },
            "required": ["customer_name", "identifier"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:aml_perform_cdd",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/aml.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "profile_id",
                        "customer_name",
                        "identifier",
                        "risk_level",
                        "risk_score",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "customer_name", "result_path": "customer_name"}),
            Postcondition("enum_member", {"path": "risk_level", "allowed": ["LOW", "MEDIUM", "HIGH"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "aml_cdd_profiles",
                    "id_path": "profile_id",
                    "id_column": "profile_id",
                },
            ),
        ),
        sop_steps=("verify-identity-document", "compute-aml-risk-score", "persist-cdd-profile"),
        department_id="quality-compliance",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Luật Phòng, chống rửa tiền 14/2022/QH15 (Điều 9–19) & Nghị định 19/2023/NĐ-CP",
        output_contract={"evidence_type": "VN_AML_CDD_PROFILE"},
        test_id=f"{TEST_MODULE}::test_aml_perform_cdd_and_founder_confirmed_str_filing",
    ),
    OperationSpec(
        op_id="aml.file-str-report",
        command="aml",
        subcommand="file_str_report",
        title="Lập báo cáo giao dịch đáng ngờ STR gửi Cục Phòng chống rửa tiền NHNN (Art. 26 AML Law 14/2022/QH15)",
        description=(
            "File a Suspicious Transaction Report (STR) to PCRT (State Bank of Vietnam) under "
            "Article 26–37 AML Law 14/2022/QH15 after founder confirmation in workspace aml.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "customer_name": {"type": "string", "minLength": 2, "maxLength": 200},
                "suspicion_type": {
                    "type": "string",
                    "enum": ["STRUCTURING", "SHELL_COMPANY", "SANCTION_NEXUS", "UNUSUAL_VOLUME"],
                    "default": "STRUCTURING",
                },
                "amount": {"type": "number", "exclusiveMinimum": 0, "default": 650_000_000.0},
                "rationale": {
                    "type": "string",
                    "default": "Chia nhỏ giao dịch tiền mặt vượt ngưỡng 400 triệu VNĐ theo QĐ 11/2023/QĐ-TTg",
                },
                "urgency": {"type": "string", "enum": ["NORMAL", "HIGH", "IMMEDIATE"], "default": "HIGH"},
            },
            "required": ["customer_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_legal_commercial_cyber_vn:aml_file_str_report",
        ),
        approval_policy="FOUNDER_CONFIRMATION",
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/aml.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "str_id",
                        "customer_name",
                        "suspicion_type",
                        "amount",
                        "urgency",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "customer_name", "result_path": "customer_name"}),
            Postcondition("value_bounds", {"path": "amount", "min": 1}),
            Postcondition(
                "record_persisted",
                {
                    "table": "aml_str_reports",
                    "id_path": "str_id",
                    "id_column": "str_id",
                },
            ),
        ),
        sop_steps=("verify-founder-authority", "compile-str-indicators", "submit-str-to-pcrt"),
        department_id="quality-compliance",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="VN",
        rule_version="Luật Phòng, chống rửa tiền 14/2022/QH15 (Điều 26–37) & QĐ 11/2023/QĐ-TTg",
        output_contract={"evidence_type": "VN_AML_STR_FILING"},
        test_id=f"{TEST_MODULE}::test_aml_perform_cdd_and_founder_confirmed_str_filing",
    ),
)

LEGAL_COMMERCIAL_CYBER_VN_OPERATIONS: tuple[OperationSpec, ...] = (
    ETRANSACTION_CYBER_OPS + FDI_CUSTOMS_OPS + BANKING_AML_OPS
)

__all__ = [
    "BANKING_AML_OPS",
    "ETRANSACTION_CYBER_OPS",
    "FDI_CUSTOMS_OPS",
    "LEGAL_COMMERCIAL_CYBER_VN_OPERATIONS",
]
