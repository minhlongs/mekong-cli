# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Sophia Integration Contract v1.0 (`mekong.sophia.execution_contract.v1`).

Defines the authoritative cross-system execution contract between Sophia AI Factory
(executive supervisor, approval authority, business KPI evaluator) and Mekong CLI
(durable ticket runtime, isolated worktree executor, deterministic verifier,
SHA-256 artifact producer, and transactional outbox reporter).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

from src.core.buzz_adapter import (
    BuzzAdapter,
    BuzzSecurityError,
    WebhookAuthorityPolicy,
    validate_callback_destination,
)
from src.mekongcli.core.goal_engine.models import (
    ExecutionTruthStatus,
    GoalStatus,
    TaskStatus,
)
from src.mekongcli.core.goal_engine.service import GoalEngine
from src.mekongcli.core.goal_engine.store import SQLiteGoalStore
from src.mekongcli.core.goal_engine.worktree_manager import WorktreeIsolationManager

CONTRACT_VERSION = "mekong.sophia.execution_contract.v1"

SOPHIA_CONTRACT_OPERATIONS: tuple[str, ...] = (
    "submit_task",
    "get_ticket",
    "get_status",
    "get_verification_evidence",
    "get_artifacts",
    "request_cancel",
    "report_approval_required",
    "resume_reconcile",
    "list_durable_reports",
    "get_cost_usage",
)

ExecutionOutcome = Literal[
    "PLANNED",
    "RUNNING",
    "SIMULATED",
    "EXECUTED",
    "EXECUTION_FAILED",
    "CANCELLED",
    "UNAVAILABLE",
]
VerificationOutcome = Literal[
    "UNVERIFIED",
    "VERIFIED_SUCCESS",
    "VERIFICATION_FAILED",
    "WAITING_APPROVAL",
    "NOT_RUN",
]
DeliveryOutcome = Literal[
    "NOT_REQUESTED",
    "PENDING",
    "SENT",
    "FAILED_RETRYABLE",
    "DEAD_LETTER",
]
BusinessOutcome = Literal[
    "NOT_EVALUATED",
    "KPI_PENDING",
    "KPI_ATTRIBUTED",
    "REQUIRES_EXTERNAL_ORACLE",
]

_VALID_EXECUTION_OUTCOMES = frozenset({
    "PLANNED",
    "RUNNING",
    "SIMULATED",
    "EXECUTED",
    "EXECUTION_FAILED",
    "CANCELLED",
    "UNAVAILABLE",
})
_VALID_VERIFICATION_OUTCOMES = frozenset({
    "UNVERIFIED",
    "VERIFIED_SUCCESS",
    "VERIFICATION_FAILED",
    "WAITING_APPROVAL",
    "NOT_RUN",
})
_VALID_DELIVERY_OUTCOMES = frozenset({
    "NOT_REQUESTED",
    "PENDING",
    "SENT",
    "FAILED_RETRYABLE",
    "DEAD_LETTER",
})
_VALID_BUSINESS_OUTCOMES = frozenset({
    "NOT_EVALUATED",
    "KPI_PENDING",
    "KPI_ATTRIBUTED",
    "REQUIRES_EXTERNAL_ORACLE",
})


class SophiaContractValidationError(ValueError):
    """Raised when a Sophia handoff payload or envelope violates v1 contract invariants."""


