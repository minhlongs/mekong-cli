# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Promise run service — the single execution path for advertised capabilities.

    UI/CLI -> identity + workspace RBAC -> capability/policy -> schema
           -> job row (QUEUED) -> approval gate -> runtime handler
           -> postcondition verification -> signed evidence -> status

Nothing about a run's state is decided by the caller: the browser can submit a
command id and schema-typed parameters, and it receives the state the backend
persisted. Failures stay failures, missing bindings stay ``NOT_IMPLEMENTED``,
and an interrupted run with an uncertain external effect becomes
``NEEDS_RECONCILIATION`` instead of silently disappearing or turning green.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import json
import os
import pathlib
import typing
import uuid

from src.core.capability_ledger import CapabilityLedger
from src.core.promise import gates as gate_registry
from src.core.promise import runtime
from src.core.promise.checks import CheckContext
from src.core.promise.checks import evaluate as evaluate_postconditions
from src.core.promise.contracts import (
    UNCERTAIN_EFFECTS,
    OperationSpec,
    load_default_registry,
)
from src.core.promise.evidence import EvidenceStore
from src.core.promise.identity import (
    Principal,
    authorize_execution,
    authorize_gate_reconcile,
    authorize_read,
)
from src.core.promise.jobs import (
    STATUS_AWAITING_APPROVAL,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_NEEDS_RECONCILIATION,
    STATUS_NOT_IMPLEMENTED,
    STATUS_QUEUED,
    STATUS_REJECTED,
    STATUS_RUNNING,
    JobStore,
    JobStoreError,
    new_run_id,
)
from src.core.promise.schema import SchemaValidationError, validate_params
from src.core.promise.signing import EvidenceSigner, code_version, redact, sha256_of, utc_now_iso

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]


class PromiseError(RuntimeError):
    """Domain error carrying a stable machine code and an HTTP hint."""

    def __init__(self, code: str, message: str, *, http_status: int = 400) -> None:
        self.code = code
        self.http_status = http_status
        super().__init__(message)


@dataclasses.dataclass
class RunOutcome:
    """Everything a caller (CLI, HTTP, UI) is allowed to know about a run."""

    run_id: str
    status: str
    command_id: str
    op_id: str | None
    workspace_id: str
    output: dict[str, typing.Any] = dataclasses.field(default_factory=dict)
    verification: dict[str, typing.Any] = dataclasses.field(default_factory=dict)
    receipt: dict[str, typing.Any] | None = None
    evidence_id: str | None = None
    duration_ms: int = 0
    error_code: str | None = None
    error_message: str | None = None
    maturity_tier: str = ""
    idempotent_replay: bool = False
    approval_request: dict[str, typing.Any] | None = None
    usage: dict[str, typing.Any] = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)


def _state_dir(explicit: str | pathlib.Path | None = None) -> pathlib.Path:
    if explicit:
        return pathlib.Path(explicit).resolve()
    env = os.getenv("MEKONG_PROMISE_STATE_DIR")
    if env:
        return pathlib.Path(env).resolve()
    return REPO_ROOT / ".mekong"


#: Root the per-workspace engine databases are resolved against.
WORKSPACE_ROOT_ENV = "MEKONG_PROMISE_WORKSPACE_ROOT"


def _workspace_root(
    explicit: str | pathlib.Path | None, state_dir: pathlib.Path
) -> pathlib.Path:
    """Where tenant engine databases live.

    Operation effects declare paths such as ``.mekong/workspaces/{id}/vietqr.db``,
    which are resolved against this root. It follows the promise state directory so
    a deployment (or a test) that relocates state with ``MEKONG_PROMISE_STATE_DIR``
    also relocates every tenant ledger — one knob, no writes left behind in the
    source checkout. With the default state dir (``<repo>/.mekong``) the parent is
    the repository root, which is the historical layout.
    """
    if explicit:
        return pathlib.Path(explicit).resolve()
    env = os.getenv(WORKSPACE_ROOT_ENV)
    if env:
        return pathlib.Path(env).resolve()
    return state_dir.parent


