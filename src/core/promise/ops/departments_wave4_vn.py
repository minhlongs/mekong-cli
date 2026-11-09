# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts for Department & C-Suite Operations across all 10 Departments.

Completes 10/10 department executable coverage across:
* ``engineering-factory`` (L2 / ``mvp-live``): ``build``, ``code``
* ``customer-success`` (L4 / ``fulfillment-stable``): ``support``, ``collab``
* ``knowledge-memory`` (L5 / ``scale-ready``): ``memory``, ``recall``
* ``market-intelligence`` (L1 / ``offer-validated``): ``benchmark``, ``eval-agent``
* ``ceo-command`` (L0 / ``company-blueprint``): ``company``, ``cfo``
* ``growth-marketing`` (L3 / ``repeatable-channel``): ``cmo``
* ``sales-revenue`` (L3 / ``first-revenue``): ``cso``
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_wave4_ops.py"

ENGINEERING_FACTORY_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="build.verify-artifact",
        command="build",
        subcommand="verify_artifact",
        title="Kiểm định chất lượng & tính toàn vẹn gói Build (L2 Engineering Factory)",
        description=(
            "Audit codebase AST quality and verify build artifact readiness via DevEngine, "
            "persisting verification record to workspace engineering.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "artifact_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "target_path": {"type": "string", "default": "src/core/promise"},
                "max_files": {"type": "integer", "minimum": 1, "maximum": 500, "default": 50},
            },
            "required": ["artifact_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:build_verify_artifact",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/engineering.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "verification_id",
                        "artifact_name",
                        "files_scanned",
                        "quality_grade",
                        "health_score",
                        "build_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "artifact_name", "result_path": "artifact_name"}),
            Postcondition("value_bounds", {"path": "health_score", "min": 0, "max": 100}),
            Postcondition("enum_member", {"path": "build_status", "allowed": ["VERIFIED", "WARNING"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "build_verifications",
                    "id_path": "verification_id",
                    "id_column": "verification_id",
                },
            ),
        ),
        sop_steps=("scan-ast-integrity", "compute-build-health", "persist-build-verification"),
        department_id="engineering-factory",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong Engineering Factory L2 Build Verification v1",
        output_contract={"evidence_type": "BUILD_VERIFICATION_RECORD"},
        test_id=f"{TEST_MODULE}::test_wave4a_engineering_factory_build_and_code_ops",
    ),
    OperationSpec(
        op_id="build.record-release",
        command="build",
        subcommand="record_release",
        title="Ghi nhận bằng chứng phát hành bản dựng MVP (Deployment Proof L2)",
        description=(
            "Record a cryptographic build release deployment proof in workspace promise.db "
            "to satisfy L2 mvp-live gate verification."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "environment": {
                    "type": "string",
                    "enum": ["staging", "production", "canary"],
                    "default": "production",
                },
                "artifact_digest": {"type": "string", "minLength": 6, "maxLength": 128},
                "health_url": {"type": "string", "default": "https://app.mekongcli.vn/healthz"},
                "http_status": {"type": "integer", "minimum": 100, "maximum": 599, "default": 200},
                "verified_by": {"type": "string", "default": "Release Pipeline"},
            },
            "required": ["environment", "artifact_digest"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:build_record_release",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/engineering.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "proof_id",
                        "environment",
                        "artifact_digest",
                        "http_status",
                        "health_status",
                        "release_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "environment", "result_path": "environment"}),
            Postcondition("value_bounds", {"path": "http_status", "min": 200, "max": 399}),
            Postcondition("enum_member", {"path": "release_status", "allowed": ["RELEASED"]}),
            Postcondition(
                "record_persisted",
                {"table": "deployment_proofs", "id_path": "proof_id", "id_column": "proof_id"},
            ),
        ),
        sop_steps=("verify-release-digest", "probe-health-status", "persist-deployment-proof"),
        department_id="engineering-factory",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong L2 MVP-Live Release Proof Contract v1",
        output_contract={"evidence_type": "DEPLOYMENT_RELEASE_PROOF"},
        test_id=f"{TEST_MODULE}::test_wave4a_engineering_factory_build_and_code_ops",
    ),
    OperationSpec(
        op_id="code.audit-module",
        command="code",
        subcommand="audit_module",
        title="Kiểm toán chất lượng mã nguồn & độ phức tạp AST (DevEngine Code Audit)",
        description=(
            "Run static AST complexity, docstring, and LOC ceiling audit via DevEngine "
            "and persist audit report to workspace engineering.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "module_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "target_path": {"type": "string", "default": "src/core/promise"},
                "max_files": {"type": "integer", "minimum": 1, "maximum": 500, "default": 40},
            },
            "required": ["module_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:code_audit_module",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/engineering.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "audit_id",
                        "module_name",
                        "files_scanned",
                        "quality_grade",
                        "health_score",
                        "audit_verdict",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "module_name", "result_path": "module_name"}),
            Postcondition("value_bounds", {"path": "health_score", "min": 0, "max": 100}),
            Postcondition("enum_member", {"path": "audit_verdict", "allowed": ["PASS", "NEEDS_REFACTOR"]}),
            Postcondition(
                "record_persisted",
                {"table": "code_audits", "id_path": "audit_id", "id_column": "audit_id"},
            ),
        ),
        sop_steps=("parse-python-ast", "score-code-health", "persist-code-audit"),
        department_id="engineering-factory",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong DevEngine AST Code Quality Standard v1",
        output_contract={"evidence_type": "CODE_QUALITY_AUDIT"},
        test_id=f"{TEST_MODULE}::test_wave4a_engineering_factory_build_and_code_ops",
    ),
    OperationSpec(
        op_id="code.scaffold-component",
        command="code",
        subcommand="scaffold_component",
        title="Khởi tạo khung thành phần chuẩn kèm Unit Test (DevEngine Scaffold)",
        description=(
            "Scaffold a standardized Python service/engine component and unit test inside "
            "the isolated workspace and record in workspace engineering.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "component_name": {"type": "string", "minLength": 2, "maxLength": 80},
                "module_type": {
                    "type": "string",
                    "enum": ["service", "engine", "cli_command", "agent_skill"],
                    "default": "service",
                },
                "with_test": {"type": "boolean", "default": True},
            },
            "required": ["component_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:code_scaffold_component",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/engineering.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "scaffold_id",
                        "component_name",
                        "module_type",
                        "files_created_count",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "component_name", "result_path": "component_name"}),
            Postcondition("value_bounds", {"path": "files_created_count", "min": 1, "max": 10}),
            Postcondition("enum_member", {"path": "status", "allowed": ["SCAFFOLDED"]}),
            Postcondition(
                "record_persisted",
                {"table": "code_scaffolds", "id_path": "scaffold_id", "id_column": "scaffold_id"},
            ),
        ),
        sop_steps=("validate-component-name", "render-scaffold-files", "persist-scaffold-record"),
        department_id="engineering-factory",
        layer_id="L2",
        gate_id="mvp-live",
        jurisdiction="GLOBAL",
        rule_version="Mekong DevEngine Component Scaffold Standard v1",
        output_contract={"evidence_type": "COMPONENT_SCAFFOLD_RECEIPT"},
        test_id=f"{TEST_MODULE}::test_wave4a_engineering_factory_build_and_code_ops",
    ),
)

