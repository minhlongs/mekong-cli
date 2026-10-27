# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""FastAPI routes for the Mekong CLI product promise (execution + evidence).

Every endpoint goes through the *one* shared execution path:

    HTTP → resolved principal (authn/authz) → schema validation → job store →
    runtime handler (real engine) → postconditions → evidence → signed receipt

Nothing here fabricates an outcome:

* ``POST /v1/cli/runs`` executes a bound operation contract. A command that has
  no real handler comes back as ``NOT_IMPLEMENTED`` — never as ``EXECUTED``.
* ``GET /v1/cli/gates`` and ``POST /v1/cli/gates/{gate_id}/reconcile`` report a
  gate measurement taken from persisted business facts. Sealing is a result of
  the measurement, not something a request body can assert.
* ``POST /v1/cli/receipts/verify`` re-verifies the signature; it does not trust
  the ``signature`` field's presence.

Endpoints:

- ``GET  /v1/cli/capabilities``        advertised ledger × executable registry
- ``POST /v1/cli/runs``                execute an allowlisted command
- ``GET  /v1/cli/runs``                list runs in the caller's workspace
- ``GET  /v1/cli/runs/{run_id}``       status, output, verification, receipt
- ``POST /v1/cli/runs/{run_id}/approval``          request an approval token
- ``POST /v1/cli/runs/{run_id}/approval/decision`` approve / reject a paused run
- ``POST /v1/cli/runs/{run_id}/cancel``            cancel a queued/running job
- ``POST /v1/cli/receipts/verify``     independent signature verification
- ``GET  /v1/cli/gates``               measured company milestone gates
- ``POST /v1/cli/gates/{gate_id}/reconcile``       re-measure one gate
"""

from __future__ import annotations

import json
import typing

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.core.cli_evidence_store import CliEvidenceStore
from src.core.promise.identity import PermissionDeniedError, Principal, resolve_principal
from src.core.promise.jobs import JobStoreError
from src.core.promise.service import PromiseError, PromiseRunService, get_service
from src.core.receipt_signer import verify_receipt_signature

router = APIRouter(prefix="/v1/cli", tags=["CLI Product Promise"])

_legacy_evidence_store = CliEvidenceStore()


# ---------------------------------------------------------------------------
# Identity — HTTP callers are denied unless a credential (or local mode) resolves
# ---------------------------------------------------------------------------

def _resolve_principal(
    request: Request,
    authorization: str | None = Header(default=None),
    x_mekong_api_key: str | None = Header(default=None),
) -> Principal:
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token and x_mekong_api_key:
        token = x_mekong_api_key.strip()
    try:
        principal = resolve_principal(token or None)
    except PermissionDeniedError as exc:
        raise HTTPException(
            status_code=403, detail={"code": exc.code, "message": str(exc)}
        ) from exc
    _ = request
    return principal


PrincipalDep = Depends(_resolve_principal)


def _service() -> PromiseRunService:
    """Process-wide promise service (state dir from ``MEKONG_PROMISE_STATE_DIR``)."""
    return get_service()


def _http_error(exc: PromiseError) -> HTTPException:
    return HTTPException(status_code=exc.http_status, detail={"code": exc.code, "message": str(exc)})


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class CommandRunRequest(BaseModel):
    command_id: str = Field(..., description="Allowlisted command name, alias, or claim_id")
    params: dict[str, typing.Any] = Field(default_factory=dict,
                                          description="Schema-validated parameters")
    subcommand: str | None = Field(default=None, description="Operation subcommand (or params.subcommand)")
    run_id: str | None = Field(default=None, description="Optional caller-supplied run identifier")
    idempotency_key: str | None = Field(default=None, description="Replay-protection key")
    approval_token_id: str | None = Field(default=None, description="Approval token for gated effects")


class ApprovalDecisionRequest(BaseModel):
    token_id: str = Field(..., min_length=4, description="Approval token bound to the run payload")
    decision: str = Field(..., pattern="^(approve|reject)$")
    notes: str = Field(default="", max_length=500)


class ReceiptVerifyRequest(BaseModel):
    receipt: dict[str, typing.Any] = Field(..., description="Full receipt object")


class GateReconcileRequest(BaseModel):
    transaction_id: str = Field(..., min_length=3,
                                description="Identifier of an already-recorded reconciled transaction")
    evidence_ref: str = Field(..., min_length=3,
                              description="Identifier of already-recorded evidence (evidence_id or run_id)")


# ---------------------------------------------------------------------------
# Capabilities: advertised ledger reconciled against the executable registry
# ---------------------------------------------------------------------------

@router.get("/capabilities")
async def get_capabilities(
    principal: Principal = PrincipalDep,
    cluster: str | None = Query(default=None),
    department_id: str | None = Query(default=None),
    layer_id: str | None = Query(default=None),
    maturity_tier: str | None = Query(default=None),
    execution_status: str | None = Query(default=None,
                                         description="EXECUTABLE | NOT_IMPLEMENTED"),
) -> dict[str, typing.Any]:
    """List advertised capabilities together with their executable binding."""
    service = _service()
    try:
        report = service.capabilities(principal)
    except (PromiseError, PermissionDeniedError) as exc:
        raise _http_error(exc) if isinstance(exc, PromiseError) else HTTPException(
            status_code=403, detail={"code": exc.code, "message": str(exc)}) from exc

    items = [
        item for item in report["items"]
        if (cluster is None or item.get("cluster") == cluster)
        and (department_id is None or item.get("department_id") == department_id)
        and (layer_id is None or item.get("layer_id") == layer_id)
        and (maturity_tier is None or item.get("maturity_tier") == maturity_tier)
        and (execution_status is None or item.get("execution_status") == execution_status)
    ]
    executable = [i for i in items if i.get("execution_status") == "EXECUTABLE"]
    return {
        "summary": report["summary"],
        "integrity": report["integrity"],
        "count": len(items),
        "items": items,
        "execution_binding": {
            "advertised_command_groups": report["count"],
            "executable_command_groups": report["executable_commands"],
            "executable_operations": report["executable_operations"],
            "filtered_executable": len(executable),
            "filtered_not_implemented": len(items) - len(executable),
            "note": ("maturity_tier in the ledger is the *advertised* claim; execution_status is "
                     "measured from the executable operation registry"),
        },
    }


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

@router.post("/runs")
async def create_command_run(
    req: CommandRunRequest,
    principal: Principal = PrincipalDep,
) -> dict[str, typing.Any]:
    """Execute an allowlisted command through the shared runtime and return its receipt."""
    service = _service()
    params = dict(req.params or {})
    subcommand = req.subcommand or str(params.pop("subcommand", "") or "") or None
    try:
        outcome = service.submit(
            principal, req.command_id, params,
            subcommand=subcommand, run_id=req.run_id,
            idempotency_key=req.idempotency_key, approval_token_id=req.approval_token_id,
        )
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc
    return _run_payload(outcome.to_dict())


@router.get("/runs")
async def list_command_runs(
    principal: Principal = PrincipalDep,
    status: str | None = Query(default=None),
    command_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> dict[str, typing.Any]:
    """List runs persisted for the caller's workspace (survives refresh/restart)."""
    service = _service()
    try:
        runs = service.list_runs(principal, status=status, command_id=command_id, limit=limit)
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc
    return {"workspace_id": principal.workspace_id, "count": len(runs), "runs": runs}


