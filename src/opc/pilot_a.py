"""Pilot A End-to-End Vertical Slice: Zalo OA → Consent/Quarantine/Quota → Quote + VietQR → Approval → Draft."""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

from src.core.vietqr_engine import VietQrEngine
from src.opc.accounting_draft import AccountingDraftExport, build_accounting_draft_export, reconcile_signed_vietqr_webhook
from src.opc.connectors.base import ConnectorProtocol, ConnectorResult
from src.opc.connectors.mock import MockConnector
from src.opc.connectors.zalo_http import ZaloOAConnector, ZaloWebhookMacError, verify_zalo_webhook_mac
from src.opc.engine import OPCEngine
from src.opc.manifest import load_pack_manifest
from src.opc.models import ActionPayload, ApprovalDecision, ApprovalToken, BusinessProfile, ProposalInput, WorkflowStatus
from src.opc.privacy_guard import PilotPrivacyGuard, redact_vietnamese_pii, resolve_tenant_db_path, verify_confidence_and_math
from src.opc.quarantine import QuarantinedInput, QuarantineFloor
from src.opc.quota import WorkflowQuotaExceededError
from src.opc.state import StateStore
from src.opc.usage import UsageLedger

ZALO_INTERACTION_WINDOW_SECONDS: Final[int] = 48 * 3600
_RUN_STATUS_MAP: Final[dict[str, WorkflowStatus]] = {
    "completed": WorkflowStatus.COMPLETED, "deduplicated": WorkflowStatus.COMPLETED,
    "reconciliation_required": WorkflowStatus.RECONCILIATION_REQUIRED,
    "failed": WorkflowStatus.FAILED, "budget_exceeded": WorkflowStatus.FAILED,
}


class ZaloInteractionWindowError(PermissionError):
    """Raised when a Zalo OA message is outside the 48-hour customer service window."""


@dataclass(frozen=True)
class ZaloWebhookEvent:
    event_id: str
    oa_id: str
    sender_id: str
    sender_name: str
    message_text: str
    timestamp: int
    last_user_interaction_ts: int
    requested_services: tuple[str, ...]
    estimated_hours: int
    project_title: str
    currency: str = "VND"
    language: str = "vi"
    extraction_confidence: float = 1.0


@dataclass(frozen=True)
class ApprovalCard:
    run_id: str
    event_id: str
    client_name: str
    client_contact: str
    project_title: str
    total_amount_vnd: int
    currency: str
    vietqr_emvco: str
    vietqr_quicklink: str
    approval_token: ApprovalToken
    action_payload: ActionPayload
    quarantine_report: QuarantinedInput
    rendered_card_vi: str
    redacted_notes: str = ""
    line_items: tuple[dict[str, Any], ...] = ()


class ZaloSandboxConnector:
    """Offline Zalo OA sandbox connector enforcing the 48h window and idempotency."""

    def __init__(self, connector_id: str = "zalo_oa_sandbox", simulate_uncertain: bool = False) -> None:
        self.connector_id, self.simulate_uncertain = connector_id, simulate_uncertain
        self.dispatched: dict[str, dict[str, Any]] = {}

    def dispatch(self, idempotency_key: str, payload: ActionPayload, *, now: int | None = None) -> ConnectorResult:
        if idempotency_key in self.dispatched:
            return ConnectorResult(True, self.connector_id, "completed", {"deduplicated": True, "record": self.dispatched[idempotency_key]})
        if self.simulate_uncertain:
            return ConnectorResult(False, self.connector_id, "uncertain_reconciliation_required", {}, "Zalo OA gateway timeout; reconciliation required.")
        age = (now - int(payload.parameters["last_user_interaction_ts"])) if (now is not None and "last_user_interaction_ts" in payload.parameters) else int(payload.parameters.get("interaction_age_seconds", 0))
        if age < 0 or age > ZALO_INTERACTION_WINDOW_SECONDS:
            return ConnectorResult(False, self.connector_id, "failed", {}, f"Zalo OA 48h window exceeded ({age}s).")
        rec = {
            "idempotency_key": idempotency_key, "recipient": payload.recipient, "content": payload.content,
            "vietqr_emvco": payload.parameters.get("vietqr_emvco", ""), "vietqr_quicklink": payload.parameters.get("vietqr_quicklink", ""),
            "amount_vnd": payload.parameters.get("amount_vnd", 0),
        }
        self.dispatched[idempotency_key] = rec
        return ConnectorResult(True, self.connector_id, "completed", {"deduplicated": False, "record": rec})