CUSTOMER_SUCCESS_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="support.submit-bug",
        command="support",
        subcommand="submit_bug",
        title="Tiếp nhận & phân loại sự cố khách hàng tự động (SupportEngine Bug Triage)",
        description=(
            "Submit a customer bug report and run deterministic urgency/channel triage "
            "in workspace support.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 200},
                "severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "default": "high",
                },
                "description": {
                    "type": "string",
                    "default": "Customer reported production issue requiring triage",
                },
                "steps": {"type": "string", "default": "1. Run operation 2. Observe output"},
            },
            "required": ["title"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:support_submit_bug",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/support.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "bug_id",
                        "title",
                        "severity",
                        "status",
                        "triage_category",
                        "triage_urgency",
                        "recommended_action",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "title", "result_path": "title"}),
            Postcondition("enum_member", {"path": "severity", "allowed": ["low", "medium", "high", "critical"]}),
            Postcondition(
                "record_persisted",
                {"table": "bug_reports", "id_path": "bug_id", "id_column": "id"},
            ),
        ),
        sop_steps=("log-bug-ticket", "classify-triage-urgency", "persist-support-bug"),
        department_id="customer-success",
        layer_id="L4",
        gate_id="fulfillment-stable",
        jurisdiction="GLOBAL",
        rule_version="Mekong Customer Success Bug Triage SOP v1",
        output_contract={"evidence_type": "SUPPORT_BUG_TICKET"},
        test_id=f"{TEST_MODULE}::test_wave4a_customer_success_support_and_collab_ops",
    ),
    OperationSpec(
        op_id="support.submit-feedback",
        command="support",
        subcommand="submit_feedback",
        title="Ghi nhận điểm hài lòng khách hàng NPS & tổng hợp CSAT (SupportEngine NPS)",
        description=(
            "Record customer NPS rating and feedback in workspace support.db and compute "
            "updated Net Promoter Score summary."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "nps_score": {"type": "integer", "minimum": 0, "maximum": 10, "default": 9},
                "feedback_text": {
                    "type": "string",
                    "default": "Hệ thống vận hành ổn định, đối soát nhanh.",
                },
                "category": {"type": "string", "default": "product_satisfaction"},
            },
            "required": ["user_id"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:support_submit_feedback",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/support.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "feedback_id",
                        "user_id",
                        "nps_score",
                        "category",
                        "aggregate_nps_score",
                        "total_responses",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "user_id", "result_path": "user_id"}),
            Postcondition("value_bounds", {"path": "nps_score", "min": 0, "max": 10}),
            Postcondition(
                "record_persisted",
                {"table": "feedback", "id_path": "feedback_id", "id_column": "id"},
            ),
        ),
        sop_steps=("validate-nps-score", "persist-feedback-row", "recalculate-nps-summary"),
        department_id="customer-success",
        layer_id="L4",
        gate_id="fulfillment-stable",
        jurisdiction="GLOBAL",
        rule_version="Mekong Customer Success NPS Ledger v1",
        output_contract={"evidence_type": "CUSTOMER_NPS_FEEDBACK"},
        test_id=f"{TEST_MODULE}::test_wave4a_customer_success_support_and_collab_ops",
    ),
    OperationSpec(
        op_id="collab.create-handoff",
        command="collab",
        subcommand="create_handoff",
        title="Khởi tạo biên bản bàn giao tác vụ liên phòng ban (CollaborationProtocol Handoff)",
        description=(
            "Create and validate a structured multi-agent delivery handoff message "
            "and persist to workspace collab.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "task_summary": {"type": "string", "minLength": 5, "maxLength": 300},
                "deliverable_ref": {
                    "type": "string",
                    "default": "docs/deliverables/release-bundle-v1.json",
                },
                "sender_role": {
                    "type": "string",
                    "enum": ["implementer", "reviewer", "tester", "planner", "researcher", "debugger"],
                    "default": "implementer",
                },
                "recipient_role": {
                    "type": "string",
                    "enum": ["implementer", "reviewer", "tester", "planner", "researcher", "debugger"],
                    "default": "reviewer",
                },
            },
            "required": ["task_summary"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:collab_create_handoff",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/collab.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "handoff_id",
                        "sender_role",
                        "recipient_role",
                        "task_summary",
                        "deliverable_ref",
                        "is_valid",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "task_summary", "result_path": "task_summary"}),
            Postcondition("enum_member", {"path": "status", "allowed": ["DISPATCHED"]}),
            Postcondition(
                "record_persisted",
                {"table": "collab_handoffs", "id_path": "handoff_id", "id_column": "handoff_id"},
            ),
        ),
        sop_steps=("register-collab-agents", "dispatch-review-handoff", "persist-collab-handoff"),
        department_id="customer-success",
        layer_id="L4",
        gate_id="fulfillment-stable",
        jurisdiction="GLOBAL",
        rule_version="Mekong Multi-Agent Collaboration Handoff Protocol v1",
        output_contract={"evidence_type": "COLLAB_HANDOFF_RECEIPT"},
        test_id=f"{TEST_MODULE}::test_wave4a_customer_success_support_and_collab_ops",
    ),
    OperationSpec(
        op_id="collab.accept-deliverable",
        command="collab",
        subcommand="accept_deliverable",
        title="Nghiệm thu bàn giao sản phẩm cho khách hàng (Client Acceptance L4 — Founder Gated)",
        description=(
            "Record formal client deliverable acceptance in workspace promise.db "
            "after FOUNDER_CONFIRMATION."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "deliverable_ref": {"type": "string", "minLength": 3, "maxLength": 240},
                "accepted_by": {"type": "string", "default": "Founder & Client Representative"},
                "nps_score": {"type": "integer", "minimum": 0, "maximum": 10, "default": 9},
                "notes": {"type": "string", "default": "Nghiệm thu bàn giao thành công theo SLA."},
            },
            "required": ["client_name", "deliverable_ref"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:collab_accept_deliverable",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/collab.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        approval_policy="FOUNDER_CONFIRMATION",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "acceptance_id",
                        "client_name",
                        "deliverable_ref",
                        "accepted_by",
                        "nps_score",
                        "acceptance_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "client_name", "result_path": "client_name"}),
            Postcondition("value_bounds", {"path": "nps_score", "min": 0, "max": 10}),
            Postcondition("enum_member", {"path": "acceptance_status", "allowed": ["ACCEPTED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "client_acceptances",
                    "id_path": "acceptance_id",
                    "id_column": "acceptance_id",
                },
            ),
        ),
        sop_steps=("founder-approval", "verify-deliverable-sla", "persist-client-acceptance"),
        department_id="customer-success",
        layer_id="L4",
        gate_id="fulfillment-stable",
        jurisdiction="GLOBAL",
        rule_version="Mekong L4 Fulfillment-Stable Client Acceptance Gate v1",
        output_contract={"evidence_type": "CLIENT_DELIVERABLE_ACCEPTANCE"},
        test_id=f"{TEST_MODULE}::test_wave4a_customer_success_support_and_collab_ops",
    ),
)