@dataclass(frozen=True)
class SophiaTaskSubmissionRequest:
    """Validated inbound task submission request from Sophia AI Factory."""

    source_id: str
    event_id: str
    goal: str
    requester: str = "sophia_orchestrator"
    workspace_id: str = "default"
    thread_id: str = "default"
    authorized_scope: str = "workspace"
    requested_capabilities: tuple[str, ...] = ("goal_execute",)
    resource_boundaries: tuple[str, ...] = (".",)
    verification_profile: str = "standard"
    cost_budget: float = 10.0
    retry_budget: int = 3
    isolate_worktree: bool = True
    require_verified: bool = True
    execute_immediately: bool = False
    simulated_run: bool = False
    callback_url: str | None = None
    commands_by_role: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    contract_version: str = CONTRACT_VERSION

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SophiaTaskSubmissionRequest":
        if not isinstance(data, dict):
            raise SophiaContractValidationError("Submission request must be a dict")
        version = str(data.get("contract_version") or CONTRACT_VERSION)
        if version != CONTRACT_VERSION:
            raise SophiaContractValidationError(
                f"Unsupported contract_version {version!r}; expected {CONTRACT_VERSION!r}"
            )
        source_id = str(data.get("source_id") or "").strip()
        event_id = str(data.get("event_id") or "").strip()
        goal = str(data.get("goal") or data.get("text") or "").strip()
        if not source_id:
            raise SophiaContractValidationError("Missing required field 'source_id'")
        if not event_id:
            raise SophiaContractValidationError("Missing required field 'event_id'")
        if not goal:
            raise SophiaContractValidationError("Missing required field 'goal'")

        raw_caps = data.get("requested_capabilities") or data.get("permitted_capabilities") or ("goal_execute",)
        if not isinstance(raw_caps, (list, tuple)) or not raw_caps:
            raise SophiaContractValidationError("requested_capabilities must be a non-empty list")
        raw_bounds = data.get("resource_boundaries") or (".",)
        if not isinstance(raw_bounds, (list, tuple)) or not raw_bounds:
            raise SophiaContractValidationError("resource_boundaries must be a non-empty list")

        return cls(
            source_id=source_id,
            event_id=event_id,
            goal=goal,
            requester=str(data.get("requester") or "sophia_orchestrator").strip(),
            workspace_id=str(data.get("workspace_id") or "default").strip(),
            thread_id=str(data.get("thread_id") or event_id).strip(),
            authorized_scope=str(data.get("authorized_scope") or "workspace").strip(),
            requested_capabilities=tuple(str(c) for c in raw_caps),
            resource_boundaries=tuple(str(b) for b in raw_bounds),
            verification_profile=str(
                data.get("verification_profile")
                or data.get("verification_requirements")
                or "standard"
            ).strip(),
            cost_budget=float(data.get("cost_budget", 10.0)),
            retry_budget=int(data.get("retry_budget", 3)),
            isolate_worktree=bool(data.get("isolate_worktree", True)),
            require_verified=bool(data.get("require_verified", True)),
            execute_immediately=bool(data.get("execute_immediately", False)),
            simulated_run=bool(data.get("simulated_run", False)),
            callback_url=data.get("callback_url"),
            commands_by_role=dict(data.get("commands_by_role") or {}),
            metadata=dict(data.get("metadata") or {}),
            contract_version=version,
        )


@dataclass(frozen=True)
class SophiaTicketAssignment:
    """Server-assigned durable ticket and mandate descriptor."""

    ticket_id: str
    goal_id: str
    source_id: str
    event_id: str
    thread_id: str
    deduplicated: bool
    mandate_version: int
    policy_version: str
    accepted_at: str
    mandate_hash: str
    truth_status: str
    permitted_capabilities: tuple[str, ...]
    resource_boundaries: tuple[str, ...]
    risk_classification: str
    cost_budget: float
    retry_budget: int
    verification_requirements: str
    contract_version: str = CONTRACT_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "ticket_id": self.ticket_id,
            "goal_id": self.goal_id,
            "source_id": self.source_id,
            "event_id": self.event_id,
            "thread_id": self.thread_id,
            "deduplicated": self.deduplicated,
            "mandate_version": self.mandate_version,
            "policy_version": self.policy_version,
            "accepted_at": self.accepted_at,
            "mandate_hash": self.mandate_hash,
            "truth_status": self.truth_status,
            "permitted_capabilities": list(self.permitted_capabilities),
            "resource_boundaries": list(self.resource_boundaries),
            "risk_classification": self.risk_classification,
            "cost_budget": self.cost_budget,
            "retry_budget": self.retry_budget,
            "verification_requirements": self.verification_requirements,
        }


