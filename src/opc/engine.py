"""OPC Proposal Workflow Engine executing Intake → Quote → Approval → Follow-up via Core Runtime."""
from __future__ import annotations

import time
import uuid
from decimal import Decimal
from typing import Any

from src.core.capability import Capability, CapabilityBus, CapabilitySource, InMemoryCapabilityBus
from src.core.governance import Governance
from src.core.runtime_adapter import MekongCoreRuntimeImpl
from src.opc.approval import ApprovalSecurityError, PayloadBoundApprovalEngine
from src.opc.connectors.base import ConnectorProtocol
from src.opc.connectors.mock import MockConnector
from src.opc.models import (
    ActionPayload,
    ApprovalDecision,
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
    """End-to-end orchestrator for OPC business packs integrated with MekongCoreRuntimeImpl."""

    def __init__(
        self,
        pack_manifest: PackManifest,
        state_store: StateStore,
        usage_ledger: UsageLedger,
        connectors: dict[str, ConnectorProtocol] | None = None,
        capability_bus: CapabilityBus | None = None,
    ) -> None:
        self.manifest = pack_manifest
        self.state = state_store
        self.usage = usage_ledger
        self.approval_engine = PayloadBoundApprovalEngine()
        self.connectors: dict[str, ConnectorProtocol] = connectors or {"mock_followup_draft": MockConnector()}
        self.bus = capability_bus or InMemoryCapabilityBus(Governance())
        self.register_pack_capabilities(self.bus)

    def register_pack_capabilities(self, bus: CapabilityBus) -> None:
        """Register declared pack capabilities onto the CapabilityBus."""
        risk = "HIGH" if (self.manifest.approval_required or self.manifest.external_effects) else "LOW"
        for cap_id in self.manifest.capabilities:
            bus.register(
                Capability(
                    id=cap_id,
                    name=f"{self.manifest.pack_id}:{cap_id}",
                    description=f"OPC pack capability {cap_id}",
                    risk_level=risk,
                    source=CapabilitySource.CUSTOM,
                )
            )

    def _assert_manifest_allows(self, capability: str, connector: str | None = None) -> None:
        if capability not in self.manifest.capabilities:
            raise PermissionError(f"Capability '{capability}' not declared in pack '{self.manifest.pack_id}'.")
        if connector is not None and connector not in self.manifest.connectors:
            raise PermissionError(f"Connector '{connector}' not declared in pack '{self.manifest.pack_id}'.")

    def build_followup_draft(self, decision: ApprovalDecision, project_title: str, lang: str = "en", notes: str = "") -> str:
        """Generate decision-specific follow-up draft in EN or VI."""
        if decision == ApprovalDecision.APPROVE:
            return (
                f"[DRAFT - DO NOT AUTO-SEND] Xin chào, báo giá dự án '{project_title}' đã sẵn sàng để gửi."
                if lang == "vi"
                else f"[DRAFT - DO NOT AUTO-SEND] Follow-up: Proposal for '{project_title}' is approved and ready."
            )
        if decision == ApprovalDecision.REVISE:
            return (
                f"[REVISION NEEDED] Cần chỉnh sửa báo giá '{project_title}': {notes}"
                if lang == "vi"
                else f"[REVISION NEEDED] Proposal '{project_title}' requires revision: {notes}"
            )
        return (
            f"[REJECTED - INTERNAL ARCHIVE] Đã từ chối báo giá '{project_title}'."
            if lang == "vi"
            else f"[REJECTED - INTERNAL ARCHIVE] Proposal '{project_title}' was declined by owner."
        )

    def generate_draft(
        self, profile: BusinessProfile, intake: ProposalInput, run_id: str | None = None,
    ) -> tuple[str, ProposalDraft, ActionPayload]:
        """Goal 1: Generate structured proposal draft and payload-bound action."""
        self._assert_manifest_allows("proposal.generate_draft")
        active_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        now = int(time.time())
        line_items: list[dict[str, Any]] = []
        total = Decimal("0")
        missing: list[str] = []
        hours_per_svc = max(1, intake.estimated_hours // max(1, len(intake.requested_services)))
        for svc in intake.requested_services:
            rate = profile.services.get(svc)
            if rate is None:
                missing.append(f"Unpriced service: '{svc}'")
                line_items.append({"service": svc, "hours": hours_per_svc, "rate": "0.0", "subtotal": "0.0"})
            else:
                sub = rate * Decimal(hours_per_svc)
                total += sub
                line_items.append({"service": svc, "hours": hours_per_svc, "rate": str(rate), "subtotal": str(sub)})

        rendered = (
            f"=== PROPOSAL: {intake.project_title} ===\n"
            f"Client: {intake.client_name} ({intake.client_contact})\n"
            f"Prepared By: {profile.business_name} ({profile.owner_name})\n"
            f"Currency: {profile.currency} | Total: {total} | Terms: {profile.payment_terms}\n"
            + "\n".join(f" - {it['service']}: {it['hours']}h @ {it['rate']} = {it['subtotal']}" for it in line_items)
        )
        draft = ProposalDraft(
            run_id=active_run_id, pack_id=self.manifest.pack_id, client_name=intake.client_name,
            project_title=intake.project_title, currency=profile.currency, line_items=tuple(line_items),
            total_amount=str(total), missing_fields=tuple(missing), rendered_proposal=rendered,
        )
        action_payload = ActionPayload(
            principal=profile.owner_name, capability="followup.create_draft", connector="mock_followup_draft",
            recipient=intake.client_contact, content=f"Draft proposal for {intake.project_title} is ready for review.",
            parameters={"project_title": intake.project_title, "amount": str(total), "language": intake.language},
            attachments=intake.attachments, budget_amount="0.00", budget_currency=profile.currency,
            expires_at=now + 86400,
        )
        self.state.save_run(
            run_id=active_run_id, pack_id=self.manifest.pack_id, status=WorkflowStatus.PENDING_APPROVAL,
            profile_data={"business_name": profile.business_name, "owner_name": profile.owner_name, "currency": profile.currency, "language": profile.language},
            input_data={"request_id": intake.request_id, "client_name": intake.client_name, "project_title": intake.project_title, "language": intake.language},
            draft_data={"total_amount": str(total), "rendered": rendered, "missing_fields": missing},
            action_payload_data=action_payload.__dict__, now=now,
        )
        self.usage.record_usage(
            UsageRecord(
                event_id=f"use_{uuid.uuid4().hex[:12]}", run_id=active_run_id, attempt=1, stage=UsageStage.ACTUAL,
                provider="deterministic_engine", model="offline_rules", tokens=len(rendered.split()),
                tool_fee="0.00", amount="0.00", currency=profile.currency, payer="owner",
                pricing_source="local_offline", created_at=now,
            )
        )
        return active_run_id, draft, action_payload

    def execute_approved_action(
        self, token: ApprovalToken, payload: ActionPayload, idempotency_key: str, hard_budget_limit: str | None = None,
    ) -> dict[str, Any]:
        """Goal 2: Verify approval, reserve budget, and dispatch external connector effect."""
        now = int(time.time())
        self._assert_manifest_allows(payload.capability, payload.connector)
        self.approval_engine.verify_and_consume(token, payload, now=now)
        if self.state.get_approval(token.token_id) is not None:
            if not self.state.consume_approval_atomic(token.token_id, token.action_digest, now):
                raise ApprovalSecurityError(f"Atomic SQLite approval lock failed for token '{token.token_id}'.")
        else:
            self.state.save_approval(token)

        connector = self.connectors.get(payload.connector)
        if not connector:
            raise ValueError(f"Unknown connector: '{payload.connector}'")
        if not self.state.record_action_attempt(idempotency_key, token.run_id, payload.capability, payload.connector, payload, now):
            return {"status": "deduplicated", "message": "Action already dispatched previously."}
        if not self.usage.reserve_budget(f"res_{idempotency_key}", token.run_id, payload.budget_amount, payload.budget_currency, "owner", now, hard_budget_limit):
            self.state.mark_action_result(idempotency_key, "budget_exceeded", None, "Hard budget ceiling exceeded.", now)
            return {"status": "budget_exceeded", "error": "Hard budget ceiling exceeded."}

        res = connector.dispatch(idempotency_key, payload)
        lang = str(payload.parameters.get("language", "en"))
        title = str(payload.parameters.get("project_title", "Project"))
        followup = self.build_followup_draft(ApprovalDecision.APPROVE, title, lang)
        if res.status == "uncertain_reconciliation_required":
            self.state.mark_action_result(idempotency_key, "uncertain", res.response_data, res.error_message, now)
            return {"status": "reconciliation_required", "error": res.error_message}
        if not res.success:
            self.state.mark_action_result(idempotency_key, "failed", res.response_data, res.error_message, now)
            return {"status": "failed", "error": res.error_message}
        self.state.mark_action_result(idempotency_key, "completed", res.response_data, None, now)
        return {"status": "completed", "result": res.response_data, "followup_draft": followup}

    def run_via_core_runtime(self, runtime: MekongCoreRuntimeImpl, goal_text: str) -> Any:
        """Execute an OPC goal through MekongCoreRuntimeImpl lifecycle."""
        return runtime.run(goal_text)
