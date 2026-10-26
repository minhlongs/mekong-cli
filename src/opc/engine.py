"""OPC Proposal Workflow Engine executing Intake → Quote → Approval → Follow-up."""
from __future__ import annotations

import time
import uuid
from decimal import Decimal
from typing import Any

from src.opc.approval import PayloadBoundApprovalEngine
from src.opc.connectors.base import ConnectorProtocol
from src.opc.connectors.mock import MockConnector
from src.opc.models import (
    ActionPayload,
    ApprovalToken,
    BusinessProfile,
    PackManifest,
    ProposalDraft,
    ProposalInput,
    UsageRecord,
    UsageStage,
    WorkflowStatus,
)
from src.opc.state import StateStore
from src.opc.usage import UsageLedger


class OPCEngine:
    """End-to-end orchestrator for OPC business packs."""

    def __init__(
        self,
        pack_manifest: PackManifest,
        state_store: StateStore,
        usage_ledger: UsageLedger,
        connectors: dict[str, ConnectorProtocol] | None = None,
    ) -> None:
        self.manifest = pack_manifest
        self.state = state_store
        self.usage = usage_ledger
        self.approval_engine = PayloadBoundApprovalEngine()
        self.connectors: dict[str, ConnectorProtocol] = connectors or {
            "mock_followup_draft": MockConnector(),
        }

    def generate_draft(
        self,
        profile: BusinessProfile,
        intake: ProposalInput,
        run_id: str | None = None,
    ) -> tuple[str, ProposalDraft, ActionPayload]:
        """Stage 1: Generate structured proposal draft and payload-bound action."""
        active_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        now = int(time.time())

        line_items: list[dict[str, Any]] = []
        total = Decimal("0")
        missing_fields: list[str] = []

        hours_per_svc = max(1, intake.estimated_hours // max(1, len(intake.requested_services)))
        for svc in intake.requested_services:
            rate = profile.services.get(svc)
            if rate is None:
                missing_fields.append(f"Unpriced service: '{svc}'")
                line_items.append({"service": svc, "hours": hours_per_svc, "rate": "0.0", "subtotal": "0.0"})
            else:
                sub = rate * Decimal(hours_per_svc)
                total += sub
                line_items.append({"service": svc, "hours": hours_per_svc, "rate": str(rate), "subtotal": str(sub)})

        rendered = (
            f"=== PROPOSAL: {intake.project_title} ===\n"
            f"Client: {intake.client_name} ({intake.client_contact})\n"
            f"Prepared By: {profile.business_name} ({profile.owner_name})\n"
            f"Currency: {profile.currency} | Total: {total}\n"
            f"Terms: {profile.payment_terms}\n"
            f"Line Items:\n" + "\n".join(f" - {it['service']}: {it['hours']}h @ {it['rate']} = {it['subtotal']}" for it in line_items)
        )

        draft = ProposalDraft(
            run_id=active_run_id,
            pack_id=self.manifest.pack_id,
            client_name=intake.client_name,
            project_title=intake.project_title,
            currency=profile.currency,
            line_items=tuple(line_items),
            total_amount=str(total),
            missing_fields=tuple(missing_fields),
            rendered_proposal=rendered,
            is_draft=True,
            is_sample_data=True,
        )

        action_payload = ActionPayload(
            principal=profile.owner_name,
            capability="followup.create_draft",
            connector="mock_followup_draft",
            recipient=intake.client_contact,
            content=f"Draft proposal for {intake.project_title} is ready for review.",
            parameters={"project_title": intake.project_title, "amount": str(total)},
            attachments=intake.attachments,
            budget_amount="0.00",
            budget_currency=profile.currency,
            expires_at=now + 86400,
        )

        self.state.save_run(
            run_id=active_run_id,
            pack_id=self.manifest.pack_id,
            status=WorkflowStatus.PENDING_APPROVAL,
            profile_data={"business_name": profile.business_name, "owner_name": profile.owner_name},
            input_data={"request_id": intake.request_id, "client_name": intake.client_name},
            draft_data={"total_amount": str(total), "rendered": rendered},
            now=now,
        )

        self.usage.record_usage(
            UsageRecord(
                event_id=f"use_{uuid.uuid4().hex[:12]}",
                run_id=active_run_id,
                attempt=1,
                stage=UsageStage.ACTUAL,
                provider="deterministic_engine",
                model="offline_rules",
                tokens=len(rendered.split()),
                tool_fee="0.00",
                amount="0.00",
                currency=profile.currency,
                payer="owner",
                pricing_source="local_offline",
                created_at=now,
            )
        )

        return active_run_id, draft, action_payload

    def execute_approved_action(
        self,
        token: ApprovalToken,
        payload: ActionPayload,
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Stage 2: Verify approval and dispatch external connector effect."""
        now = int(time.time())

        # Validate token and payload binding
        self.approval_engine.verify_and_consume(token, payload, now=now)
        self.state.save_approval(token)

        connector = self.connectors.get(payload.connector)
        if not connector:
            raise ValueError(f"Unknown connector: '{payload.connector}'")

        if not self.state.record_action_attempt(
            idempotency_key=idempotency_key,
            run_id=token.run_id,
            capability=payload.capability,
            connector=payload.connector,
            payload=payload,
            now=now,
        ):
            return {"status": "deduplicated", "message": "Action already dispatched previously."}

        res = connector.dispatch(idempotency_key, payload)

        if res.status == "uncertain_reconciliation_required":
            self.state.mark_action_result(idempotency_key, "uncertain", res.response_data, res.error_message, now)
            return {"status": "reconciliation_required", "error": res.error_message}

        if not res.success:
            self.state.mark_action_result(idempotency_key, "failed", res.response_data, res.error_message, now)
            return {"status": "failed", "error": res.error_message}

        self.state.mark_action_result(idempotency_key, "completed", res.response_data, None, now)
        return {"status": "completed", "result": res.response_data}