@router.get("/runs/{run_id}")
async def get_command_run(run_id: str, principal: Principal = PrincipalDep) -> dict[str, typing.Any]:
    """Fetch a persisted run: status, output, postconditions and signed receipt."""
    service = _service()
    try:
        record = service.get_run(principal, run_id)
    except PromiseError as exc:
        if exc.code != "RUN_NOT_FOUND":
            raise _http_error(exc) from exc
        record = None
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc
    if record:
        return {**record, "source": "promise_job_store"}

    # Runs recorded by the pre-promise receipt store are still readable, but they
    # are labelled so a UI can never present them as a verified promise run.
    legacy = _legacy_evidence_store.get_run(run_id)
    if legacy:
        return {**legacy, "source": "legacy_receipt_store"}
    raise HTTPException(status_code=404,
                        detail={"code": "RUN_NOT_FOUND",
                                "message": f"run '{run_id}' not found in workspace "
                                           f"'{principal.workspace_id}'"})


@router.post("/runs/{run_id}/approval")
async def request_run_approval(run_id: str, principal: Principal = PrincipalDep) -> dict[str, typing.Any]:
    """Issue an approval token bound to the run's payload digest."""
    service = _service()
    try:
        return service.request_approval(principal, run_id)
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc
    except JobStoreError as exc:
        raise HTTPException(status_code=409,
                            detail={"code": "ILLEGAL_RUN_STATE", "message": str(exc)}) from exc


