# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Executable operation contracts for OPC (One-Person Company) and Zalo Official Account.

Registers the seven customer-communication and business-pack operations for
``opc`` and ``zalo-oa``:

* ``opc.status`` — inspect OPC pack registry and workspace run/approval/action counts
* ``opc.pilot-a`` — execute Pilot A vertical slice (QuarantineFloor -> Quote + VietQR -> ApprovalCard)
* ``opc.send-message`` — quarantine content, verify founder approval, and dispatch approved follow-up
* ``zalo-oa.add-follower`` — register or update a Zalo OA follower in workspace ``zalo.db``
* ``zalo-oa.generate-caption`` — generate a multi-tone social marketing caption and persist it
* ``zalo-oa.send-message`` — send a direct Zalo OA message (gated by ``FOUNDER_CONFIRMATION``)
* ``zalo-oa.broadcast`` — broadcast a segmented Zalo OA campaign (gated by ``FOUNDER_CONFIRMATION``)
"""

from __future__ import annotations

from src.core.promise.contracts import HandlerRef, OperationSpec, Postcondition

TEST_MODULE = "tests/test_promise_opc_zalo_ops.py"

OPC_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="opc.status",
        command="opc",
        subcommand="status",
        title="Tra cứu trạng thái gói nghiệp vụ OPC và sổ cái phiên chạy",
        description=(
            "Inspect registered OPC business packs and workspace-scoped run, approval, and action counts."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "pack_id": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 80,
                    "default": "client-proposal-followup",
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_opc_zalo:opc_workspace_status"
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/opc.db",),
        external_effect="NONE",
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["status", "pack_id", "capabilities", "total_runs", "db_path"]},
            ),
            Postcondition("enum_member", {"path": "status", "allowed": ["OPERATIONAL"]}),
            Postcondition("value_bounds", {"path": "total_runs", "min": 0}),
        ),
        sop_steps=("inspect-packs", "count-ledger", "verify"),
        department_id="executive-ops",
        layer_id="L1",
        jurisdiction="VN",
        rule_version="OPC Pack Schema opc-pack/v1",
        output_contract={"evidence_type": "OPC_WORKSPACE_STATUS"},
        test_id=f"{TEST_MODULE}::test_opc_status_reports_packs_and_workspace_counts",
    ),
    OperationSpec(
        op_id="opc.pilot-a",
        command="opc",
        subcommand="pilot_a",
        title="Báo giá tự động Pilot A (Quarantine -> Báo giá Decimal + VietQR -> Thẻ phê duyệt)",
        description=(
            "Validate incoming inquiry against QuarantineFloor and the 48h Zalo interaction window, "
            "compute a deterministic Decimal quote with EMVCo VietQR, and persist the run in opc.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 1000,
                    "default": "Nhờ báo giá gói tư vấn AI và VietQR 10 giờ.",
                },
                "client_name": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 120,
                    "default": "Công ty TNHH Sao Mai",
                },
                "sender_id": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 64,
                    "default": "84901112233",
                },
                "project_title": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 160,
                    "default": "Tư Vấn AI & VietQR",
                },
                "estimated_hours": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 2000,
                    "default": 10,
                },
            },
            "required": [],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_opc_zalo:opc_pilot_a_quote"
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/opc.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "run_id",
                        "total_amount_vnd",
                        "vietqr_emvco",
                        "approval_token_id",
                        "quarantine_safe",
                    ]
                },
            ),
            Postcondition("value_bounds", {"path": "total_amount_vnd", "min": 1}),
            Postcondition("enum_member", {"path": "status", "allowed": ["PENDING_APPROVAL"]}),
            Postcondition(
                "record_persisted",
                {"table": "opc_runs", "match": {"run_id": "{result.run_id}"}},
            ),
        ),
        sop_steps=("intake", "quarantine-check", "compute-quote", "generate-vietqr", "persist-run"),
        department_id="sales-revenue",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="OPC Pilot A + Napas 247 VietQR EMVCo",
        output_contract={"evidence_type": "OPC_PILOT_A_PROPOSAL"},
        test_id=f"{TEST_MODULE}::test_opc_pilot_a_persists_quote_and_blocks_prompt_injection",
    ),
    OperationSpec(
        op_id="opc.send-message",
        command="opc",
        subcommand="send_message",
        title="Gửi thông điệp phản hồi báo giá OPC (yêu cầu Founder phê duyệt)",
        description=(
            "Inspect outbound proposal follow-up message through QuarantineFloor and dispatch it "
            "after founder approval, recording the action in workspace opc.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "minLength": 2, "maxLength": 120},
                "project_title": {"type": "string", "minLength": 2, "maxLength": 160},
                "content": {"type": "string", "minLength": 3, "maxLength": 2000},
                "language": {"type": "string", "enum": ["vi", "en"], "default": "vi"},
                "estimated_hours": {"type": "integer", "minimum": 1, "maximum": 2000, "default": 10},
            },
            "required": ["recipient", "project_title", "content"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            callable_path="src.core.promise.ops.handlers_opc_zalo:opc_send_approved_followup"
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/opc.db",),
        external_effect="SEND_MESSAGE",
        approval_policy="FOUNDER_CONFIRMATION",
        idempotency_fields=("recipient", "project_title", "content"),
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "run_id",
                        "idempotency_key",
                        "recipient",
                        "dispatch_status",
                        "followup_draft",
                    ]
                },
            ),
            Postcondition(
                "echoes_input",
                {
                    "pairs": [
                        {"result_path": "recipient", "param_path": "recipient"},
                        {"result_path": "project_title", "param_path": "project_title"},
                    ]
                },
            ),
            Postcondition("enum_member", {"path": "dispatch_status", "allowed": ["completed", "deduplicated"]}),
            Postcondition(
                "record_persisted",
                {"table": "opc_actions", "match": {"idempotency_key": "{result.idempotency_key}"}},
            ),
        ),
        sop_steps=("quarantine-check", "await-founder-approval", "dispatch-connector", "verify"),
        department_id="sales-revenue",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="OPC Payload-Bound HMAC Approval v1",
        output_contract={"evidence_type": "OPC_APPROVED_ACTION"},
        test_id=f"{TEST_MODULE}::test_opc_send_message_requires_founder_approval_and_persists_action",
    ),
)

ZALO_OA_OPS: tuple[OperationSpec, ...] = (
    OperationSpec(
        op_id="zalo-oa.add-follower",
        command="zalo-oa",
        subcommand="add_follower",
        title="Đăng ký hoặc cập nhật người quan tâm Zalo OA theo phân khúc",
        description=(
            "Register or update a follower in the workspace-scoped Zalo OA database with segment tagging."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "minLength": 3, "maxLength": 64},
                "name": {"type": "string", "minLength": 2, "maxLength": 120},
                "phone": {"type": "string", "maxLength": 24, "default": ""},
                "segment": {
                    "type": "string",
                    "enum": ["vip", "active", "standard"],
                    "default": "standard",
                },
            },
            "required": ["user_id", "name"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.zalo_engine",
            factory="ZaloEngine",
            method="add_follower",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/zalo.db",),
        external_effect="WORKSPACE_WRITE",
        idempotency_fields=("user_id", "segment"),
        postconditions=(
            Postcondition("output_fields", {"required": ["ok", "user_id", "name", "segment"]}),
            Postcondition(
                "echoes_input",
                {
                    "pairs": [
                        {"result_path": "user_id", "param_path": "user_id"},
                        {"result_path": "name", "param_path": "name"},
                    ]
                },
            ),
            Postcondition(
                "record_persisted",
                {"table": "followers", "match": {"user_id": "{result.user_id}"}},
            ),
        ),
        sop_steps=("validate-follower", "upsert-follower", "verify"),
        department_id="marketing-growth",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Zalo OA Follower Segmentation v1",
        output_contract={"evidence_type": "ZALO_FOLLOWER_RECORD"},
        test_id=f"{TEST_MODULE}::test_zalo_add_follower_and_generate_caption_persist_to_workspace_db",
    ),
    OperationSpec(
        op_id="zalo-oa.generate-caption",
        command="zalo-oa",
        subcommand="generate_caption",
        title="Khởi tạo nội dung bài đăng Zalo OA đa giọng điệu kèm hashtag",
        description=(
            "Generate a structured Vietnamese social caption in the selected tone and persist it to zalo.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "topic": {"type": "string", "minLength": 3, "maxLength": 300},
                "tone": {
                    "type": "string",
                    "enum": ["vui_ve", "chuyen_nghiep", "sang_tao", "khuyen_mai", "binh_phap"],
                    "default": "vui_ve",
                },
                "save": {"type": "boolean", "enum": [True], "default": True},
            },
            "required": ["topic"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.zalo_engine",
            factory="ZaloEngine",
            method="generate_caption",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/zalo.db",),
        external_effect="WORKSPACE_WRITE",
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["caption_id", "topic", "tone", "content", "hashtags"]},
            ),
            Postcondition(
                "echoes_input",
                {"pairs": [{"result_path": "topic", "param_path": "topic"}]},
            ),
            Postcondition(
                "enum_member",
                {
                    "path": "tone",
                    "allowed": ["vui_ve", "chuyen_nghiep", "sang_tao", "khuyen_mai", "binh_phap"],
                },
            ),
            Postcondition(
                "record_persisted",
                {"table": "captions", "match": {"caption_id": "{result.caption_id}"}},
            ),
        ),
        sop_steps=("select-tone", "compose-caption", "persist-caption", "verify"),
        department_id="marketing-growth",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Zalo OA Multi-Tone Content Engine v1",
        output_contract={"evidence_type": "ZALO_SOCIAL_CAPTION"},
        test_id=f"{TEST_MODULE}::test_zalo_add_follower_and_generate_caption_persist_to_workspace_db",
    ),
    OperationSpec(
        op_id="zalo-oa.send-message",
        command="zalo-oa",
        subcommand="send_message",
        title="Gửi tin nhắn trực tiếp Zalo OA tới khách hàng (yêu cầu Founder phê duyệt)",
        description=(
            "Send a direct customer service message via Zalo OA after founder confirmation and persist "
            "the delivery record in workspace zalo.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "minLength": 3, "maxLength": 64},
                "text": {"type": "string", "minLength": 1, "maxLength": 2000},
                "template": {"type": "string", "maxLength": 80, "default": ""},
                "save": {"type": "boolean", "enum": [True], "default": True},
            },
            "required": ["user_id", "text"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.zalo_engine",
            factory="ZaloEngine",
            method="send_message",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/zalo.db",),
        external_effect="SEND_MESSAGE",
        approval_policy="FOUNDER_CONFIRMATION",
        idempotency_fields=("user_id", "text"),
        postconditions=(
            Postcondition(
                "output_fields",
                {"required": ["message_id", "user_id", "text", "status", "sent_at"]},
            ),
            Postcondition(
                "echoes_input",
                {
                    "pairs": [
                        {"result_path": "user_id", "param_path": "user_id"},
                        {"result_path": "text", "param_path": "text"},
                    ]
                },
            ),
            Postcondition("enum_member", {"path": "status", "allowed": ["delivered"]}),
            Postcondition(
                "record_persisted",
                {"table": "messages", "match": {"message_id": "{result.message_id}"}},
            ),
        ),
        sop_steps=("await-founder-approval", "dispatch-message", "persist-delivery", "verify"),
        department_id="customer-ops",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Zalo OA Customer Messaging v1",
        output_contract={"evidence_type": "ZALO_DIRECT_MESSAGE"},
        test_id=f"{TEST_MODULE}::test_zalo_send_message_and_broadcast_require_approval_and_persist",
    ),
    OperationSpec(
        op_id="zalo-oa.broadcast",
        command="zalo-oa",
        subcommand="broadcast",
        title="Phát sóng chiến dịch Zalo OA theo phân khúc (yêu cầu Founder phê duyệt)",
        description=(
            "Dispatch a targeted broadcast campaign to followers in the selected segment after founder "
            "confirmation and record the campaign in workspace zalo.db."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 160},
                "text": {"type": "string", "minLength": 3, "maxLength": 2000},
                "target_segment": {
                    "type": "string",
                    "enum": ["all", "vip", "active", "standard"],
                    "default": "all",
                },
                "save": {"type": "boolean", "enum": [True], "default": True},
            },
            "required": ["title", "text"],
            "additionalProperties": False,
        },
        handler=HandlerRef(
            module="src.core.zalo_engine",
            factory="ZaloEngine",
            method="broadcast_campaign",
        ),
        effects=("WRITE:.mekong/workspaces/{workspace_id}/zalo.db",),
        external_effect="SEND_MESSAGE",
        approval_policy="FOUNDER_CONFIRMATION",
        idempotency_fields=("title", "target_segment", "text"),
        postconditions=(
            Postcondition(
                "output_fields",
                {
                    "required": [
                        "broadcast_id",
                        "title",
                        "target_segment",
                        "recipients_count",
                        "status",
                    ]
                },
            ),
            Postcondition(
                "echoes_input",
                {
                    "pairs": [
                        {"result_path": "title", "param_path": "title"},
                        {"result_path": "target_segment", "param_path": "target_segment"},
                    ]
                },
            ),
            Postcondition("enum_member", {"path": "status", "allowed": ["completed"]}),
            Postcondition(
                "record_persisted",
                {"table": "broadcasts", "match": {"broadcast_id": "{result.broadcast_id}"}},
            ),
        ),
        sop_steps=("segment-followers", "await-founder-approval", "broadcast-campaign", "verify"),
        department_id="marketing-growth",
        layer_id="L2",
        jurisdiction="VN",
        rule_version="Zalo OA Broadcast Campaign v1",
        output_contract={"evidence_type": "ZALO_BROADCAST_CAMPAIGN"},
        test_id=f"{TEST_MODULE}::test_zalo_send_message_and_broadcast_require_approval_and_persist",
    ),
)

OPC_ZALO_OPERATIONS: tuple[OperationSpec, ...] = (
    *OPC_OPS,
    *ZALO_OA_OPS,
)

__all__ = ["OPC_OPS", "OPC_ZALO_OPERATIONS", "ZALO_OA_OPS"]