@dataclass(frozen=True)
class SophiaOutcomeEnvelope:
    """Four-axis outcome envelope separating execution, verification, delivery, and business truth."""

    ticket_id: str
    goal_id: str
    truth_status: str
    simulated: bool
    execution_outcome: ExecutionOutcome
    verification_outcome: VerificationOutcome
    delivery_outcome: DeliveryOutcome
    business_outcome: BusinessOutcome = "NOT_EVALUATED"
    verified_success_claim_permitted: bool = False
    contract_version: str = CONTRACT_VERSION

    def __post_init__(self) -> None:
        if self.execution_outcome not in _VALID_EXECUTION_OUTCOMES:
            raise SophiaContractValidationError(
                f"Invalid execution_outcome: {self.execution_outcome!r}"
            )
        if self.verification_outcome not in _VALID_VERIFICATION_OUTCOMES:
            raise SophiaContractValidationError(
                f"Invalid verification_outcome: {self.verification_outcome!r}"
            )
        if self.delivery_outcome not in _VALID_DELIVERY_OUTCOMES:
            raise SophiaContractValidationError(
                f"Invalid delivery_outcome: {self.delivery_outcome!r}"
            )
        if self.business_outcome not in _VALID_BUSINESS_OUTCOMES:
            raise SophiaContractValidationError(
                f"Invalid business_outcome: {self.business_outcome!r}"
            )
        expected_claim = (
            self.truth_status == ExecutionTruthStatus.VERIFIED_SUCCESS.value
            and self.execution_outcome == "EXECUTED"
            and self.verification_outcome == "VERIFIED_SUCCESS"
            and not self.simulated
        )
        if self.verified_success_claim_permitted and not expected_claim:
            raise SophiaContractValidationError(
                "verified_success_claim_permitted=True is forbidden unless "
                "truth_status=='VERIFIED_SUCCESS', execution_outcome=='EXECUTED', "
                "verification_outcome=='VERIFIED_SUCCESS', and simulated==False"
            )
        object.__setattr__(self, "verified_success_claim_permitted", expected_claim)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "ticket_id": self.ticket_id,
            "goal_id": self.goal_id,
            "truth_status": self.truth_status,
            "simulated": self.simulated,
            "execution_outcome": self.execution_outcome,
            "verification_outcome": self.verification_outcome,
            "delivery_outcome": self.delivery_outcome,
            "business_outcome": self.business_outcome,
            "verified_success_claim_permitted": self.verified_success_claim_permitted,
        }


