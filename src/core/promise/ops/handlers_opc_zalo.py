# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Composite handlers for OPC (One-Person Company) and Zalo Official Account operations.

Every handler executes against a workspace-scoped SQLite database (``opc.db`` or
``zalo.db``) resolved through :func:`src.core.promise.ops.handlers_finance.engine_db`
and enforces deterministic ``QuarantineFloor`` checks on untrusted inbound text.
"""

from __future__ import annotations

import pathlib
import sqlite3
import time
import typing
from decimal import Decimal

from src.core.promise.ops.handlers_finance import engine_db
from src.core.promise.runtime import HandlerContext


def _default_pack_manifest_path() -> pathlib.Path:
    return (
        pathlib.Path(__file__).resolve().parents[3]
        / "opc"
        / "packs"
        / "client-proposal-followup"
        / "pack.json"
    )


def opc_workspace_status(
    context: HandlerContext,
    pack_id: str = "client-proposal-followup",
) -> dict[str, typing.Any]:
    """Inspect OPC pack registry and workspace-scoped ``opc.db`` run/action counts."""
    from src.opc.manifest import (
        SUPPORTED_RUNTIMES,
        SUPPORTED_SCHEMA_VERSIONS,
        PackRegistry,
        load_pack_manifest,
    )
    from src.opc.state import StateStore

    db_file = engine_db(context, "opc")
    state = StateStore(db_file)
    manifest_path = _default_pack_manifest_path()

    packs_dir = manifest_path.parent.parent
    registry = PackRegistry()
    if packs_dir.is_dir():
        registry.discover_from_dir(packs_dir)

    target_pack_id = pack_id or "client-proposal-followup"
    manifest = registry.get(target_pack_id)
    if manifest is None:
        if target_pack_id == "client-proposal-followup" and manifest_path.is_file():
            manifest = load_pack_manifest(manifest_path)
        else:
            raise ValueError(f"Unknown OPC pack_id: {target_pack_id}")

    with sqlite3.connect(str(state.db_path), timeout=5.0) as conn:
        total_runs = int(conn.execute("SELECT COUNT(*) FROM opc_runs").fetchone()[0])
        total_approvals = int(conn.execute("SELECT COUNT(*) FROM opc_approvals").fetchone()[0])
        total_actions = int(conn.execute("SELECT COUNT(*) FROM opc_actions").fetchone()[0])

    return {
        "status": "OPERATIONAL",
        "pack_id": manifest.pack_id,
        "schema_version": manifest.schema_version,
        "compatible_runtime": manifest.compatible_runtime,
        "capabilities": list(manifest.capabilities),
        "connectors": list(manifest.connectors),
        "packs": [p.pack_id for p in registry.list_packs()],
        "supported_runtimes": sorted(list(SUPPORTED_RUNTIMES)),
        "supported_schema_versions": sorted(list(SUPPORTED_SCHEMA_VERSIONS)),
        "total_runs": total_runs,
        "total_approvals": total_approvals,
        "total_actions": total_actions,
        "db_path": str(state.db_path),
    }


def opc_pilot_a_quote(
    context: HandlerContext,
    message: str = "Nhờ báo giá gói tư vấn AI và VietQR 10 giờ.",
    client_name: str = "Công ty TNHH Sao Mai",
    sender_id: str = "84901112233",
    project_title: str = "Tư Vấn AI & VietQR",
    estimated_hours: int = 10,
) -> dict[str, typing.Any]:
    """Run Pilot A vertical slice (QuarantineFloor -> Quote + VietQR -> ApprovalCard) in workspace ``opc.db``."""
    from src.opc.mekong_bench import _bench_profile
    from src.opc.pilot_a import PilotAWorkflow, ZaloWebhookEvent

    db_file = engine_db(context, "opc")
    profile = _bench_profile()
    wf = PilotAWorkflow(db_path=db_file, profile=profile)
    now_ts = int(time.time())
    event_id = f"evt_{context.run_id or 'pilot_a'}"
    event = ZaloWebhookEvent(
        event_id=event_id,
        oa_id="oa_workspace",
        sender_id=sender_id,
        sender_name=client_name,
        message_text=message,
        timestamp=now_ts,
        last_user_interaction_ts=now_ts - 1200,
        requested_services=("tu_van_ai", "tich_hop_vietqr"),
        estimated_hours=int(estimated_hours),
        project_title=project_title,
        currency="VND",
        language="vi",
    )
    card = wf.handle_webhook(event)
    return {
        "run_id": card.run_id,
        "event_id": card.event_id,
        "pack_id": wf.engine.manifest.pack_id,
        "client_name": card.client_name,
        "client_contact": card.client_contact,
        "project_title": card.project_title,
        "total_amount_vnd": card.total_amount_vnd,
        "currency": card.currency,
        "vietqr_emvco": card.vietqr_emvco,
        "vietqr_quicklink": card.vietqr_quicklink,
        "approval_token_id": card.approval_token.token_id,
        "quarantine_safe": card.quarantine_report.is_safe,
        "status": "PENDING_APPROVAL",
    }


def opc_send_approved_followup(
    context: HandlerContext,
    recipient: str,
    project_title: str,
    content: str,
    language: str = "vi",
    estimated_hours: int = 10,
) -> dict[str, typing.Any]:
    """Quarantine message content, issue HMAC-bound token, and dispatch approved follow-up in ``opc.db``."""
    from src.opc.connectors.mock import MockConnector
    from src.opc.engine import OPCEngine
    from src.opc.manifest import load_pack_manifest
    from src.opc.models import ApprovalDecision, BusinessProfile, ProposalInput, WorkflowStatus
    from src.opc.pilot_a import ZaloSandboxConnector
    from src.opc.quarantine import QuarantineFloor
    from src.opc.state import StateStore
    from src.opc.usage import UsageLedger

    floor = QuarantineFloor()
    report = floor.inspect(content, source=f"opc.send-message:{recipient}")
    floor.enforce_before_tool(report)

    db_file = engine_db(context, "opc")
    manifest = load_pack_manifest(_default_pack_manifest_path())
    state = StateStore(db_file)
    usage = UsageLedger(db_file)
    engine = OPCEngine(
        manifest,
        state,
        usage,
        connectors={
            "mock_followup_draft": MockConnector(),
            "zalo_oa_sandbox": ZaloSandboxConnector(),
        },
    )
    profile = BusinessProfile(
        business_name="CÔNG TY TNHH MEKONG OPC",
        owner_name=context.principal_id or "founder",
        language=language,
        locale="vi_VN" if language == "vi" else "en_US",
        timezone="Asia/Ho_Chi_Minh",
        currency="VND",
        services={"tu_van_ai": Decimal("600000"), "tich_hop_vietqr": Decimal("400000")},
        payment_terms="Thanh toán 100% qua VietQR",
        jurisdiction="VN",
    )
    intake = ProposalInput(
        request_id=f"req_{context.run_id or 'followup'}",
        client_name=recipient,
        client_contact=recipient,
        project_title=project_title,
        requested_services=("tu_van_ai", "tich_hop_vietqr"),
        estimated_hours=int(estimated_hours),
        currency="VND",
        language=language,
        notes=content,
    )
    active_run_id, draft, payload = engine.generate_draft(profile, intake, run_id=context.run_id or None)
    now_ts = int(time.time())
    token = engine.approval_engine.issue_token(
        active_run_id, payload, decision=ApprovalDecision.APPROVE
    )
    state.save_approval(token)
    idempotency_key = f"idem_{active_run_id}"
    outcome = engine.execute_approved_action(
        token, payload, idempotency_key=idempotency_key
    )
    if outcome.get("status") == "completed":
        state.save_run(
            run_id=active_run_id,
            pack_id=manifest.pack_id,
            status=WorkflowStatus.COMPLETED,
            profile_data={"business_name": profile.business_name, "owner_name": profile.owner_name},
            input_data={"request_id": intake.request_id, "client_name": intake.client_name},
            now=now_ts,
            draft_data={"total_amount": draft.total_amount, "rendered": draft.rendered_proposal},
            action_payload_data=payload.__dict__,
        )
    return {
        "run_id": active_run_id,
        "idempotency_key": idempotency_key,
        "recipient": recipient,
        "project_title": project_title,
        "capability": payload.capability,
        "connector": payload.connector,
        "dispatch_status": outcome.get("status"),
        "followup_draft": outcome.get("followup_draft", ""),
        "quarantine_safe": report.is_safe,
    }


__all__ = [
    "opc_pilot_a_quote",
    "opc_send_approved_followup",
    "opc_workspace_status",
]