KNOWLEDGE_MEMORY_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="memory.store-note",
        command="memory",
        subcommand="store_note",
        title="Lưu trữ tri thức vận hành & bài học SOP vào kho bộ nhớ (MemoryStore L5)",
        description=(
            "Persist an institutional knowledge note and action outcome to workspace memory.db "
            "and JSONL memory corpus."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "minLength": 3, "maxLength": 200},
                "outcome": {"type": "string", "minLength": 3, "maxLength": 500},
                "agent_id": {"type": "string", "default": "knowledge-curator"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["topic", "outcome"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:memory_store_note",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/memory.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "note_id",
                        "topic",
                        "agent_id",
                        "outcome",
                        "tags_count",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "topic", "result_path": "topic"}),
            Postcondition("value_bounds", {"path": "tags_count", "min": 1, "max": 20}),
            Postcondition("enum_member", {"path": "status", "allowed": ["STORED"]}),
            Postcondition(
                "record_persisted",
                {"table": "memory_notes", "id_path": "note_id", "id_column": "note_id"},
            ),
        ),
        sop_steps=("append-memory-jsonl", "index-sqlite-note", "verify-note-persisted"),
        department_id="knowledge-memory",
        layer_id="L5",
        gate_id="scale-ready",
        jurisdiction="GLOBAL",
        rule_version="Mekong L5 Institutional Memory Standard v1",
        output_contract={"evidence_type": "INSTITUTIONAL_MEMORY_NOTE"},
        test_id=f"{TEST_MODULE}::test_wave4a_knowledge_memory_and_recall_ops",
    ),
    OperationSpec(
        op_id="memory.export-sop-pack",
        command="memory",
        subcommand="export_sop_pack",
        title="Đóng gói & xuất bộ quy trình chuẩn SOP sẵn sàng nhân bản (SOP Export L5)",
        description=(
            "Export a cryptographic SOP bundle and record clone-ready proof in workspace promise.db "
            "for L5 scale-ready verification."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "pack_name": {"type": "string", "minLength": 3, "maxLength": 160},
                "sop_count": {"type": "integer", "minimum": 1, "maximum": 200, "default": 12},
                "exported_by": {"type": "string", "default": "Knowledge Engine"},
            },
            "required": ["pack_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:memory_export_sop_pack",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/memory.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "export_id",
                        "pack_name",
                        "sop_count",
                        "bundle_sha256",
                        "artifact_path",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "pack_name", "result_path": "pack_name"}),
            Postcondition("value_bounds", {"path": "sop_count", "min": 1, "max": 200}),
            Postcondition("enum_member", {"path": "status", "allowed": ["EXPORTED"]}),
            Postcondition("artifact_written", {"path_from_result": "artifact_path", "min_bytes": 20}),
            Postcondition(
                "record_persisted",
                {"table": "sop_exports", "id_path": "export_id", "id_column": "export_id"},
            ),
        ),
        sop_steps=("compute-sop-bundle-digest", "record-sop-export-proof"),
        department_id="knowledge-memory",
        layer_id="L5",
        gate_id="scale-ready",
        jurisdiction="GLOBAL",
        rule_version="Mekong L5 Scale-Ready SOP Export Contract v1",
        output_contract={"evidence_type": "SOP_PACK_EXPORT_PROOF"},
        test_id=f"{TEST_MODULE}::test_wave4a_knowledge_memory_and_recall_ops",
    ),
    OperationSpec(
        op_id="recall.query-knowledge",
        command="recall",
        subcommand="query_knowledge",
        title="Truy vấn tri thức vận hành & lịch sử quyết định (Recall Knowledge Search)",
        description=(
            "Search institutional memory notes by keyword/tag and record the recall trace "
            "in workspace memory.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2, "maxLength": 200},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:recall_query_knowledge",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/memory.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "query_id",
                        "query",
                        "matches_count",
                        "top_matches",
                        "recall_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "query", "result_path": "query"}),
            Postcondition("value_bounds", {"path": "matches_count", "min": 0, "max": 50}),
            Postcondition(
                "enum_member",
                {"path": "recall_status", "allowed": ["MATCHED", "EMPTY_CORPUS_INDEXED"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "recall_queries", "id_path": "query_id", "id_column": "query_id"},
            ),
        ),
        sop_steps=("search-memory-corpus", "rank-recall-hits", "persist-recall-query"),
        department_id="knowledge-memory",
        layer_id="L5",
        gate_id="scale-ready",
        jurisdiction="GLOBAL",
        rule_version="Mekong L5 Institutional Recall Protocol v1",
        output_contract={"evidence_type": "KNOWLEDGE_RECALL_TRACE"},
        test_id=f"{TEST_MODULE}::test_wave4a_knowledge_memory_and_recall_ops",
    ),
    OperationSpec(
        op_id="recall.attest-clone-readiness",
        command="recall",
        subcommand="attest_clone_readiness",
        title="Xác nhận mức sẵn sàng nhân bản vận hành doanh nghiệp (L5 Scale-Ready Attestation)",
        description=(
            "Record an L5 scale-ready clone readiness attestation in workspace promise.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "clone_profile_name": {"type": "string", "minLength": 3, "maxLength": 160},
                "founder_name": {"type": "string", "default": "Founder"},
                "readiness_score": {"type": "integer", "minimum": 1, "maximum": 100, "default": 92},
                "statement": {
                    "type": "string",
                    "default": "SOP pack và kho tri thức đạt chuẩn nhân bản vận hành L5 Scale-Ready.",
                },
            },
            "required": ["clone_profile_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:recall_attest_clone_readiness",
        ),
        effects=(
            "WRITE:.mekong/workspaces/{workspace_id}/memory.db",
            "WRITE:.mekong/promise_evidence.db",
        ),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "attestation_id",
                        "clone_profile_name",
                        "readiness_score",
                        "status",
                    ]
                },
            ),
            Postcondition(
                "echoes_input",
                {"param_path": "clone_profile_name", "result_path": "clone_profile_name"},
            ),
            Postcondition("value_bounds", {"path": "readiness_score", "min": 1, "max": 100}),
            Postcondition("enum_member", {"path": "status", "allowed": ["ATTESTED"]}),
            Postcondition(
                "record_persisted",
                {"table": "attestations", "id_path": "attestation_id", "id_column": "attestation_id"},
            ),
        ),
        sop_steps=("verify-clone-profile", "record-scale-ready-attestation"),
        department_id="knowledge-memory",
        layer_id="L5",
        gate_id="scale-ready",
        jurisdiction="GLOBAL",
        rule_version="Mekong L5 Scale-Ready Clone Attestation v1",
        output_contract={"evidence_type": "CLONE_READINESS_ATTESTATION"},
        test_id=f"{TEST_MODULE}::test_wave4a_knowledge_memory_and_recall_ops",
    ),
)