class PromiseRunService:
    """Orchestrates authorized, verified, persisted capability executions."""

    def __init__(
        self,
        *,
        state_dir: str | pathlib.Path | None = None,
        workspace_root: str | pathlib.Path | None = None,
        ledger: CapabilityLedger | None = None,
        registry: typing.Any | None = None,
        signer: EvidenceSigner | None = None,
        job_store: JobStore | None = None,
        evidence_store: EvidenceStore | None = None,
        code_version_override: str | None = None,
    ) -> None:
        self.state_dir = _state_dir(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_root = _workspace_root(workspace_root, self.state_dir)
        self.ledger = ledger or CapabilityLedger()
        self.registry = registry or load_default_registry()
        self.signer = signer or EvidenceSigner()
        self.jobs = job_store or JobStore(self.state_dir / "promise_jobs.db")
        self.evidence = evidence_store or EvidenceStore(
            self.state_dir / "promise_evidence.db", signer=self.signer
        )
        self.code_version = code_version_override or code_version()
        self._approval_engine: typing.Any = None
        self._opc_state: typing.Any = None
        self._usage: typing.Any = None

    # ------------------------------------------------------------------
    # Lazy reuse of the existing OPC approval / usage / state subsystems
    # ------------------------------------------------------------------
    @property
    def approvals(self) -> typing.Any:
        if self._approval_engine is None:
            from src.opc.approval import PayloadBoundApprovalEngine

            self._approval_engine = PayloadBoundApprovalEngine()
        return self._approval_engine

    @property
    def opc_state(self) -> typing.Any:
        if self._opc_state is None:
            from src.opc.state import StateStore

            self._opc_state = StateStore(self.state_dir / "opc_state.db")
        return self._opc_state

    @property
    def usage(self) -> typing.Any:
        if self._usage is None:
            from src.opc.usage import UsageLedger

            self._usage = UsageLedger(self.state_dir / "opc_usage.db")
        return self._usage

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------
    def submit(
        self,
        principal: Principal,
        command_id: str,
        params: dict[str, typing.Any] | None = None,
        *,
        subcommand: str | None = None,
        idempotency_key: str | None = None,
        run_id: str | None = None,
        approval_token_id: str | None = None,
    ) -> RunOutcome:
        raw_params = dict(params or {})
        entry = self.ledger.resolve_command(command_id)
        if entry is None:
            raise PromiseError(
                "UNKNOWN_COMMAND",
                f"'{command_id}' is not an advertised capability in the claim ledger",
                http_status=404,
            )
        canonical = entry["name"]
        cluster = entry["cluster"]
        requested_sub = subcommand or str(raw_params.get("subcommand") or "") or None

        spec = self.registry.resolve(canonical, requested_sub)

        # Capability/policy checks run *before* anything is persisted — including
        # the NOT_IMPLEMENTED record for an advertised command with no bound
        # operation, which is still a run row attributed to the caller.
        authorize_execution(
            principal,
            command_id=canonical,
            cluster=cluster,
            external_effect=spec.external_effect if spec else "NONE",
            irreversible_effects=UNCERTAIN_EFFECTS,
        )

        if spec is None:
            return self._record_unimplemented(
                principal, entry, requested_sub, run_id=run_id, idempotency_key=idempotency_key
            )

        active_key = idempotency_key or self._derive_idempotency_key(principal, spec, raw_params)
        if active_key:
            existing = self.jobs.find_by_idempotency_key(principal.workspace_id, active_key)
            if existing:
                return self._outcome_from_job(existing, idempotent_replay=True)

        try:
            clean_params = validate_params(spec.input_schema, raw_params)
        except SchemaValidationError as exc:
            return self._record_failure(
                principal, entry, spec, raw_params, "INPUT_INVALID", str(exc),
                detail={"field_errors": exc.errors}, run_id=run_id, idempotency_key=active_key,
            )

        job = self.jobs.create_job(
            workspace_id=principal.workspace_id,
            principal_id=principal.principal_id,
            command_id=canonical,
            op_id=spec.op_id,
            subcommand=spec.subcommand,
            params=clean_params,
            params_digest=sha256_of(clean_params),
            idempotency_key=active_key,
            status=STATUS_QUEUED,
            external_effect=spec.external_effect,
            code_version=self.code_version,
            run_id=run_id,
        )

        if spec.approval_policy != "AUTO":
            decision = self._require_approval(principal, job, spec, clean_params, approval_token_id)
            if decision is not None:
                return decision

        return self._execute_job(principal, job, spec, entry, clean_params)

    # ------------------------------------------------------------------
    # Approval handling
    # ------------------------------------------------------------------
    def _action_payload(self, job: dict[str, typing.Any], spec: OperationSpec, ttl: int = 3600) -> typing.Any:
        import time as _time

        from src.opc.models import ActionPayload

        budget = dict(spec.cost_policy.get("max_budget") or {})
        return ActionPayload(
            principal=job["principal_id"],
            capability=spec.op_id,
            connector=spec.external_effect,
            recipient=job["workspace_id"],
            content=f"mekong {job['command_id']} {spec.subcommand}".strip(),
            parameters=dict(job["params"]),
            attachments=(),
            budget_amount=str(budget.get("amount", "0")),
            budget_currency=str(budget.get("currency", "VND")),
            expires_at=int(_time.time()) + ttl,
        )

    def request_approval(
        self, principal: Principal, run_id: str, *, ttl_seconds: int = 3600
    ) -> dict[str, typing.Any]:
        job = self.jobs.get_job(run_id, principal.workspace_id)
        if not job:
            raise PromiseError("RUN_NOT_FOUND", f"run '{run_id}' not found in this workspace", http_status=404)
        spec = self.registry.get(job.get("op_id") or "")
        if spec is None:
            raise PromiseError("NO_OPERATION_BINDING", f"run '{run_id}' has no bound operation")
        payload = self._action_payload(job, spec, ttl_seconds)
        self._save_opc_run(principal, job, spec, status_name="PENDING_APPROVAL", payload=payload)
        # ``custom_ttl`` binds the token's own expiry to the requested window:
        # without it every approval silently lived for the engine default, so a
        # caller asking for a five-minute window got an hour.
        token = self.approvals.issue_token(run_id, payload, custom_ttl=ttl_seconds)
        self.opc_state.save_approval(token)
        if job["status"] == STATUS_QUEUED:
            job = self.jobs.transition(
                run_id, principal.workspace_id, STATUS_AWAITING_APPROVAL,
                event_type="APPROVAL_REQUESTED",
                detail={"token_id": token.token_id, "policy": spec.approval_policy,
                        "action_digest": token.action_digest, "expires_at": token.expires_at},
                approval_token_id=token.token_id,
            )
        return {
            "run_id": run_id,
            "status": job["status"],
            "approval_token_id": token.token_id,
            "action_digest": token.action_digest,
            "policy": spec.approval_policy,
            "expires_at": token.expires_at,
            "approver_roles_required": sorted({"founder", "approver"}),
            "payload_preview": redact(payload.parameters),
        }

    def _save_opc_run(
        self,
        principal: Principal,
        job: dict[str, typing.Any],
        spec: OperationSpec,
        *,
        status_name: str,
        payload: typing.Any = None,
    ) -> None:
        """Mirror a promise run into the OPC state store.

        ``opc_approvals.run_id`` is a foreign key onto ``opc_runs``, so an approval
        token may only exist for a run that is itself persisted — and the mirrored
        row is what lets the OPC cockpit show awaiting-approval promise runs.
        """
        import time as _time

        from src.opc.models import WorkflowStatus

        self.opc_state.save_run(
            run_id=str(job["run_id"]),
            pack_id=f"promise:{spec.command}",
            status=WorkflowStatus[status_name],
            profile_data={
                "workspace_id": principal.workspace_id,
                "principal_id": principal.principal_id,
                "command_id": job["command_id"],
                "op_id": spec.op_id,
                "department_id": spec.department_id,
                "layer_id": spec.layer_id,
                "approval_policy": spec.approval_policy,
                "external_effect": spec.external_effect,
                "code_version": self.code_version,
            },
            input_data=dict(job.get("params") or {}),
            now=int(_time.time()),
            action_payload_data=dataclasses.asdict(payload) if payload is not None else None,
        )

    def _require_approval(
        self,
        principal: Principal,
        job: dict[str, typing.Any],
        spec: OperationSpec,
        params: dict[str, typing.Any],
        approval_token_id: str | None,
    ) -> RunOutcome | None:
        """Return an outcome when execution must pause; ``None`` to continue."""
        import time as _time

        if not approval_token_id:
            paused = self.jobs.transition(
                job["run_id"], principal.workspace_id, STATUS_AWAITING_APPROVAL,
                event_type="APPROVAL_REQUIRED",
                detail={"policy": spec.approval_policy, "external_effect": spec.external_effect},
            )
            request = self.request_approval(principal, job["run_id"])
            return RunOutcome(
                run_id=paused["run_id"], status=paused["status"], command_id=job["command_id"],
                op_id=spec.op_id, workspace_id=principal.workspace_id,
                error_code="APPROVAL_REQUIRED",
                error_message=(
                    f"operation '{spec.op_id}' has effect '{spec.external_effect}' and requires "
                    f"{spec.approval_policy}; approval request created"
                ),
                approval_request=request, maturity_tier=self._tier_for(spec),
            )

        token = self.opc_state.get_approval(approval_token_id)
        if token is None:
            return self._fail_job(job, principal, spec, params, "APPROVAL_TOKEN_UNKNOWN",
                                  f"approval token '{approval_token_id}' does not exist")
        payload = self._action_payload(job, spec, ttl=max(1, token.expires_at - int(_time.time())))
        payload = dataclasses.replace(payload, expires_at=token.expires_at)
        try:
            from src.opc.approval import compute_action_digest

            if compute_action_digest(payload) != token.action_digest:
                raise PromiseError(
                    "APPROVAL_PAYLOAD_MISMATCH",
                    "the submitted payload no longer matches the approved payload digest",
                    http_status=409,
                )
            if not self.opc_state.consume_approval_atomic(
                approval_token_id, token.action_digest, int(_time.time())
            ):
                raise PromiseError(
                    "APPROVAL_REPLAY_OR_EXPIRED",
                    "approval token was already consumed, revoked or has expired",
                    http_status=409,
                )
        except PromiseError as exc:
            return self._fail_job(job, principal, spec, params, exc.code, str(exc))
        self.jobs.append_event(job["run_id"], principal.workspace_id, "APPROVAL_CONSUMED",
                               job["status"], job["status"],
                               {"token_id": approval_token_id, "digest": token.action_digest})
        return None

    def decide_approval(
        self,
        approver: Principal,
        run_id: str,
        token_id: str,
        decision: str,
        *,
        notes: str = "",
    ) -> RunOutcome:
        """Approve or reject a paused run, then resume it when approved."""
        from src.core.promise.identity import authorize_approval

        authorize_approval(approver)
        job = self.jobs.get_job(run_id, approver.workspace_id)
        if not job:
            raise PromiseError("RUN_NOT_FOUND", f"run '{run_id}' not found in this workspace", http_status=404)
        token = self.opc_state.get_approval(token_id)
        if token is None or token.run_id != run_id:
            raise PromiseError("APPROVAL_TOKEN_UNKNOWN", f"approval token '{token_id}' is not bound to this run")
        if decision not in {"approve", "reject"}:
            raise PromiseError("INVALID_DECISION", "decision must be 'approve' or 'reject'")

        spec = self.registry.get(job.get("op_id") or "")
        if spec is None:
            raise PromiseError("NO_OPERATION_BINDING", "run has no bound operation")

        if decision == "reject":
            self.opc_state.save_approval(dataclasses.replace(token, revoked=True, revision_notes=notes))
            self._save_opc_run(approver, job, spec, status_name="REJECTED")
            rejected = self.jobs.transition(
                run_id, approver.workspace_id, STATUS_REJECTED, event_type="APPROVAL_REJECTED",
                detail={"token_id": token_id, "approver": approver.principal_id, "notes": notes},
                error_code="APPROVAL_REJECTED", error_message=notes or "rejected by approver",
            )
            return self._outcome_from_job(rejected)

        entry = self.ledger.resolve_command(job["command_id"]) or {}
        self.jobs.append_event(run_id, approver.workspace_id, "APPROVAL_GRANTED",
                               job["status"], job["status"],
                               {"token_id": token_id, "approver": approver.principal_id})
        resumed = self.jobs.transition(run_id, approver.workspace_id, STATUS_QUEUED,
                                       event_type="RESUMED_AFTER_APPROVAL",
                                       detail={"approver": approver.principal_id})
        self._save_opc_run(approver, resumed, spec, status_name="APPROVED")
        outcome = self._execute_job(approver, resumed, spec, entry, resumed["params"],
                                    approval_token_id=token_id)
        self._save_opc_run(
            approver, resumed, spec,
            status_name="COMPLETED" if outcome.status == STATUS_COMPLETED else "FAILED",
        )
        return outcome

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------
    def _execute_job(
        self,
        principal: Principal,
        job: dict[str, typing.Any],
        spec: OperationSpec,
        entry: dict[str, typing.Any],
        params: dict[str, typing.Any],
        *,
        approval_token_id: str | None = None,
    ) -> RunOutcome:
        run_id = job["run_id"]
        workspace_id = principal.workspace_id
        self.jobs.transition(run_id, workspace_id, STATUS_RUNNING, event_type="EXECUTION_STARTED",
                             detail={"op_id": spec.op_id, "handler": spec.handler.describe(),
                                     "attempts": int(job.get("attempts") or 0) + 1},
                             attempts=int(job.get("attempts") or 0) + 1,
                             approval_token_id=approval_token_id or job.get("approval_token_id"))
        self._reserve_budget(run_id, spec, principal)

        outcome = self._run_handler_with_timeout(spec, params, principal, run_id)

        checks: list[dict[str, typing.Any]] = []
        if outcome.handler_ran and not outcome.error_code:
            ctx = CheckContext(
                params=params, result=outcome.payload, engine=outcome.engine,
                engine_db_path=outcome.engine_db_path, workspace_root=self.workspace_root,
                run_id=run_id, workspace_id=workspace_id,
            )
            checks = [c.to_dict() for c in evaluate_postconditions(spec.postconditions, ctx)]

        status, error_code, error_message = self._classify(spec, outcome, checks, run_id, workspace_id)
        verification = {
            "handler_ran": outcome.handler_ran,
            "handler_ref": outcome.handler_ref,
            "checks": checks,
            "required_checks_failed": [
                c["check"] for c in checks if c.get("required", True) and c["status"] != "PASSED"
            ],
            "business_conditions_met": bool(checks) and status == STATUS_COMPLETED,
            "artifacts": outcome.artifacts,
            "engine_db_path": outcome.engine_db_path,
            "status": "PASSED" if status == STATUS_COMPLETED else "FAILED",
            "verifier": f"{spec.op_id}:postconditions",
        }

        evidence_id = None
        receipt = None
        if outcome.handler_ran:
            evidence = self.evidence.record_run_evidence(
                run_id=run_id, workspace_id=workspace_id, principal_id=principal.principal_id,
                command_id=job["command_id"], op_id=spec.op_id,
                gate_id=spec.gate_id or entry.get("gate_id") or None,
                evidence_type=str(entry.get("evidence_type") or spec.output_contract.get("evidence_type")
                                  or "COMMAND_EXECUTION"),
                code_version=self.code_version, input_payload=params,
                output_payload=outcome.payload, handler_ran=True, checks=checks,
            )
            evidence_id = evidence["evidence_id"]
            receipt = self._build_receipt(entry, spec, job, params, outcome, verification,
                                          evidence, principal, status)

        self._record_usage(run_id, spec, outcome, status)

        fields: dict[str, typing.Any] = {
            "result_json": json.dumps(redact(outcome.payload), sort_keys=True, ensure_ascii=False,
                                      default=str),
            "verification_json": json.dumps(verification, sort_keys=True, ensure_ascii=False,
                                            default=str),
            "duration_ms": outcome.duration_ms,
            "error_code": error_code,
            "error_message": error_message,
        }
        if receipt:
            fields["receipt_id"] = f"RCPT-{run_id}"
        updated = self.jobs.transition(run_id, workspace_id, status,
                                       event_type="EXECUTION_FINISHED",
                                       detail={"op_id": spec.op_id, "checks": len(checks)},
                                       **fields)
        self._write_receipt(receipt, run_id, workspace_id, job, spec, entry, status,
                            outcome, params, verification)
        return RunOutcome(
            run_id=run_id, status=updated["status"], command_id=job["command_id"], op_id=spec.op_id,
            workspace_id=workspace_id, output=redact(outcome.payload), verification=verification,
            receipt=receipt, evidence_id=evidence_id, duration_ms=outcome.duration_ms,
            error_code=error_code, error_message=error_message, maturity_tier=self._tier_for(spec),
            usage=self._usage_summary(run_id),
        )

    def _run_handler_with_timeout(
        self,
        spec: OperationSpec,
        params: dict[str, typing.Any],
        principal: Principal,
        run_id: str = "",
    ) -> runtime.HandlerOutcome:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="promise-op") as pool:
            future = pool.submit(
                runtime.execute, spec, params,
                workspace_root=self.workspace_root, workspace_id=principal.workspace_id,
                state_dir=self.state_dir, run_id=run_id, principal_id=principal.principal_id,
            )
            try:
                return future.result(timeout=spec.timeout_seconds)
            except concurrent.futures.TimeoutError:
                return runtime.HandlerOutcome(
                    True, {"status": "TIMEOUT", "error": f"handler exceeded {spec.timeout_seconds}s"},
                    error=f"handler exceeded {spec.timeout_seconds}s", error_code="HANDLER_TIMEOUT",
                    handler_ref=spec.handler.describe(),
                )

    def _classify(
        self,
        spec: OperationSpec,
        outcome: runtime.HandlerOutcome,
        checks: list[dict[str, typing.Any]],
        run_id: str,
        workspace_id: str,
    ) -> tuple[str, str | None, str | None]:
        if outcome.error_code:
            return STATUS_FAILED, outcome.error_code, outcome.error
        failed_required = [c for c in checks if c.get("required", True) and c["status"] != "PASSED"]
        payload_status = str(outcome.payload.get("status", "")).upper()
        uncertain = spec.external_effect in UNCERTAIN_EFFECTS
        if uncertain and (
            payload_status in {"UNKNOWN", "TIMEOUT"}
            or outcome.payload.get("reconciliation_required") is True
            or outcome.error_code == "HANDLER_TIMEOUT"
        ):
            return (STATUS_NEEDS_RECONCILIATION, "PROVIDER_STATE_UNKNOWN",
                    "external effect was attempted but the provider outcome is unknown — reconcile before retrying")
        if failed_required:
            detail = "; ".join(f"{c['check']}: {c.get('detail', '')}" for c in failed_required[:3])
            return STATUS_FAILED, "BUSINESS_CONDITION_UNMET", detail
        if payload_status in {"FAILED", "ERROR"}:
            return STATUS_FAILED, "HANDLER_REPORTED_FAILURE", str(outcome.payload.get("error") or payload_status)
        if not checks:
            return STATUS_FAILED, "NO_POSTCONDITION_EVALUATED", "contract declared no measurable condition"
        return STATUS_COMPLETED, None, None

    # ------------------------------------------------------------------
    # Usage / cost honesty
    # ------------------------------------------------------------------
    def _reserve_budget(self, run_id: str, spec: OperationSpec, principal: Principal) -> None:
        budget = dict(spec.cost_policy.get("max_budget") or {})
        if not budget.get("amount"):
            return
        import time as _time

        from src.opc.models import UsageStage  # noqa: F401  (kept for symmetry with record path)

        self.usage.reserve_budget(
            event_id=f"res_{uuid.uuid4().hex[:12]}", run_id=run_id,
            max_budget_amount=str(budget["amount"]), currency=str(budget.get("currency", "VND")),
            payer=principal.workspace_id, now=int(_time.time()),
            hard_limit=str(budget["hard_limit"]) if budget.get("hard_limit") else None,
        )

    def _record_usage(
        self, run_id: str, spec: OperationSpec, outcome: runtime.HandlerOutcome, status: str
    ) -> None:
        import time as _time

        from src.opc.models import UsageRecord, UsageStage

        reported = outcome.payload.get("usage") if isinstance(outcome.payload, dict) else None
        now = int(_time.time())
        if isinstance(reported, dict) and reported.get("amount") is not None:
            stage = UsageStage.ACTUAL
            amount: str | None = str(reported["amount"])
            currency = str(reported.get("currency", "VND"))
            provider = str(reported.get("provider", spec.handler.module))
        elif spec.external_effect in UNCERTAIN_EFFECTS and status in {
            STATUS_NEEDS_RECONCILIATION, STATUS_FAILED
        }:
            stage = UsageStage.UNKNOWN  # never coerced to zero
            amount = None
            currency = str((spec.cost_policy.get("max_budget") or {}).get("currency", "VND"))
            provider = str(reported.get("provider") if isinstance(reported, dict) else "external")
        else:
            return
        self.usage.record_usage(
            UsageRecord(
                event_id=f"use_{uuid.uuid4().hex[:12]}", run_id=run_id, attempt=1, stage=stage,
                provider=provider, model=str((reported or {}).get("model", "n/a")) if isinstance(reported, dict) else "n/a",
                tokens=int((reported or {}).get("tokens", 0)) if isinstance(reported, dict) else 0,
                tool_fee=None, amount=amount, currency=currency, payer="workspace",
                pricing_source=str((reported or {}).get("pricing_source", "provider_response"))
                if isinstance(reported, dict) else "unknown_provider_state",
                created_at=now,
            )
        )

    def _usage_summary(self, run_id: str) -> dict[str, typing.Any]:
        aggregate = self.usage.aggregate_run_costs(run_id)
        aggregate["stages"] = sorted({r.stage.value for r in self.usage.get_run_records(run_id)})
        return aggregate

    # ------------------------------------------------------------------
    # Receipts
    # ------------------------------------------------------------------
    def _build_receipt(
        self,
        entry: dict[str, typing.Any],
        spec: OperationSpec,
        job: dict[str, typing.Any],
        params: dict[str, typing.Any],
        outcome: runtime.HandlerOutcome,
        verification: dict[str, typing.Any],
        evidence: dict[str, typing.Any],
        principal: Principal,
        status: str,
    ) -> dict[str, typing.Any]:
        body = {
            "receipt_version": "2.0.0",
            "receipt_tier": "TIER_1_COMMAND_EXECUTION",
            "run_id": job["run_id"],
            "workspace_id": principal.workspace_id,
            "principal_id": principal.principal_id,
            "command_id": job["command_id"],
            "op_id": spec.op_id,
            "department_id": entry.get("department_id", spec.department_id),
            "layer_id": entry.get("layer_id", spec.layer_id),
            "owner_agent": entry.get("owner_agent", ""),
            "sop_chain": list(spec.sop_steps or entry.get("sop_steps") or []),
            "gate_id": spec.gate_id or entry.get("gate_id", ""),
            "gate_artifact": entry.get("gate_artifact", ""),
            "input_sha256": sha256_of(redact(params)),
            "output_sha256": sha256_of(redact(outcome.payload)),
            "code_version": self.code_version,
            "handler_ref": outcome.handler_ref,
            "handler_ran": outcome.handler_ran,
            "artifact_integrity": "VERIFIED" if outcome.handler_ran else "UNKNOWN",
            "business_conditions_met": verification["business_conditions_met"],
            "domain_verification": {
                "status": verification["status"],
                "verifier": verification["verifier"],
                "checks": verification["checks"],
            },
            "statutory_citations": list(entry.get("statutory_citations") or spec.statutory_basis),
            "jurisdiction": spec.jurisdiction,
            "rule_version": spec.rule_version,
            "evidence_id": evidence.get("evidence_id"),
            "run_status": status,
            "created_at": utc_now_iso(),
        }
        return self.signer.sign(body)

    def _write_receipt(
        self,
        receipt: dict[str, typing.Any] | None,
        run_id: str,
        workspace_id: str,
        job: dict[str, typing.Any],
        spec: OperationSpec,
        entry: dict[str, typing.Any],
        status: str,
        outcome: runtime.HandlerOutcome,
        params: dict[str, typing.Any],
        verification: dict[str, typing.Any],
    ) -> None:
        """Mirror the receipt into the legacy evidence store for existing consumers."""
        if receipt is None:
            return
        try:
            from src.core.cli_evidence_store import CliEvidenceStore

            legacy = CliEvidenceStore(self.state_dir / "cli_promise_evidence.db")
            legacy.record_run(
                run_id=run_id, command_id=job["command_id"], cluster=entry.get("cluster", ""),
                department_id=entry.get("department_id", ""), layer_id=entry.get("layer_id", ""),
                status=status, input_payload=redact(params), output_payload=redact(outcome.payload),
                error_message=outcome.error, duration_ms=outcome.duration_ms,
            )
            legacy.record_receipt({
                "run_id": run_id, "command_id": job["command_id"],
                "department_id": receipt.get("department_id", ""), "layer_id": receipt.get("layer_id", ""),
                "input_sha256": receipt.get("input_sha256", ""), "output_sha256": receipt.get("output_sha256", ""),
                "signature": receipt.get("signature") or "",
                **{k: v for k, v in receipt.items()
                   if k in {"receipt_version", "receipt_tier", "owner_agent", "sop_chain",
                            "gate_artifact", "domain_verification", "statutory_citations",
                            "created_at", "algorithm", "signing", "workspace_id", "op_id",
                            "code_version", "business_conditions_met", "handler_ran",
                            "evidence_id", "run_status"}},
            })
        except Exception:  # noqa: BLE001, S110 — legacy mirror must never fail the run
            pass
        _ = (spec, verification, workspace_id)

    def verify_receipt(self, receipt: dict[str, typing.Any]) -> dict[str, typing.Any]:
        return self.signer.verify(receipt)

    # ------------------------------------------------------------------
    # Reads, cancellation, recovery, reconciliation
    # ------------------------------------------------------------------
    def get_run(self, principal: Principal, run_id: str) -> dict[str, typing.Any]:
        authorize_read(principal)
        job = self.jobs.get_job(run_id, principal.workspace_id)
        if not job:
            raise PromiseError("RUN_NOT_FOUND", f"run '{run_id}' not found in this workspace", http_status=404)
        return {
            "job": job,
            "events": self.jobs.events(run_id, principal.workspace_id),
            "evidence": self.evidence.get_evidence_for_run(run_id, principal.workspace_id),
            "usage": self._usage_summary(run_id),
        }

    def list_runs(
        self, principal: Principal, *, status: str | None = None, command_id: str | None = None, limit: int = 50
    ) -> list[dict[str, typing.Any]]:
        authorize_read(principal)
        return self.jobs.list_jobs(principal.workspace_id, status=status, command_id=command_id, limit=limit)

    def cancel(self, principal: Principal, run_id: str) -> dict[str, typing.Any]:
        job = self.jobs.get_job(run_id, principal.workspace_id)
        if not job:
            raise PromiseError("RUN_NOT_FOUND", f"run '{run_id}' not found in this workspace", http_status=404)
        try:
            updated = self.jobs.request_cancellation(run_id, principal.workspace_id)
        except JobStoreError as exc:
            raise PromiseError("CANCEL_REJECTED", str(exc), http_status=409) from exc
        return updated

    def recover_after_restart(self) -> list[dict[str, str]]:
        return self.jobs.recover_interrupted(
            uncertain_effects=UNCERTAIN_EFFECTS, code_version=self.code_version
        )

    def reconcile(
        self,
        principal: Principal,
        run_id: str,
        *,
        resolution: str,
        proof: dict[str, typing.Any],
    ) -> dict[str, typing.Any]:
        """Close a ``NEEDS_RECONCILIATION`` run with provider-side proof."""
        job = self.jobs.get_job(run_id, principal.workspace_id)
        if not job:
            raise PromiseError("RUN_NOT_FOUND", f"run '{run_id}' not found in this workspace", http_status=404)
        if job["status"] != STATUS_NEEDS_RECONCILIATION:
            raise PromiseError("NOT_AWAITING_RECONCILIATION",
                               f"run '{run_id}' is {job['status']}, not awaiting reconciliation", http_status=409)
        if resolution not in {"CONFIRMED_COMPLETED", "CONFIRMED_NOT_EXECUTED", "CONFIRMED_FAILED"}:
            raise PromiseError("INVALID_RESOLUTION",
                               "resolution must be CONFIRMED_COMPLETED, CONFIRMED_NOT_EXECUTED or CONFIRMED_FAILED")
        if not proof.get("provider") or not proof.get("reference"):
            raise PromiseError("PROOF_REQUIRED",
                               "reconciliation proof must name the provider and its transaction reference")
        target = STATUS_COMPLETED if resolution == "CONFIRMED_COMPLETED" else STATUS_FAILED
        updated = self.jobs.transition(
            run_id, principal.workspace_id, target, event_type="RECONCILED",
            detail={"resolution": resolution, "proof": redact(proof), "reconciled_by": principal.principal_id},
            error_code=None if target == STATUS_COMPLETED else "RECONCILED_AS_NOT_COMPLETED",
            error_message=None if target == STATUS_COMPLETED else f"provider resolution: {resolution}",
        )
        self.evidence.record_attestation(
            workspace_id=principal.workspace_id, run_id=run_id, kind="RECONCILIATION",
            subject=run_id, attested_by=principal.principal_id,
            criteria={"resolution": resolution, "provider": proof["provider"],
                      "reference": proof["reference"]},
            evidence_refs=[job.get("receipt_id") or run_id],
        )
        return updated

    # ------------------------------------------------------------------
    # Capability / gate views
    # ------------------------------------------------------------------
    def capabilities(self, principal: Principal) -> dict[str, typing.Any]:
        authorize_read(principal)
        items: list[dict[str, typing.Any]] = []
        for entry in self.ledger.list_all():
            ops = self.registry.operations_for(entry["name"])
            items.append({
                **{k: entry.get(k) for k in (
                    "claim_id", "name", "command", "aliases", "cluster", "department_id",
                    "department_name", "layer_id", "promise_summary", "gate_id", "gate_artifact",
                    "owner_agent", "support_agents", "sop_steps", "approval_policy",
                    "external_effects", "statutory_citations", "acceptance_criteria",
                )},
                "executable_operations": [
                    {"op_id": o.op_id, "subcommand": o.subcommand, "title": o.title,
                     "external_effect": o.external_effect, "approval_policy": o.approval_policy,
                     "postconditions": [p.check for p in o.postconditions], "test_id": o.test_id,
                     "handler": o.handler.describe()}
                    for o in ops
                ],
                "operation_count": len(ops),
                "execution_status": (
                    "EXECUTABLE" if ops else "NOT_IMPLEMENTED"
                ),
                "maturity_tier": entry.get("maturity_tier"),
            })
        return {
            "summary": self.ledger.get_summary_stats(),
            "integrity": self.ledger.validate_integrity(),
            "executable_commands": len({o.command for o in self.registry.all()}),
            "executable_operations": len(self.registry),
            "count": len(items),
            "items": items,
        }

    def gates(self, principal: Principal) -> dict[str, typing.Any]:
        authorize_read(principal)
        evaluated = gate_registry.evaluate_all(self.evidence, principal.workspace_id)
        return {
            "gate_tier": "TIER_2_COMPANY_MILESTONE",
            "workspace_id": principal.workspace_id,
            "total_gates": len(evaluated),
            "unlocked_count": sum(1 for g in evaluated if g["status"] == gate_registry.STATUS_SEALED),
            "gates": evaluated,
            "signing": {"status": "SIGNED" if self.signer.is_configured else "UNSIGNED",
                        "key_id": self.signer.identity.key_id},
        }

    def reconcile_gate(self, principal: Principal, gate_id: str) -> dict[str, typing.Any]:
        """Re-measure a gate; sealing is a *result*, never an input."""
        authorize_gate_reconcile(principal)
        if gate_id not in gate_registry.GATE_BY_ID:
            raise PromiseError("UNKNOWN_GATE", f"gate '{gate_id}' is not defined", http_status=404)
        evaluation = gate_registry.evaluate_gate(gate_id, self.evidence, principal.workspace_id)
        evaluation["reconciled_by"] = principal.principal_id
        evaluation["reconciled_at"] = utc_now_iso()
        if evaluation["status"] != gate_registry.STATUS_SEALED:
            evaluation["reason"] = "conditions unmet — gate stays unlocked"
        return evaluation

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _tier_for(self, spec: OperationSpec | None) -> str:
        if spec is None:
            return "NOT_IMPLEMENTED"
        return "REAL_VERIFIED" if spec.test_id else "PARTIAL_LOOKUP"

    def _derive_idempotency_key(
        self, principal: Principal, spec: OperationSpec, params: dict[str, typing.Any]
    ) -> str | None:
        """Derive the replay key from the operation's *declared* identity fields.

        An operation that declares ``idempotency_fields`` is asserting a business
        fact exactly once per identity (a bank transaction, a tax registration, an
        issued invoice). Deriving the key only for provider-side effects silently
        dropped that promise for every workspace-write operation: a double click,
        a retried webhook or a restarted client would create a second run and a
        second row. The engine-level UNIQUE constraints stay as the second line of
        defence — they are what catches a replay submitted under a different key.
        """
        if not spec.idempotency_fields:
            return None
        subset = {k: params.get(k) for k in spec.idempotency_fields}
        return f"{spec.op_id}:{sha256_of(subset)}"

    def _record_unimplemented(
        self,
        principal: Principal,
        entry: dict[str, typing.Any],
        subcommand: str | None,
        *,
        run_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> RunOutcome:
        job = self.jobs.create_job(
            workspace_id=principal.workspace_id, principal_id=principal.principal_id,
            command_id=entry["name"], subcommand=subcommand, params={"subcommand": subcommand},
            params_digest=sha256_of({"subcommand": subcommand}), idempotency_key=idempotency_key,
            status=STATUS_QUEUED, external_effect="NONE", code_version=self.code_version,
            run_id=run_id or new_run_id(),
        )
        updated = self.jobs.transition(
            job["run_id"], principal.workspace_id, STATUS_NOT_IMPLEMENTED,
            event_type="NO_OPERATION_BINDING",
            detail={"advertised_claim": entry.get("claim_id"), "requested_subcommand": subcommand},
            error_code="NO_OPERATION_BINDING",
            error_message=(
                f"'mekong {entry['name']}' is advertised but has no bound business operation yet "
                "(see docs/cli-promise/CLAIM_LEDGER.md)"
            ),
        )
        return RunOutcome(
            run_id=updated["run_id"], status=updated["status"], command_id=entry["name"], op_id=None,
            workspace_id=principal.workspace_id, error_code="NO_OPERATION_BINDING",
            error_message=updated["error_message"], maturity_tier="NOT_IMPLEMENTED",
        )

    def _record_failure(
        self,
        principal: Principal,
        entry: dict[str, typing.Any],
        spec: OperationSpec,
        params: dict[str, typing.Any],
        code: str,
        message: str,
        *,
        detail: dict[str, typing.Any] | None = None,
        run_id: str | None = None,
        idempotency_key: str | None = None,
    ) -> RunOutcome:
        job = self.jobs.create_job(
            workspace_id=principal.workspace_id, principal_id=principal.principal_id,
            command_id=entry["name"], op_id=spec.op_id, subcommand=spec.subcommand, params=params,
            params_digest=sha256_of(params), idempotency_key=idempotency_key, status=STATUS_QUEUED,
            external_effect=spec.external_effect, code_version=self.code_version,
            run_id=run_id or new_run_id(),
        )
        updated = self.jobs.transition(
            job["run_id"], principal.workspace_id, STATUS_FAILED, event_type="PRE_EXECUTION_FAILURE",
            detail=detail or {}, error_code=code, error_message=message,
        )
        return self._outcome_from_job(updated)

    def _fail_job(
        self,
        job: dict[str, typing.Any],
        principal: Principal,
        spec: OperationSpec,
        params: dict[str, typing.Any],
        code: str,
        message: str,
    ) -> RunOutcome:
        updated = self.jobs.transition(
            job["run_id"], principal.workspace_id,
            STATUS_FAILED if job["status"] in {STATUS_QUEUED, STATUS_RUNNING} else STATUS_REJECTED,
            event_type="APPROVAL_FAILURE", detail={"code": code}, error_code=code, error_message=message,
        )
        _ = (spec, params, principal)
        return self._outcome_from_job(updated)

    def _outcome_from_job(self, job: dict[str, typing.Any], *, idempotent_replay: bool = False) -> RunOutcome:
        verification = job.get("verification") or {}
        return RunOutcome(
            run_id=job["run_id"], status=job["status"], command_id=job["command_id"],
            op_id=job.get("op_id"), workspace_id=job["workspace_id"],
            output=job.get("result") or {}, verification=verification,
            duration_ms=int(job.get("duration_ms") or 0), error_code=job.get("error_code"),
            error_message=job.get("error_message"), idempotent_replay=idempotent_replay,
            maturity_tier=self._tier_for(self.registry.get(job.get("op_id") or "")),
            usage=self._usage_summary(job["run_id"]),
        )


_SERVICE: PromiseRunService | None = None


def get_service(**kwargs: typing.Any) -> PromiseRunService:
    """Process-wide service instance (tests inject their own state dir)."""
    global _SERVICE
    if _SERVICE is None or kwargs:
        _SERVICE = PromiseRunService(**kwargs)
    return _SERVICE


def reset_service() -> None:
    global _SERVICE
    _SERVICE = None


__all__ = [
    "PromiseError",
    "PromiseRunService",
    "RunOutcome",
    "get_service",
    "reset_service",
]
