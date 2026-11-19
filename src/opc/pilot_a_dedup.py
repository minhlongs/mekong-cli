"""Idempotent duplicate-event reconstruction helpers for Pilot A workflows."""
from __future__ import annotations

import json
from typing import Any

from src.opc.models import ActionPayload, ApprovalDecision, ApprovalToken, WorkflowStatus
from src.opc.quarantine import QuarantinedInput
from src.opc.state import StateStore


def find_run_by_request_id(
    state: StateStore,
    request_id: str,
    *,
    tenant_id: str | None = None,
) -> dict[str, Any] | None:
    """Retrieve the first persisted run matching proposal_input.request_id (scoped to tenant_id when provided)."""
    if not (clean_id := request_id.strip()):
        return None
    clean_tenant = tenant_id.strip() if tenant_id else None
    with state._get_connection() as conn:  # noqa: SLF001
        for row in conn.execute("SELECT * FROM opc_runs ORDER BY created_at ASC, rowid ASC").fetchall():
            try:
                inp = json.loads(row["proposal_input_json"])
            except (TypeError, ValueError):
                continue
            if not (isinstance(inp, dict) and str(inp.get("request_id", "")).strip() == clean_id):
                continue
            action_payload = json.loads(row["action_payload_json"]) if row["action_payload_json"] else None
            if clean_tenant is not None:
                row_tenant = str(((action_payload or {}).get("parameters") or {}).get("tenant_id", "")).strip()
                if row_tenant != clean_tenant:
                    continue
            return {
                "run_id": row["run_id"],
                "pack_id": row["pack_id"],
                "status": WorkflowStatus(row["status"]),
                "business_profile": json.loads(row["business_profile_json"]),
                "proposal_input": inp,
                "proposal_draft": json.loads(row["proposal_draft_json"]) if row["proposal_draft_json"] else None,
                "action_payload": action_payload,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
    return None


def get_latest_approval_for_run(state: StateStore, run_id: str) -> ApprovalToken | None:
    """Retrieve the most recent approval token recorded for a run."""
    with state._get_connection() as conn:  # noqa: SLF001
        row = conn.execute(
            "SELECT * FROM opc_approvals WHERE run_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
            (run_id,),
        ).fetchone()
        if not row:
            return None
        return ApprovalToken(
            token_id=row["token_id"],
            run_id=row["run_id"],
            action_digest=row["action_digest"],
            principal=row["principal"],
            decision=ApprovalDecision(row["decision"]),
            created_at=int(row["created_at"]),
            expires_at=int(row["expires_at"]),
            consumed=bool(row["consumed"]),
            revoked=bool(row["revoked"]),
            revision_notes=str(row["revision_notes"] or ""),
            signature=str(row["signature"] or ""),
        )


def rebuild_existing_approval_card(
    state: StateStore,
    card_cls: type[Any],
    event: Any,
    q_msg: QuarantinedInput,
    redacted_notes: str,
    citations: tuple[dict[str, Any], ...],
    runtime_engine: str,
    default_vat_rate_pct: int,
    *,
    tenant_id: str | None = None,
) -> Any | None:
    """Reconstruct an existing ApprovalCard for a deduplicated event_id without minting a new run."""
    existing = find_run_by_request_id(state, event.event_id, tenant_id=tenant_id)
    if not existing:
        return None
    persisted_input = existing.get("proposal_input") or {}
    action_dict = existing.get("action_payload") or {}
    if not action_dict:
        return None
    incoming_sender = str(event.sender_id).strip()
    incoming_contact = f"zalo:{incoming_sender}"
    persisted_sender = str(persisted_input.get("sender_id", "")).strip()
    persisted_contact = str(persisted_input.get("client_contact") or action_dict.get("recipient") or "").strip()
    if not persisted_sender and not persisted_contact:
        return None
    if persisted_sender and persisted_sender != incoming_sender:
        return None
    if persisted_contact and persisted_contact != incoming_contact:
        return None
    token = get_latest_approval_for_run(state, existing["run_id"])
    if token is None:
        return None
    params = dict(action_dict.get("parameters") or {})
    payload = ActionPayload(
        principal=str(action_dict["principal"]),
        capability=str(action_dict["capability"]),
        connector=str(action_dict["connector"]),
        recipient=str(action_dict["recipient"]),
        content=str(action_dict["content"]),
        parameters=params,
        attachments=tuple(action_dict.get("attachments", [])),
        budget_amount=str(action_dict["budget_amount"]),
        budget_currency=str(action_dict["budget_currency"]),
        expires_at=int(action_dict["expires_at"]),
    )
    draft_info = existing.get("proposal_draft") or {}
    amount_vnd = int(params.get("amount_vnd", 0))
    subtotal_vnd = int(params.get("subtotal_vnd", draft_info.get("subtotal_vnd", amount_vnd)))
    vat_rate_pct = int(params.get("vat_rate_pct", draft_info.get("vat_rate_pct", default_vat_rate_pct)))
    vat_amount_vnd = int(params.get("vat_amount_vnd", draft_info.get("vat_amount_vnd", max(0, amount_vnd - subtotal_vnd))))
    emvco = str(params.get("vietqr_emvco", ""))
    quicklink = str(params.get("vietqr_quicklink", ""))
    line_items = tuple(draft_info.get("line_items") or ())
    run_id = str(existing["run_id"])
    client_name = str(persisted_input.get("client_name") or "Khách hàng SME")
    client_contact = persisted_contact or f"zalo:{persisted_sender}"
    project_title = str(persisted_input.get("project_title") or draft_info.get("project_title") or params.get("project_title") or "")
    currency = str(persisted_input.get("currency") or action_dict.get("budget_currency") or "VND")
    persisted_notes = str(persisted_input.get("notes") or "")
    rendered = (
        f"[PHIẾU PHÊ DUYỆT BÁO GIÁ - PILOT A]\nMã phiên: {run_id} | Khách: {client_name}\n"
        f"Dự án: {project_title} | Tổng: {amount_vnd:,} {currency}\n"
        f"VietQR: {emvco[:32]}... | HMAC: {token.signature[:16]}..."
    )
    return card_cls(
        run_id, event.event_id, client_name, client_contact, project_title,
        amount_vnd, currency, emvco, quicklink, token, payload, q_msg,
        rendered, persisted_notes, line_items, citations, "", runtime_engine,
        subtotal_vnd, vat_rate_pct, vat_amount_vnd,
    )