MARKET_INTELLIGENCE_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="benchmark.run-suite",
        command="benchmark",
        subcommand="run_suite",
        title="Chạy bộ kiểm chuẩn năng lực & độ bền Agent (BenchmarkBridge Suite)",
        description=(
            "Execute deterministic PEV/routing/memory benchmark suite via BenchmarkBridge "
            "and persist results to workspace benchmark.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "suite": {
                    "type": "string",
                    "enum": ["pev", "routing", "memory", "chaos", "all"],
                    "default": "pev",
                },
                "iterations": {"type": "integer", "minimum": 1, "maximum": 20, "default": 2},
                "chaos_level": {
                    "type": "string",
                    "enum": ["none", "low", "medium", "high"],
                    "default": "none",
                },
            },
            "required": ["suite"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:benchmark_run_suite",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/benchmark.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "benchmark_id",
                        "suite",
                        "iterations",
                        "overall_score",
                        "pass_rate_pct",
                        "verdict",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "suite", "result_path": "suite"}),
            Postcondition("value_bounds", {"path": "overall_score", "min": 0, "max": 100}),
            Postcondition("enum_member", {"path": "verdict", "allowed": ["EXCELLENT", "PASS", "DEGRADED"]}),
            Postcondition(
                "record_persisted",
                {"table": "benchmark_runs", "id_path": "benchmark_id", "id_column": "benchmark_id"},
            ),
        ),
        sop_steps=("execute-benchmark-suite", "compute-resilience-score", "persist-benchmark-run"),
        department_id="market-intelligence",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="GLOBAL",
        rule_version="Mekong BenchmarkBridge Resilience Standard v1",
        output_contract={"evidence_type": "AGENT_BENCHMARK_REPORT"},
        test_id=f"{TEST_MODULE}::test_wave4a_market_intelligence_benchmark_and_eval_agent_ops",
    ),
    OperationSpec(
        op_id="benchmark.compare-competitors",
        command="benchmark",
        subcommand="compare_competitors",
        title="So sánh vị thế cạnh tranh & điểm khác biệt sản phẩm (Market Intelligence L1)",
        description=(
            "Evaluate competitive landscape differentiation for an offer segment and persist "
            "to workspace benchmark.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "segment_name": {"type": "string", "minLength": 3, "maxLength": 160},
                "competitors": {"type": "array", "items": {"type": "string"}},
                "our_strength_score": {"type": "integer", "minimum": 1, "maximum": 100, "default": 88},
            },
            "required": ["segment_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:benchmark_compare_competitors",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/benchmark.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "comparison_id",
                        "segment_name",
                        "competitors_evaluated",
                        "differentiation_score",
                        "positioning_verdict",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "segment_name", "result_path": "segment_name"}),
            Postcondition("value_bounds", {"path": "differentiation_score", "min": 1, "max": 100}),
            Postcondition(
                "enum_member",
                {
                    "path": "positioning_verdict",
                    "allowed": ["CATEGORY_LEADER", "COMPETITIVE_NICHE", "PARITY_RISK"],
                },
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "competitor_comparisons",
                    "id_path": "comparison_id",
                    "id_column": "comparison_id",
                },
            ),
        ),
        sop_steps=("score-competitor-matrix", "classify-positioning", "persist-competitor-comparison"),
        department_id="market-intelligence",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="GLOBAL",
        rule_version="Mekong L1 Market Intelligence Positioning Matrix v1",
        output_contract={"evidence_type": "COMPETITOR_BENCHMARK_MATRIX"},
        test_id=f"{TEST_MODULE}::test_wave4a_market_intelligence_benchmark_and_eval_agent_ops",
    ),
    OperationSpec(
        op_id="eval-agent.evaluate-quality",
        command="eval-agent",
        subcommand="evaluate_quality",
        title="Đánh giá chất lượng thực thi nhiệm vụ của Agent (EvalsBridge Mission Eval)",
        description=(
            "Record and score an agent mission execution in workspace evals.db via EvalsBridge."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "goal": {"type": "string", "minLength": 3, "maxLength": 300},
                "duration_ms": {"type": "integer", "minimum": 1, "default": 1250},
                "credits_used": {"type": "number", "minimum": 0, "default": 0.15},
                "quality_score": {"type": "integer", "minimum": 0, "maximum": 100, "default": 94},
            },
            "required": ["agent_id", "goal"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:eval_agent_evaluate_quality",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/evals.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "mission_id",
                        "agent_id",
                        "goal",
                        "quality_score",
                        "quality_grade",
                        "duration_ms",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "agent_id", "result_path": "agent_id"}),
            Postcondition("value_bounds", {"path": "quality_score", "min": 0, "max": 100}),
            Postcondition("enum_member", {"path": "quality_grade", "allowed": ["A", "B", "C"]}),
            Postcondition(
                "record_persisted",
                {"table": "mission_evals", "id_path": "mission_id", "id_column": "mission_id"},
            ),
        ),
        sop_steps=("measure-mission-telemetry", "grade-agent-quality", "persist-mission-eval"),
        department_id="market-intelligence",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="GLOBAL",
        rule_version="Mekong EvalsBridge Quality Scoring Standard v1",
        output_contract={"evidence_type": "AGENT_QUALITY_EVALUATION"},
        test_id=f"{TEST_MODULE}::test_wave4a_market_intelligence_benchmark_and_eval_agent_ops",
    ),
    OperationSpec(
        op_id="eval-agent.audit-safety",
        command="eval-agent",
        subcommand="audit_safety",
        title="Kiểm toán an toàn, che giấu bí mật & ranh giới thực thi của Agent (Agent Safety Audit)",
        description=(
            "Audit agent safety guardrails, secret redaction, and boundary compliance in workspace evals.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "minLength": 2, "maxLength": 120},
                "policy_profile": {"type": "string", "default": "VN_STATUTORY_STRICT"},
                "redaction_verified": {"type": "boolean", "default": True},
                "boundary_verified": {"type": "boolean", "default": True},
            },
            "required": ["agent_id"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:eval_agent_audit_safety",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/evals.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "safety_audit_id",
                        "agent_id",
                        "policy_profile",
                        "safety_score",
                        "violations_count",
                        "safety_verdict",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "agent_id", "result_path": "agent_id"}),
            Postcondition("value_bounds", {"path": "safety_score", "min": 0, "max": 100}),
            Postcondition(
                "enum_member",
                {"path": "safety_verdict", "allowed": ["SAFE_APPROVED", "REMEDIATION_REQUIRED"]},
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "agent_safety_audits",
                    "id_path": "safety_audit_id",
                    "id_column": "safety_audit_id",
                },
            ),
        ),
        sop_steps=("verify-secret-redaction", "check-stdlib-boundary", "persist-safety-audit"),
        department_id="market-intelligence",
        layer_id="L1",
        gate_id="offer-validated",
        jurisdiction="GLOBAL",
        rule_version="Mekong Agent Safety & Redaction Guardrail v1",
        output_contract={"evidence_type": "AGENT_SAFETY_AUDIT"},
        test_id=f"{TEST_MODULE}::test_wave4a_market_intelligence_benchmark_and_eval_agent_ops",
    ),
)

