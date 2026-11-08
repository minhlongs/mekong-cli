"""Pilot A End-to-End Vertical Slice: Zalo OA Intake → Quarantine → Deterministic Quote + VietQR → Approval Card."""
from __future__ import annotations

import time
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

from src.core.vietqr_engine import VietQrEngine
from src.opc.connectors.base import ConnectorResult
from src.opc.connectors.mock import MockConnector
from src.opc.engine import OPCEngine
from src.opc.manifest import load_pack_manifest
from src.opc.models import (
    ActionPayload,
    ApprovalDecision,
    ApprovalToken,
    BusinessProfile,
    ProposalInput,
    WorkflowStatus,
)
from src.opc.quarantine import QuarantinedInput, QuarantineFloor
from src.opc.state import StateStore
from src.opc.usage import UsageLedger

ZALO_INTERACTION_WINDOW_SECONDS: Final[int] = 48 * 3600


class ZaloInteractionWindowError(PermissionError):
    """Raised when a Zalo OA message is outside the 48-hour customer service window."""


@dataclass(frozen=True)
class ZaloWebhookEvent:
    """Incoming customer inquiry from a Zalo Official Account webhook."""
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


@dataclass(frozen=True)
class ApprovalCard:
    """One-tap Vietnamese owner approval card binding quote, VietQR, and HMAC token."""
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


class ZaloSandboxConnector:
    """Offline Zalo OA sandbox connector enforcing the 48h window and idempotency."""

    def __init__(self, connector_id: str = "zalo_oa_sandbox", simulate_uncertain: bool = False) -> None:
        self.connector_id = connector_id
        self.simulate_uncertain = simulate_uncertain
        self.dispatched: dict[str, dict[str, Any]] = {}

    def dispatch(self, idempotency_key: str, payload: ActionPayload, *, now: int | None = None) -> ConnectorResult:
        """Dispatch approved proposal + VietQR message to Zalo OA sandbox idempotently."""
        if idempotency_key in self.dispatched:
            return ConnectorResult(True, self.connector_id, "completed", {"deduplicated": True, "record": self.dispatched[idempotency_key]})
        if self.simulate_uncertain:
            return ConnectorResult(False, self.connector_id, "uncertain_reconciliation_required", {}, "Zalo OA gateway timeout; reconciliation required.")
        window_age = int(payload.parameters.get("interaction_age_seconds", 0))
        if now is not None and "last_user_interaction_ts" in payload.parameters:
            window_age = now - int(payload.parameters["last_user_interaction_ts"])
        if window_age < 0 or window_age > ZALO_INTERACTION_WINDOW_SECONDS:
            return ConnectorResult(False, self.connector_id, "failed", {}, f"Zalo OA 48h window exceeded ({window_age}s).")
        record = {
            "idempotency_key": idempotency_key, "recipient": payload.recipient, "content": payload.content,
            "vietqr_emvco": payload.parameters.get("vietqr_emvco", ""),
            "vietqr_quicklink": payload.parameters.get("vietqr_quicklink", ""),
            "amount_vnd": payload.parameters.get("amount_vnd", 0),
        }
        self.dispatched[idempotency_key] = record
        return ConnectorResult(True, self.connector_id, "completed", {"deduplicated": False, "record": record})