class PilotAWorkflow:
    """End-to-end Pilot A coordinator (Zalo OA → Consent/Quarantine/Quota → Quote + VietQR → Approval → Draft)."""

    def __init__(
        self, db_path: str | Path | None, profile: BusinessProfile, pack_manifest_path: str | Path | None = None,
        zalo_connector: ConnectorProtocol | ZaloSandboxConnector | ZaloOAConnector | None = None, *,
        approval_secret: str | bytes | None = None, enforce_consent: bool = False,
        privacy_guard: PilotPrivacyGuard | None = None, tenant_id: str = "default",
        tenant_db_dir: str | Path | None = None, sme_tier: str = "pilot_a",
        workflow_quota_limit: int | None = None, require_webhook_mac: bool | None = None,
    ) -> None:
        manifest = load_pack_manifest(pack_manifest_path or (Path(__file__).resolve().parent / "packs" / "client-proposal-followup" / "pack.json"))
        self.profile, self.tenant_id, self.enforce_consent, self.sme_tier = profile, tenant_id, enforce_consent, sme_tier
        self.workflow_quota_limit = workflow_quota_limit
        db_p = resolve_tenant_db_path(tenant_db_dir, tenant_id, active_tenant_id=tenant_id) if tenant_db_dir is not None else Path(db_path or ".mekong/opc_state.db")
        if tenant_db_dir is None:
            resolve_tenant_db_path(db_p.parent, tenant_id, active_tenant_id=tenant_id)
        self.state, self.usage = StateStore(db_p), UsageLedger(db_p)
        self.zalo_connector: Any = zalo_connector or ZaloSandboxConnector()
        self.require_webhook_mac = isinstance(self.zalo_connector, ZaloOAConnector) if require_webhook_mac is None else require_webhook_mac
        conn_id = getattr(self.zalo_connector, "connector_id", "zalo_oa_sandbox")
        self.connector_id = conn_id if conn_id in manifest.connectors else "zalo_oa_sandbox"
        conns: dict[str, Any] = {"mock_followup_draft": MockConnector(), "zalo_oa_sandbox": ZaloSandboxConnector(), self.connector_id: self.zalo_connector}
        self.engine = OPCEngine(manifest, self.state, self.usage, connectors=conns, approval_secret=approval_secret)
        self.quarantine = QuarantineFloor()
        self.vietqr = VietQrEngine(db_path=db_p.parent / f"{db_p.stem}_vietqr.db")
        self.privacy_guard = privacy_guard or PilotPrivacyGuard(db_p.parent / f"{db_p.stem}_privacy.db", opc_db_path=db_p)

    def handle_webhook(
        self, event: ZaloWebhookEvent, *, webhook_mac: str | None = None,
        oa_secret_key: str | None = None, app_id: str = "", raw_webhook_data: str | bytes = "",
    ) -> ApprovalCard:
        eff_secret = oa_secret_key if oa_secret_key is not None else os.getenv("ZALO_OA_SECRET_KEY", "")
        if (self.require_webhook_mac or oa_secret_key is not None or webhook_mac is not None) and not verify_zalo_webhook_mac(app_id, raw_webhook_data, event.timestamp, eff_secret, webhook_mac or ""):
            raise ZaloWebhookMacError("Zalo OA webhook MAC verification failed (fail-closed).")
        if self.enforce_consent:
            self.privacy_guard.require_consent(event.sender_id)
        age = event.timestamp - event.last_user_interaction_ts
        if age < 0 or age > ZALO_INTERACTION_WINDOW_SECONDS:
            raise ZaloInteractionWindowError(f"Zalo OA interaction window expired for '{event.sender_id}' (age={age}s).")
        q_msg = self.quarantine.inspect(event.message_text, source=f"zalo:{event.event_id}")
        self.quarantine.enforce_before_tool(q_msg)
        redacted = redact_vietnamese_pii(event.message_text)
        intake = ProposalInput(
            event.event_id, event.sender_name, f"zalo:{event.sender_id}", event.project_title,
            event.requested_services, event.estimated_hours, event.currency, event.language, redacted.redacted_text,
        )
        self.quarantine.enforce_before_tool(self.quarantine.guard_proposal_input(intake))
        period_ym = datetime.fromtimestamp(event.timestamp, tz=timezone.utc).strftime("%Y-%m")
        q_res = self.usage.reserve_workflow_quota(self.tenant_id, event.event_id, period_ym, event.timestamp, self.workflow_quota_limit, self.sme_tier)
        if not q_res.allowed:
            raise WorkflowQuotaExceededError(f"Tenant '{self.tenant_id}' exceeded {q_res.limit_count} workflows for {period_ym}.")
        try:
            run_id, draft, base_payload = self.engine.generate_draft(self.profile, intake)
            amount_vnd = int(verify_confidence_and_math(draft.line_items, draft.total_amount, confidence=event.extraction_confidence))
        except Exception:
            self.usage.quota_guard.release_workflow_slot(self.tenant_id, event.event_id, period_ym)
            raise
        qr = self.vietqr.generate_qr(str(self.profile.preferences.get("bank_id", "MB")).upper(), str(self.profile.preferences.get("account_no", "0988889999")), self.profile.business_name, amount_vnd, f"OPC {run_id}")
        payload = replace(
            base_payload, connector=self.connector_id, content=f"[BẢN NHÁP BÁO GIÁ] {draft.project_title} - Tổng cộng: {amount_vnd:,} VND",
            parameters={**base_payload.parameters, "amount_vnd": amount_vnd, "tenant_id": self.tenant_id, "vietqr_emvco": qr["emvco_payload"], "vietqr_quicklink": qr["quicklink_url"], "interaction_age_seconds": age, "last_user_interaction_ts": event.last_user_interaction_ts},
        )
        token = self.engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.APPROVE)
        self.state.save_run(run_id, self.engine.manifest.pack_id, WorkflowStatus.PENDING_APPROVAL, {"business_name": self.profile.business_name, "owner_name": self.profile.owner_name}, {"request_id": intake.request_id, "client_name": intake.client_name, "sender_id": event.sender_id}, int(time.time()), {"total_amount": draft.total_amount, "line_items": list(draft.line_items)}, payload.__dict__)
        self.state.save_approval(token)
        card_vi = f"[PHIẾU PHÊ DUYỆT BÁO GIÁ - PILOT A]\nMã phiên: {run_id} | Khách: {event.sender_name}\nDự án: {event.project_title} | Tổng: {amount_vnd:,} {event.currency}\nVietQR: {qr['emvco_payload'][:32]}... | HMAC: {token.signature[:16]}..."
        return ApprovalCard(run_id, event.event_id, event.sender_name, intake.client_contact, event.project_title, amount_vnd, event.currency, qr["emvco_payload"], qr["quicklink_url"], token, payload, q_msg, card_vi, redacted.redacted_text, draft.line_items)

    def approve_and_send(self, card: ApprovalCard, token: ApprovalToken | None = None, idempotency_key: str | None = None, *, now: int | None = None) -> dict[str, Any]:
        last_ts, intake_age = int(card.action_payload.parameters.get("last_user_interaction_ts", 0)), int(card.action_payload.parameters.get("interaction_age_seconds", 0))
        window_age = (now - last_ts) if now is not None else (int(time.time()) - card.approval_token.created_at + intake_age)
        if window_age < 0 or window_age > ZALO_INTERACTION_WINDOW_SECONDS:
            raise ZaloInteractionWindowError(f"Zalo OA interaction window expired at dispatch (age={window_age}s).")
        res = self.engine.execute_approved_action(token or card.approval_token, card.action_payload, idempotency_key=idempotency_key or f"pilot_a_{card.run_id}", now=now)
        if (st := _RUN_STATUS_MAP.get(res.get("status", ""))) and (existing := self.state.get_run(card.run_id)):
            self.state.save_run(card.run_id, existing["pack_id"], st, existing["business_profile"], existing["proposal_input"], int(now or time.time()), existing.get("proposal_draft"), existing.get("action_payload"))
        return res

    def reconcile_payment_and_export_draft(self, card: ApprovalCard, raw_webhook: bytes, signature: str, secret: str, vat_rate_pct: int = 8, target_provider: str = "misa_meinvoice") -> tuple[dict[str, Any], AccountingDraftExport]:
        recon = reconcile_signed_vietqr_webhook(self.vietqr, raw_webhook, signature, secret, card.run_id, card.total_amount_vnd)
        return recon, build_accounting_draft_export(card.run_id, card.client_name, card.line_items, card.total_amount_vnd, vat_rate_pct, target_provider, recon["bank_tx_id"])