@router.post("/runs/{run_id}/approval/decision")
async def decide_run_approval(
    run_id: str,
    req: ApprovalDecisionRequest,
    principal: Principal = PrincipalDep,
) -> dict[str, typing.Any]:
    """Approve or reject a paused run; approval resumes real execution."""
    service = _service()
    try:
        outcome = service.decide_approval(principal, run_id, req.token_id, req.decision,
                                          notes=req.notes)
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc
    except JobStoreError as exc:
        raise HTTPException(status_code=409,
                            detail={"code": "ILLEGAL_RUN_STATE", "message": str(exc)}) from exc
    return _run_payload(outcome.to_dict())


@router.post("/runs/{run_id}/cancel")
async def cancel_command_run(run_id: str, principal: Principal = PrincipalDep) -> dict[str, typing.Any]:
    """Cancel a queued or paused run (terminal runs cannot be cancelled)."""
    service = _service()
    try:
        return service.cancel(principal, run_id)
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc
    except JobStoreError as exc:
        raise HTTPException(status_code=409,
                            detail={"code": "ILLEGAL_RUN_STATE", "message": str(exc)}) from exc


def _run_payload(data: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """Shape a run for the website/CLI contract (keys the bridge already reads)."""
    verification = data.get("verification") or {}
    return {
        "run_id": data.get("run_id"),
        "command_id": data.get("command_id"),
        "op_id": data.get("op_id"),
        "status": data.get("status"),
        "output": data.get("output") or {},
        "receipt": data.get("receipt"),
        "evidence_id": data.get("evidence_id"),
        "domain_verification": {
            "handler_ran": verification.get("handler_ran"),
            "business_conditions_met": verification.get("business_conditions_met"),
            "checks": verification.get("checks") or [],
            "required_checks_failed": verification.get("required_checks_failed") or [],
            "artifacts": verification.get("artifacts") or [],
            "verifier": verification.get("verifier"),
            "status": verification.get("status"),
        },
        "duration_ms": data.get("duration_ms"),
        "maturity_tier": data.get("maturity_tier"),
        "error_code": data.get("error_code"),
        "error_message": data.get("error_message"),
        "approval_request": data.get("approval_request"),
        "usage": data.get("usage") or {},
        "idempotent_replay": bool(data.get("idempotent_replay")),
        "workspace_id": data.get("workspace_id"),
    }


# ---------------------------------------------------------------------------
# Receipt verification
# ---------------------------------------------------------------------------

@router.post("/receipts/verify")
async def verify_command_receipt(
    req: ReceiptVerifyRequest,
    principal: Principal = PrincipalDep,
) -> dict[str, typing.Any]:
    """Re-verify a receipt signature; v2 receipts also report business conditions."""
    receipt = dict(req.receipt or {})
    if str(receipt.get("receipt_version") or "").startswith("2"):
        service = _service()
        try:
            result = service.verify_receipt(receipt)
        except PromiseError as exc:
            raise _http_error(exc) from exc
        except PermissionDeniedError as exc:
            raise HTTPException(status_code=403,
                                detail={"code": exc.code, "message": str(exc)}) from exc
        return {
            "valid": bool(result.get("valid")),
            "run_id": receipt.get("run_id"),
            "command_id": receipt.get("command_id"),
            "algorithm": receipt.get("algorithm", "HMAC-SHA256"),
            "domain_verification": {
                "handler_ran": receipt.get("handler_ran"),
                "artifact_integrity": receipt.get("artifact_integrity"),
                "business_conditions_met": receipt.get("business_conditions_met"),
            },
            "signing": result.get("signing") or receipt.get("signing"),
            "reason": result.get("reason"),
            "receipt_version": receipt.get("receipt_version"),
        }
    # Legacy Tier-1 receipts (pre-promise dispatcher): verify the HMAC the same
    # way the old route did, but report honestly when the signature is absent.
    legacy = dict(receipt)
    signature = legacy.pop("signature", None)
    legacy.pop("algorithm", None)
    if not signature or not isinstance(signature, str):
        return {"valid": False, "reason": "Missing or invalid signature field in receipt.",
                "run_id": legacy.get("run_id"), "command_id": legacy.get("command_id"),
                "algorithm": "HMAC-SHA256", "receipt_version": "1.0.0"}
    return {
        "valid": bool(verify_receipt_signature(legacy, signature)),
        "run_id": legacy.get("run_id"),
        "command_id": legacy.get("command_id"),
        "algorithm": "HMAC-SHA256",
        "domain_verification": legacy.get("domain_verification"),
        "receipt_version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Company milestone gates — measured, never asserted
# ---------------------------------------------------------------------------

@router.get("/gates")
async def list_company_gates(principal: Principal = PrincipalDep) -> dict[str, typing.Any]:
    """Measure every L0–L5 company milestone gate from persisted business facts."""
    service = _service()
    try:
        return service.gates(principal)
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc


@router.post("/gates/{gate_id}/reconcile")
async def reconcile_company_gate(
    gate_id: str,
    req: GateReconcileRequest,
    principal: Principal = PrincipalDep,
) -> dict[str, typing.Any]:
    """Re-measure one gate; seal it only if the measurement says every condition is met.

    The submitted ``transaction_id`` / ``evidence_ref`` must already exist as
    persisted evidence in the caller's workspace. They are references to proof,
    not proof: a gate is sealed by the measured conditions, and this endpoint
    returns 409 with the unmet conditions when the facts are not there.
    """
    service = _service()
    try:
        measured = service.reconcile_gate(principal, gate_id)
    except PromiseError as exc:
        raise _http_error(exc) from exc
    except PermissionDeniedError as exc:
        raise HTTPException(status_code=403,
                            detail={"code": exc.code, "message": str(exc)}) from exc

    conditions = {c["condition"]: bool(c["met"]) for c in measured.get("conditions", [])}
    references = _known_references(service, principal.workspace_id)
    unknown = [
        label for label, value in (("transaction_id", req.transaction_id),
                                   ("evidence_ref", req.evidence_ref))
        if value not in references
    ]
    if unknown:
        raise HTTPException(status_code=409, detail={
            "code": "EVIDENCE_REFERENCE_UNKNOWN",
            "message": (f"{', '.join(unknown)} does not match any evidence recorded in workspace "
                        f"'{principal.workspace_id}' — run the command that produces it first"),
            "gate_id": gate_id,
            "status": measured.get("status"),
            "conditions": measured.get("conditions"),
        })

    sealed = bool(conditions) and all(conditions.values())
    if sealed:
        _legacy_evidence_store.unlock_gate_with_reconciliation(
            gate_id=gate_id,
            transaction_id=req.transaction_id,
            evidence_ref=req.evidence_ref,
            verified_conditions=conditions,
        )
        return {
            "gate_id": gate_id,
            "status": measured.get("status"),
            "sealed": True,
            "conditions": measured.get("conditions"),
            "reconciled_transaction_id": req.transaction_id,
            "evidence_ref": req.evidence_ref,
            "reconciled_by": measured.get("reconciled_by"),
            "reconciled_at": measured.get("reconciled_at"),
        }

    raise HTTPException(status_code=409, detail={
        "code": "GATE_CONDITIONS_UNMET",
        "message": "gate stays unlocked — the measured business conditions are not satisfied",
        "gate_id": gate_id,
        "status": measured.get("status"),
        "conditions": measured.get("conditions"),
        "unmet": sorted(name for name, met in conditions.items() if not met),
    })


def _known_references(service: PromiseRunService, workspace_id: str) -> set[str]:
    """Every identifier that counts as recorded evidence inside one workspace."""
    refs: set[str] = set()
    store = service.evidence
    for row in store.query("revenue_transactions", workspace_id):
        refs.add(str(row.get("tx_id") or ""))
        raw = row.get("provider_confirmation_json")
        if isinstance(raw, str) and raw:
            try:
                confirmation = json.loads(raw)
            except ValueError:
                confirmation = {}
            for key in ("bank_tx_id", "reference", "provider_reference"):
                if confirmation.get(key):
                    refs.add(str(confirmation[key]))
    for table in ("deployment_proofs", "client_acceptances", "attestations"):
        for row in store.query(table, workspace_id):
            for key in ("proof_id", "acceptance_id", "attestation_id", "run_id", "subject"):
                if row.get(key):
                    refs.add(str(row[key]))
    for row in store.query("promise_evidence", workspace_id):
        for key in ("evidence_id", "run_id"):
            if row.get(key):
                refs.add(str(row[key]))
    refs.discard("")
    return refs