def validate_sophia_handoff_fixture(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate a Sophia handoff envelope or submission fixture against v1 invariants."""
    if not isinstance(payload, dict):
        raise SophiaContractValidationError("Handoff fixture must be a dictionary")
    version = payload.get("contract_version")
    if version != CONTRACT_VERSION:
        raise SophiaContractValidationError(
            f"Invalid contract_version {version!r}; expected {CONTRACT_VERSION!r}"
        )

    if "execution_outcome" in payload or "verification_outcome" in payload:
        envelope = SophiaOutcomeEnvelope(
            ticket_id=str(payload.get("ticket_id") or ""),
            goal_id=str(payload.get("goal_id") or ""),
            truth_status=str(payload.get("truth_status") or ExecutionTruthStatus.UNAVAILABLE.value),
            simulated=bool(payload.get("simulated", False)),
            execution_outcome=payload.get("execution_outcome", "UNAVAILABLE"),
            verification_outcome=payload.get("verification_outcome", "UNVERIFIED"),
            delivery_outcome=payload.get("delivery_outcome", "NOT_REQUESTED"),
            business_outcome=payload.get("business_outcome", "NOT_EVALUATED"),
            verified_success_claim_permitted=bool(
                payload.get("verified_success_claim_permitted", False)
            ),
            contract_version=version,
        )
        if not envelope.ticket_id or not envelope.goal_id:
            raise SophiaContractValidationError(
                "Outcome envelope requires non-empty 'ticket_id' and 'goal_id'"
            )
        return envelope.to_dict()

    req = SophiaTaskSubmissionRequest.from_dict(payload)
    if req.callback_url is not None:
        validate_callback_destination(req.callback_url, strict_dns=False)
    return {
        "contract_version": req.contract_version,
        "source_id": req.source_id,
        "event_id": req.event_id,
        "goal": req.goal,
        "requester": req.requester,
        "workspace_id": req.workspace_id,
        "valid": True,
    }


class SophiaExecutionContractV1:
    """Authoritative v1 execution contract facade for Sophia AI Factory integration."""

    CONTRACT_VERSION = CONTRACT_VERSION
    OPERATIONS = SOPHIA_CONTRACT_OPERATIONS

    def __init__(
        self,
        store: SQLiteGoalStore,
        engine: GoalEngine,
        *,
        worktree_manager: WorktreeIsolationManager | None = None,
        authority_policy: WebhookAuthorityPolicy | None = None,
        transport: Any | None = None,
    ) -> None:
        self._store = store
        self._engine = engine
        self._worktree_manager = worktree_manager or getattr(
            engine, "worktree_manager", None
        ) or WorktreeIsolationManager(repo_root=engine.cwd)
        default_policy = authority_policy or WebhookAuthorityPolicy(
            allowed_requesters=("sophia_orchestrator", "sophia", "buzz", "founder"),
        )
        self._buzz = BuzzAdapter(
            outbox_store=store,
            authority_policy=default_policy,
            transport=transport,
        )

    @staticmethod
    def _derive_outcomes(
        truth_status: str,
        *,
        simulated: bool,
        has_verification_run: bool,
        verification_passed: bool | None,
        delivery_status: str | None,
    ) -> tuple[ExecutionOutcome, VerificationOutcome, DeliveryOutcome, BusinessOutcome]:
        if simulated or truth_status == ExecutionTruthStatus.SIMULATED.value:
            exec_out: ExecutionOutcome = "SIMULATED"
        elif truth_status in (
            ExecutionTruthStatus.PLANNED.value,
            ExecutionTruthStatus.QUEUED.value,
        ):
            exec_out = "PLANNED"
        elif truth_status in (
            ExecutionTruthStatus.RUNNING.value,
            ExecutionTruthStatus.RETRY_WAIT.value,
        ):
            exec_out = "RUNNING"
        elif truth_status in (
            ExecutionTruthStatus.VERIFIED_SUCCESS.value,
            ExecutionTruthStatus.VERIFICATION_FAILED.value,
        ):
            exec_out = "EXECUTED"
        elif truth_status == ExecutionTruthStatus.CANCELLED.value:
            exec_out = "CANCELLED"
        elif truth_status in (
            ExecutionTruthStatus.EXECUTION_FAILED.value,
            ExecutionTruthStatus.BLOCKED.value,
            ExecutionTruthStatus.WAITING_APPROVAL.value,
        ):
            exec_out = "EXECUTION_FAILED"
        else:
            exec_out = "UNAVAILABLE"

        if truth_status == ExecutionTruthStatus.WAITING_APPROVAL.value:
            ver_out: VerificationOutcome = "WAITING_APPROVAL"
        elif truth_status == ExecutionTruthStatus.VERIFIED_SUCCESS.value and not simulated:
            ver_out = "VERIFIED_SUCCESS"
        elif truth_status == ExecutionTruthStatus.VERIFICATION_FAILED.value or (
            has_verification_run and verification_passed is False
        ):
            ver_out = "VERIFICATION_FAILED"
        elif has_verification_run and not simulated and verification_passed is True:
            ver_out = "VERIFIED_SUCCESS"
        elif exec_out in ("PLANNED", "RUNNING", "SIMULATED", "CANCELLED"):
            ver_out = "NOT_RUN"
        else:
            ver_out = "UNVERIFIED"

        raw_deliv = (delivery_status or "NOT_REQUESTED").upper()
        deliv_out: DeliveryOutcome = (
            raw_deliv if raw_deliv in _VALID_DELIVERY_OUTCOMES else "NOT_REQUESTED"  # type: ignore[assignment]
        )
        return exec_out, ver_out, deliv_out, "NOT_EVALUATED"

    # ------------------------------------------------------------------ #
    # 1. submit_task
    # ------------------------------------------------------------------ #

    def submit_task(
        self,
        request: dict[str, Any] | SophiaTaskSubmissionRequest,
    ) -> dict[str, Any]:
        """Submit a task from Sophia, enforce authority & SSRF policy, and optionally execute."""
        req = (
            request
            if isinstance(request, SophiaTaskSubmissionRequest)
            else SophiaTaskSubmissionRequest.from_dict(request)
        )
        webhook_payload: dict[str, Any] = {
            "goal": req.goal,
            "source_id": req.source_id,
            "event_id": req.event_id,
            "thread_id": req.thread_id,
            "requester": req.requester,
            "workspace_id": req.workspace_id,
            "authorized_scope": req.authorized_scope,
            "permitted_capabilities": list(req.requested_capabilities),
            "resource_boundaries": list(req.resource_boundaries),
            "verification_requirements": req.verification_profile,
            "cost_budget": req.cost_budget,
            "retry_budget": req.retry_budget,
            "callback_url": req.callback_url,
            "context": req.metadata,
        }
        if isinstance(request, dict):
            for sec_key in (
                "mandate_hash",
                "policy_version",
                "mandate_version",
                "risk_classification",
                "permitted_capabilities",
            ):
                if sec_key in request:
                    webhook_payload[sec_key] = request[sec_key]

        ticket, created = self._buzz.admit_webhook_event(
            webhook_payload,
            source_id=req.source_id,
        )
        if not created:
            status_env = self.get_status(ticket.ticket_id)
            return {
                "contract_version": CONTRACT_VERSION,
                "ticket": self.get_ticket(ticket.ticket_id)["ticket"],
                "deduplicated": True,
                "status": status_env,
            }

        exec_cmds = not req.simulated_run
        if req.commands_by_role or (req.execute_immediately and exec_cmds):
            if "goal_execute" not in ticket.mandate.permitted_capabilities:
                raise BuzzSecurityError(
                    "Ticket mandate lacks 'goal_execute' capability required for command execution"
                )
            if ticket.mandate.authorized_scope == "read_only" and req.commands_by_role:
                raise BuzzSecurityError(
                    "Ticket with 'read_only' authorized_scope cannot bind mutating commands_by_role"
                )

        goal_record = self._engine.create_goal(req.goal)
        tasks = self._store.get_tasks(goal_record.id)
        if req.commands_by_role:
            fallback_check_cmd = req.commands_by_role.get("*", "python3 -m src.main --help")
            for t in tasks:
                if t.role.value in req.commands_by_role:
                    t.command = req.commands_by_role[t.role.value]
                    t.mutates_workspace = True
                else:
                    t.command = fallback_check_cmd
                    t.mutates_workspace = "*" in req.commands_by_role
            self._store.save_tasks(tasks)

        self._store.update_ticket_truth_status(
            ticket.ticket_id,
            ExecutionTruthStatus.PLANNED,
            goal_id=goal_record.id,
        )

        if req.execute_immediately:
            self._store.update_ticket_truth_status(
                ticket.ticket_id,
                ExecutionTruthStatus.RUNNING,
                goal_id=goal_record.id,
            )
            finished_goal = self._engine.run_goal(
                goal_record.id,
                verification_profile=req.verification_profile,
                execute_commands=not req.simulated_run,
                isolate_worktree=req.isolate_worktree,
                ticket_id=ticket.ticket_id,
            )
            final_ts = finished_goal.truth_status.value
            self._store.update_ticket_truth_status(
                ticket.ticket_id,
                final_ts,
                goal_id=goal_record.id,
            )
            if req.callback_url:
                self._buzz.send_update(
                    final_ts,
                    {"ticket_id": ticket.ticket_id, "goal_id": goal_record.id},
                    callback_url=req.callback_url,
                    ticket_id=ticket.ticket_id,
                    source_id=req.source_id,
                    thread_id=req.thread_id,
                )

        return {
            "contract_version": CONTRACT_VERSION,
            "ticket": self.get_ticket(ticket.ticket_id)["ticket"],
            "deduplicated": False,
            "status": self.get_status(ticket.ticket_id),
        }

    # ------------------------------------------------------------------ #
    # 2. get_ticket
    # ------------------------------------------------------------------ #

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        """Retrieve server-assigned ticket and verify mandate HMAC integrity."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        mandate = self._store.verify_mandate_integrity(ticket_id)
        assignment = SophiaTicketAssignment(
            ticket_id=str(row["ticket_id"]),
            goal_id=str(row["goal_id"]),
            source_id=mandate.source_id,
            event_id=mandate.event_id,
            thread_id=str(row.get("thread_id") or "default"),
            deduplicated=False,
            mandate_version=mandate.mandate_version,
            policy_version=mandate.policy_version,
            accepted_at=mandate.accepted_at,
            mandate_hash=mandate.mandate_hash,
            truth_status=str(row["truth_status"]),
            permitted_capabilities=mandate.permitted_capabilities,
            resource_boundaries=mandate.resource_boundaries,
            risk_classification=mandate.risk_classification,
            cost_budget=mandate.cost_budget,
            retry_budget=mandate.retry_budget,
            verification_requirements=mandate.verification_requirements,
        )
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket": assignment.to_dict(),
        }

    # ------------------------------------------------------------------ #
    # 3. get_status
    # ------------------------------------------------------------------ #

    def get_status(self, ticket_id: str) -> dict[str, Any]:
        """Return canonical 4-axis outcome envelope for ``ticket_id``."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        goal_id = str(row["goal_id"])
        goal = self._store.get_goal(goal_id)
        latest_verif = self._store.get_latest_verification(goal_id) if goal else None
        outbox_rows = self._store.list_outbox(ticket_id=ticket_id)
        latest_delivery = outbox_rows[-1]["delivery_status"] if outbox_rows else None

        eff_truth = (
            goal.truth_status.value
            if goal is not None and goal.truth_status != ExecutionTruthStatus.PLANNED
            else str(row["truth_status"])
        )
        tasks = self._store.get_tasks(goal_id) if goal else []
        simulated = (
            eff_truth == ExecutionTruthStatus.SIMULATED.value
            or (bool(tasks) and any(t.truth_status == ExecutionTruthStatus.SIMULATED for t in tasks))
        )

        exec_out, ver_out, deliv_out, biz_out = self._derive_outcomes(
            eff_truth,
            simulated=simulated,
            has_verification_run=(latest_verif is not None),
            verification_passed=(latest_verif.passed if latest_verif is not None else None),
            delivery_status=latest_delivery,
        )
        envelope = SophiaOutcomeEnvelope(
            ticket_id=str(row["ticket_id"]),
            goal_id=goal_id,
            truth_status=eff_truth,
            simulated=simulated,
            execution_outcome=exec_out,
            verification_outcome=ver_out,
            delivery_outcome=deliv_out,
            business_outcome=biz_out,
        )
        return envelope.to_dict()

    # ------------------------------------------------------------------ #
    # 4. get_verification_evidence
    # ------------------------------------------------------------------ #

    def get_verification_evidence(self, ticket_id: str) -> dict[str, Any]:
        """Return deterministic verification evidence and task-level truth states."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        goal_id = str(row["goal_id"])
        latest_verif = self._store.get_latest_verification(goal_id)
        tasks = self._store.get_tasks(goal_id)
        criteria = self._store.get_criteria(goal_id)
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket_id": str(row["ticket_id"]),
            "goal_id": goal_id,
            "truth_status": str(row["truth_status"]),
            "verification_run": (
                {
                    "id": latest_verif.id,
                    "profile": latest_verif.profile,
                    "passed": latest_verif.passed,
                    "results": latest_verif.results,
                    "created_at": latest_verif.created_at,
                }
                if latest_verif is not None
                else None
            ),
            "criteria": [
                {
                    "id": c.id,
                    "description": c.description,
                    "satisfied": c.satisfied,
                    "evidence": c.evidence,
                }
                for c in criteria
            ],
            "tasks": [
                {
                    "task_id": t.id,
                    "role": t.role.value,
                    "status": t.status.value,
                    "truth_status": t.truth_status.value,
                    "exit_code": t.exit_code,
                    "command": t.command,
                }
                for t in tasks
            ],
        }

    # ------------------------------------------------------------------ #
    # 5. get_artifacts
    # ------------------------------------------------------------------ #

    def get_artifacts(self, ticket_id: str) -> dict[str, Any]:
        """Return SHA-256 verified artifact manifests harvested for ``ticket_id``."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        goal_id = str(row["goal_id"])
        manifests = self._worktree_manager.list_artifacts(ticket_id=ticket_id)
        flat_artifacts: list[dict[str, Any]] = []
        for mf in manifests:
            for item in mf.get("artifacts", []):
                flat_artifacts.append(item)
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket_id": ticket_id,
            "goal_id": goal_id,
            "manifest_count": len(manifests),
            "artifact_count": len(flat_artifacts),
            "manifests": manifests,
            "artifacts": flat_artifacts,
        }

    # ------------------------------------------------------------------ #
    # 6. request_cancel
    # ------------------------------------------------------------------ #

    def request_cancel(self, ticket_id: str, reason: str = "cancelled_by_sophia") -> dict[str, Any]:
        """Cancel an active or planned ticket and update both goal and ticket truth_status."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        goal_id = str(row["goal_id"])
        goal = self._store.get_goal(goal_id)
        if goal is not None:
            self._engine.cancel_goal(goal.id)
        self._store.update_ticket_truth_status(
            ticket_id,
            ExecutionTruthStatus.CANCELLED,
        )
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket_id": ticket_id,
            "goal_id": goal_id,
            "cancelled": True,
            "truth_status": ExecutionTruthStatus.CANCELLED.value,
            "reason": reason,
        }

    # ------------------------------------------------------------------ #
    # 7. report_approval_required
    # ------------------------------------------------------------------ #

    def report_approval_required(
        self,
        ticket_id: str,
        *,
        task_id: str | None = None,
        reason: str = "operator_approval_required",
    ) -> dict[str, Any]:
        """Transition ticket and goal to ``WAITING_APPROVAL`` fail-closed checkpoint."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        goal_id = str(row["goal_id"])
        goal = self._store.get_goal(goal_id)
        if goal is not None:
            tasks = self._store.get_tasks(goal.id)
            for t in tasks:
                if task_id is None or t.id == task_id:
                    t.status = TaskStatus.BLOCKED
                    t.truth_status = ExecutionTruthStatus.WAITING_APPROVAL
                    t.blocked_reason = reason
            if tasks:
                self._store.save_tasks(tasks)
            goal.status = GoalStatus.BLOCKED
            goal.truth_status = ExecutionTruthStatus.WAITING_APPROVAL
            self._store.save_goal(goal)
        self._store.update_ticket_truth_status(
            ticket_id,
            ExecutionTruthStatus.WAITING_APPROVAL,
        )
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket_id": ticket_id,
            "goal_id": goal_id,
            "task_id": task_id,
            "truth_status": ExecutionTruthStatus.WAITING_APPROVAL.value,
            "reason": reason,
        }

    # ------------------------------------------------------------------ #
    # 8. resume_reconcile
    # ------------------------------------------------------------------ #

    def resume_reconcile(
        self,
        ticket_id: str,
        *,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Reconcile expired leases and orphaned tasks for ``ticket_id`` without duplicating non-idempotent work."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        goal_id = str(row["goal_id"])
        reconciled_tasks = self._store.reconcile_orphaned_running_tasks(
            goal_id,
            now=now or time.time(),
        )
        goal = self._store.get_goal(goal_id)
        if goal is not None:
            if any(t.truth_status == ExecutionTruthStatus.WAITING_APPROVAL for t in reconciled_tasks):
                goal.status = GoalStatus.BLOCKED
                goal.truth_status = ExecutionTruthStatus.WAITING_APPROVAL
                self._store.save_goal(goal)
            self._store.update_ticket_truth_status(
                ticket_id,
                goal.truth_status,
            )
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket_id": ticket_id,
            "goal_id": goal_id,
            "reconciled": [
                {
                    "task_id": t.id,
                    "status": t.status.value,
                    "truth_status": t.truth_status.value,
                    "blocked_reason": t.blocked_reason,
                }
                for t in reconciled_tasks
            ],
            "status": self.get_status(ticket_id),
        }

    # ------------------------------------------------------------------ #
    # 9. list_durable_reports
    # ------------------------------------------------------------------ #

    def list_durable_reports(
        self,
        *,
        ticket_id: str | None = None,
        delivery_status: str | None = None,
    ) -> dict[str, Any]:
        """List transactional outbox reports (optionally filtered by ``ticket_id`` and ``delivery_status``)."""
        rows = self._store.list_outbox(
            ticket_id=ticket_id,
            delivery_status=delivery_status,
        )
        return {
            "contract_version": CONTRACT_VERSION,
            "count": len(rows),
            "reports": rows,
        }

    # ------------------------------------------------------------------ #
    # 10. get_cost_usage
    # ------------------------------------------------------------------ #

    def get_cost_usage(self, ticket_id: str) -> dict[str, Any]:
        """Return honest cost/token accounting for ``ticket_id`` (never fabricating ``0.0`` when unmeasured)."""
        row = self._store.get_ticket(ticket_id)
        if row is None:
            raise KeyError(f"Unknown ticket_id: {ticket_id}")
        mandate = self._store.verify_mandate_integrity(ticket_id)
        return {
            "contract_version": CONTRACT_VERSION,
            "ticket_id": str(row["ticket_id"]),
            "goal_id": str(row["goal_id"]),
            "cost_budget": mandate.cost_budget,
            "measured_tokens": row.get("measured_tokens"),
            "estimated_tokens": row.get("estimated_tokens"),
            "actual_cost": row.get("actual_cost"),
            "estimated_cost": row.get("estimated_cost"),
            "cost_status": str(row.get("cost_status") or "UNKNOWN"),
        }