class PilotAWorkflow:
    """End-to-end Pilot A coordinator (Zalo OA → Quarantine → Quote + VietQR → Approval → Dispatch)."""

    def __init__(
        self, db_path: str | Path, profile: BusinessProfile,
        pack_manifest_path: str | Path | None = None, zalo_connector: ZaloSandboxConnector | None = None,
    ) -> None:
        default_pack = Path(__file__).resolve().parent / "packs" / "client-proposal-followup" / "pack.json"
        manifest = load_pack_manifest(pack_manifest_path or default_pack)
        self.profile = profile
        self.state = StateStore(db_path)
        self.usage = UsageLedger(db_path)
        self.zalo_connector = zalo_connector or ZaloSandboxConnector()
        self.engine = OPCEngine(
            manifest, self.state, self.usage,
            connectors={"mock_followup_draft": MockConnector(), "zalo_oa_sandbox": self.zalo_connector},
        )
        self.quarantine = QuarantineFloor()
        self.vietqr = VietQrEngine(db_path=Path(db_path).with_name("pilot_a_vietqr.db"))

    def handle_webhook(self, event: ZaloWebhookEvent) -> ApprovalCard:
        """Validate 48h window & quarantine, compute deterministic quote + VietQR, and issue ApprovalCard."""
        age = event.timestamp - event.last_user_interaction_ts
        if age < 0 or age > ZALO_INTERACTION_WINDOW_SECONDS:
            raise ZaloInteractionWindowError(f"Zalo OA interaction window expired for '{event.sender_id}' (age={age}s).")
        q_msg = self.quarantine.inspect(event.message_text, source=f"zalo:{event.event_id}")
        self.quarantine.enforce_before_tool(q_msg)

        intake = ProposalInput(
            request_id=event.event_id, client_name=event.sender_name, client_contact=f"zalo:{event.sender_id}",
            project_title=event.project_title, requested_services=event.requested_services,
            estimated_hours=event.estimated_hours, currency=event.currency, language=event.language, notes=event.message_text,
        )
        self.quarantine.enforce_before_tool(self.quarantine.guard_proposal_input(intake))

        run_id, draft, base_payload = self.engine.generate_draft(self.profile, intake)
        amount_vnd = int(Decimal(draft.total_amount))
        qr = self.vietqr.generate_qr(
            bank=str(self.profile.preferences.get("bank_id", "MB")).upper(),
            account_number=str(self.profile.preferences.get("account_no", "0988889999")),
            account_name=self.profile.business_name, amount_vnd=amount_vnd, memo=f"OPC {run_id}",
        )
        payload = replace(
            base_payload, connector="zalo_oa_sandbox",
            content=f"[BẢN NHÁP BÁO GIÁ] {draft.project_title} - Tổng cộng: {amount_vnd:,} VND",
            parameters={
                **base_payload.parameters, "amount_vnd": amount_vnd,
                "vietqr_emvco": qr["emvco_payload"], "vietqr_quicklink": qr["quicklink_url"],
                "interaction_age_seconds": age, "last_user_interaction_ts": event.last_user_interaction_ts,
            },
        )
        token = self.engine.approval_engine.issue_token(run_id, payload, decision=ApprovalDecision.APPROVE)
        self.state.save_run(
            run_id=run_id, pack_id=self.engine.manifest.pack_id, status=WorkflowStatus.PENDING_APPROVAL,
            profile_data={"business_name": self.profile.business_name, "owner_name": self.profile.owner_name},
            input_data={"request_id": intake.request_id, "client_name": intake.client_name},
            now=int(time.time()), action_payload_data=payload.__dict__,
        )
        self.state.save_approval(token)
        card_vi = (
            f"[PHIẾU PHÊ DUYỆT BÁO GIÁ - PILOT A]\n"
            f"Mã phiên: {run_id} | Khách hàng: {event.sender_name} (zalo:{event.sender_id})\n"
            f"Dự án: {event.project_title} | Tổng tiền: {amount_vnd:,} {event.currency}\n"
            f"VietQR EMVCo: {qr['emvco_payload'][:32]}... | HMAC: {token.signature[:16]}..."
        )
        return ApprovalCard(
            run_id=run_id, event_id=event.event_id, client_name=event.sender_name,
            client_contact=intake.client_contact, project_title=event.project_title,
            total_amount_vnd=amount_vnd, currency=event.currency, vietqr_emvco=qr["emvco_payload"],
            vietqr_quicklink=qr["quicklink_url"], approval_token=token, action_payload=payload,
            quarantine_report=q_msg, rendered_card_vi=card_vi,
        )

    def approve_and_send(
        self, card: ApprovalCard, token: ApprovalToken | None = None,
        idempotency_key: str | None = None, *, now: int | None = None,
    ) -> dict[str, Any]:
        """Verify HMAC approval token and dispatch quote + VietQR to Zalo OA sandbox."""
        # A card held past the 48h Zalo customer-service window cannot be sent even if its
        # approval token had a longer TTL, because the platform rejects the outbound message.
        last_ts = int(card.action_payload.parameters.get("last_user_interaction_ts", 0))
        if now is not None and (now - last_ts < 0 or now - last_ts > ZALO_INTERACTION_WINDOW_SECONDS):
            raise ZaloInteractionWindowError(f"Zalo OA interaction window expired at dispatch (age={now - last_ts}s).")
        return self.engine.execute_approved_action(
            token or card.approval_token, card.action_payload, idempotency_key=idempotency_key or f"pilot_a_{card.run_id}",
        )