CEO_CSUITE_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="company.init-blueprint",
        command="company",
        subcommand="init_blueprint",
        title="Khởi tạo Bản thiết kế Doanh nghiệp L0 (Company Blueprint Initialization)",
        description=(
            "Generate an isolated company blueprint configuration inside the workspace "
            "and persist blueprint record to workspace company.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "product_type": {
                    "type": "string",
                    "enum": ["saas", "digital", "api_service", "consulting"],
                    "default": "saas",
                },
                "scenario": {
                    "type": "string",
                    "enum": ["local_first", "hybrid", "api_only", "apple_silicon"],
                    "default": "hybrid",
                },
                "budget_tier": {
                    "type": "string",
                    "enum": ["zero", "minimal", "hybrid", "unlimited"],
                    "default": "minimal",
                },
                "primary_language": {
                    "type": "string",
                    "enum": ["vi", "en", "both"],
                    "default": "vi",
                },
            },
            "required": ["company_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:company_init_blueprint",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/company.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "blueprint_id",
                        "company_name",
                        "product_type",
                        "scenario",
                        "budget_tier",
                        "files_generated_count",
                        "status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "company_name", "result_path": "company_name"}),
            Postcondition("value_bounds", {"path": "files_generated_count", "min": 1, "max": 20}),
            Postcondition("enum_member", {"path": "status", "allowed": ["INITIALIZED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "company_blueprints",
                    "id_path": "blueprint_id",
                    "id_column": "blueprint_id",
                },
            ),
        ),
        sop_steps=("validate-company-config", "render-blueprint-files", "persist-company-blueprint"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="VN",
        rule_version="Mekong L0 Company Blueprint Schema v1",
        output_contract={"evidence_type": "COMPANY_BLUEPRINT_RECORD"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="company.audit-readiness",
        command="company",
        subcommand="audit_readiness",
        title="Kiểm toán mức độ sẵn sàng 10 Phòng ban Doanh nghiệp (10-Department Readiness Audit)",
        description=(
            "Audit 10-department operational readiness score and persist to workspace company.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "company_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "departments_ready_count": {"type": "integer", "minimum": 1, "maximum": 10, "default": 10},
            },
            "required": ["company_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:company_audit_readiness",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/company.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "readiness_id",
                        "company_name",
                        "departments_ready_count",
                        "readiness_score",
                        "readiness_status",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "company_name", "result_path": "company_name"}),
            Postcondition("value_bounds", {"path": "readiness_score", "min": 10, "max": 100}),
            Postcondition(
                "enum_member",
                {
                    "path": "readiness_status",
                    "allowed": ["READY_FOR_EXECUTION", "BLUEPRINT_INCOMPLETE"],
                },
            ),
            Postcondition(
                "record_persisted",
                {
                    "table": "company_readiness_audits",
                    "id_path": "readiness_id",
                    "id_column": "readiness_id",
                },
            ),
        ),
        sop_steps=("score-10-departments", "classify-company-readiness", "persist-readiness-audit"),
        department_id="ceo-command",
        layer_id="L0",
        gate_id="company-blueprint",
        jurisdiction="VN",
        rule_version="Mekong 10-Department Operating Model Standard v1",
        output_contract={"evidence_type": "COMPANY_READINESS_AUDIT"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="cfo.forecast-runway",
        command="cfo",
        subcommand="forecast_runway",
        title="Dự báo dòng tiền & thời gian sống Runway (CFO Cash Runway Forecast)",
        description=(
            "Calculate monthly net burn and cash runway in months and persist forecast to workspace cfo.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "scenario_name": {"type": "string", "minLength": 2, "maxLength": 160},
                "cash_balance_vnd": {"type": "number", "minimum": 0, "default": 1_200_000_000.0},
                "monthly_burn_vnd": {"type": "number", "minimum": 1, "default": 150_000_000.0},
                "monthly_revenue_vnd": {"type": "number", "minimum": 0, "default": 90_000_000.0},
            },
            "required": ["scenario_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:cfo_forecast_runway",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/cfo.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "forecast_id",
                        "scenario_name",
                        "cash_balance_vnd",
                        "runway_months",
                        "risk_tier",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "scenario_name", "result_path": "scenario_name"}),
            Postcondition("value_bounds", {"path": "runway_months", "min": 0, "max": 120}),
            Postcondition("enum_member", {"path": "risk_tier", "allowed": ["HEALTHY", "WATCH", "CRITICAL"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "cfo_runway_forecasts",
                    "id_path": "forecast_id",
                    "id_column": "forecast_id",
                },
            ),
        ),
        sop_steps=("compute-net-burn", "project-runway-months", "persist-cfo-forecast"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="VN",
        rule_version="Mekong CFO Treasury & Runway Governance v1",
        output_contract={"evidence_type": "CFO_RUNWAY_FORECAST"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="cfo.approve-budget",
        command="cfo",
        subcommand="approve_budget",
        title="Phê duyệt ngân sách phòng ban (CFO Budget Allocation — Founder Gated)",
        description=(
            "Approve a departmental budget allocation in workspace cfo.db after FOUNDER_CONFIRMATION."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "department_name": {"type": "string", "minLength": 2, "maxLength": 120},
                "approved_amount_vnd": {"type": "number", "minimum": 1000},
                "fiscal_period": {"type": "string", "default": "Q4-2026"},
                "approved_by": {"type": "string", "default": "Founder & CFO"},
            },
            "required": ["department_name", "approved_amount_vnd"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:cfo_approve_budget",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/cfo.db",),
        external_effect="WORKSPACE_WRITE",
        approval_policy="FOUNDER_CONFIRMATION",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "approval_id",
                        "department_name",
                        "fiscal_period",
                        "approved_amount_vnd",
                        "approval_status",
                    ]
                },
            ),
            Postcondition(
                "echoes_input",
                {"param_path": "department_name", "result_path": "department_name"},
            ),
            Postcondition("value_bounds", {"path": "approved_amount_vnd", "min": 1000}),
            Postcondition("enum_member", {"path": "approval_status", "allowed": ["APPROVED"]}),
            Postcondition(
                "record_persisted",
                {
                    "table": "cfo_budget_approvals",
                    "id_path": "approval_id",
                    "id_column": "approval_id",
                },
            ),
        ),
        sop_steps=("founder-approval", "validate-budget-cap", "persist-budget-approval"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="VN",
        rule_version="Mekong CFO Capital Allocation Gate v1",
        output_contract={"evidence_type": "CFO_BUDGET_APPROVAL"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="cmo.plan-funnel",
        command="cmo",
        subcommand="plan_funnel",
        title="Thiết kế phễu tăng trưởng & chiến dịch đa kênh (CMO Funnel & Growth Experiment)",
        description=(
            "Create a marketing acquisition campaign and growth experiment via MarketingEngine "
            "in workspace marketing.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "funnel_name": {"type": "string", "minLength": 3, "maxLength": 160},
                "primary_channel": {
                    "type": "string",
                    "enum": ["zalo", "social", "seo", "email", "paid_ads"],
                    "default": "zalo",
                },
                "budget_usd": {"type": "number", "minimum": 0, "default": 2500.0},
                "target_audience": {"type": "string", "default": "Vietnamese SME Founders"},
                "hypothesis": {
                    "type": "string",
                    "default": "Zalo OA interactive demo increases qualified trials by 25%",
                },
            },
            "required": ["funnel_name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:cmo_plan_funnel",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/marketing.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "campaign_id",
                        "funnel_name",
                        "primary_channel",
                        "budget_usd",
                        "status",
                        "experiment_id",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "funnel_name", "result_path": "funnel_name"}),
            Postcondition("value_bounds", {"path": "budget_usd", "min": 0}),
            Postcondition(
                "record_persisted",
                {"table": "campaigns", "id_path": "campaign_id", "id_column": "id"},
            ),
        ),
        sop_steps=("create-funnel-campaign", "register-growth-experiment", "persist-marketing-funnel"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="VN",
        rule_version="Mekong CMO Growth Funnel Standard v1",
        output_contract={"evidence_type": "CMO_FUNNEL_PLAN"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="cmo.audit-channel-cac",
        command="cmo",
        subcommand="audit_channel_cac",
        title="Kiểm toán chi phí thu hút khách hàng CAC & hiệu suất kênh L3 (CMO Channel CAC Audit)",
        description=(
            "Audit channel CAC and LTV/CAC efficiency and persist channel metric proof in workspace promise.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "channel": {"type": "string", "minLength": 2, "maxLength": 120},
                "period": {"type": "string", "default": "2026-11"},
                "spend_vnd": {"type": "number", "minimum": 0, "default": 30_000_000.0},
                "leads": {"type": "integer", "minimum": 1, "default": 120},
                "conversions": {"type": "integer", "minimum": 1, "default": 15},
                "avg_ltv_vnd": {"type": "number", "minimum": 1000, "default": 12_000_000.0},
            },
            "required": ["channel"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:cmo_audit_channel_cac",
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
                        "metric_id",
                        "channel",
                        "period",
                        "cac_vnd",
                        "ltv_cac_ratio",
                        "efficiency_verdict",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "channel", "result_path": "channel"}),
            Postcondition("value_bounds", {"path": "cac_vnd", "min": 0}),
            Postcondition(
                "enum_member",
                {
                    "path": "efficiency_verdict",
                    "allowed": ["REPEATABLE_PROFITABLE", "OPTIMIZE_FUNNEL", "UNPROFITABLE"],
                },
            ),
            Postcondition(
                "record_persisted",
                {"table": "channel_metrics", "id_path": "metric_id", "id_column": "metric_id"},
            ),
        ),
        sop_steps=("compute-channel-cac", "evaluate-ltv-cac-ratio", "persist-channel-metric"),
        department_id="growth-marketing",
        layer_id="L3",
        gate_id="repeatable-channel",
        jurisdiction="VN",
        rule_version="Mekong L3 Repeatable-Channel CAC Standard v1",
        output_contract={"evidence_type": "CMO_CHANNEL_CAC_METRIC"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="cso.qualify-lead",
        command="cso",
        subcommand="qualify_lead",
        title="Chấm điểm BANT & thẩm định cơ hội bán hàng B2B (CSO Lead Qualification)",
        description=(
            "Qualify a B2B sales lead with BANT scoring and ROI projection via SalesEngine "
            "and persist deal to workspace sales.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "company": {"type": "string", "minLength": 2, "maxLength": 160},
                "deal_name": {"type": "string", "default": "Enterprise AI Operations Suite"},
                "estimated_value_usd": {"type": "number", "minimum": 100, "default": 18_000.0},
                "contact_email": {"type": "string", "default": "ceo@enterprise.vn"},
                "bant_score": {"type": "integer", "minimum": 0, "maximum": 100, "default": 85},
            },
            "required": ["company"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:cso_qualify_lead",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/sales.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "deal_id",
                        "company",
                        "deal_name",
                        "estimated_value_usd",
                        "stage",
                        "bant_score",
                        "qualification_verdict",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "company", "result_path": "company"}),
            Postcondition("value_bounds", {"path": "bant_score", "min": 0, "max": 100}),
            Postcondition(
                "enum_member",
                {
                    "path": "qualification_verdict",
                    "allowed": ["SQL_QUALIFIED", "MQL_NURTURE", "DISQUALIFIED"],
                },
            ),
            Postcondition(
                "record_persisted",
                {"table": "deals", "id_path": "deal_id", "id_column": "id"},
            ),
        ),
        sop_steps=("score-bant-criteria", "generate-deal-roi-prep", "persist-qualified-deal"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="VN",
        rule_version="Mekong CSO B2B Lead Qualification Standard v1",
        output_contract={"evidence_type": "CSO_QUALIFIED_DEAL"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
    OperationSpec(
        op_id="cso.review-pipeline",
        command="cso",
        subcommand="review_pipeline",
        title="Đánh giá độ phủ Pipeline doanh thu & tỷ lệ chuyển đổi (CSO Pipeline Review)",
        description=(
            "Audit sales pipeline metrics and quota coverage ratio via SalesEngine "
            "and persist review to workspace sales.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "review_period": {"type": "string", "minLength": 4, "default": "Q4-2026"},
                "target_quota_usd": {"type": "number", "minimum": 100, "default": 50_000.0},
            },
            "required": ["review_period"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_departments_wave4:cso_review_pipeline",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/sales.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "review_id",
                        "review_period",
                        "total_deals",
                        "total_pipeline_value",
                        "weighted_pipeline_value",
                        "coverage_ratio",
                        "pipeline_health",
                    ]
                },
            ),
            Postcondition("echoes_input", {"param_path": "review_period", "result_path": "review_period"}),
            Postcondition("value_bounds", {"path": "coverage_ratio", "min": 0}),
            Postcondition(
                "enum_member",
                {"path": "pipeline_health", "allowed": ["STRONG_COVERAGE", "BUILDING_PIPELINE"]},
            ),
            Postcondition(
                "record_persisted",
                {"table": "cso_pipeline_reviews", "id_path": "review_id", "id_column": "review_id"},
            ),
        ),
        sop_steps=("aggregate-pipeline-deals", "compute-quota-coverage", "persist-pipeline-review"),
        department_id="sales-revenue",
        layer_id="L3",
        gate_id="first-revenue",
        jurisdiction="VN",
        rule_version="Mekong CSO Revenue Pipeline Governance v1",
        output_contract={"evidence_type": "CSO_PIPELINE_REVIEW"},
        test_id=f"{TEST_MODULE}::test_wave4a_csuite_company_cfo_cmo_cso_ops",
    ),
)

DEPARTMENTS_WAVE4_OPERATIONS: tuple[OperationSpec, ...] = (
    *ENGINEERING_FACTORY_OPS,
    *CUSTOMER_SUCCESS_OPS,
    *KNOWLEDGE_MEMORY_OPS,
    *MARKET_INTELLIGENCE_OPS,
    *CEO_CSUITE_OPS,
)

__all__ = [
    "CEO_CSUITE_OPS",
    "CUSTOMER_SUCCESS_OPS",
    "DEPARTMENTS_WAVE4_OPERATIONS",
    "ENGINEERING_FACTORY_OPS",
    "KNOWLEDGE_MEMORY_OPS",
    "MARKET_INTELLIGENCE_OPS",
]
