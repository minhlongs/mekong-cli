# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""FastAPI Routes for Mekong CLI Product Promise & Fullstack Execution.

Endpoints:
- ``GET /v1/cli/capabilities``: List 197 command groups with contract metadata.
- ``POST /v1/cli/runs``: Execute an allowlisted command, verify, sign receipt, and store.
- ``GET /v1/cli/runs/{run_id}``: Fetch run status, output, and cryptographic receipt.
- ``POST /v1/cli/receipts/verify``: Independently verify HMAC-SHA256 receipt integrity.
- ``GET /v1/cli/gates``: Fetch Tier 2 L0–L5 Company Milestone Gates status.
- ``POST /v1/cli/gates/{gate_id}/reconcile``: Unlock a milestone gate with reconciliation proof.
"""

from __future__ import annotations

import typing

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.capability_ledger import CapabilityLedger
from src.core.cli_command_dispatcher import CliCommandDispatcher, CommandExecutionError
from src.core.cli_evidence_store import CliEvidenceStore
from src.core.receipt_signer import verify_receipt_signature

router = APIRouter(prefix="/v1/cli", tags=["CLI Product Promise"])

_ledger = CapabilityLedger()
_evidence_store = CliEvidenceStore()
_dispatcher = CliCommandDispatcher(ledger=_ledger, evidence_store=_evidence_store)


class CommandRunRequest(BaseModel):
    command_id: str = Field(..., description="Allowlisted command name, alias, or claim_id")
    params: dict[str, typing.Any] = Field(default_factory=dict, description="Schema-validated parameters")
    run_id: str | None = Field(default=None, description="Optional idempotent run identifier")


class ReceiptVerifyRequest(BaseModel):
    receipt: dict[str, typing.Any] = Field(..., description="Full CommandExecutionReceipt object")


class GateReconcileRequest(BaseModel):
    transaction_id: str = Field(..., min_length=3, description="Reconciled banking or audit transaction ID")
    evidence_ref: str = Field(..., min_length=3, description="Reference to verifiable external artifact")


@router.get("/capabilities")
async def get_capabilities(
    cluster: str | None = Query(default=None),
    department_id: str | None = Query(default=None),
    layer_id: str | None = Query(default=None),
    maturity_tier: str | None = Query(default=None),
) -> dict[str, typing.Any]:
    """List capability ledger entries and summary statistics."""
    items = _ledger.list_all(
        cluster=cluster,
        department_id=department_id,
        layer_id=layer_id,
        maturity_tier=maturity_tier,
    )
    return {
        "summary": _ledger.get_summary_stats(),
        "integrity": _ledger.validate_integrity(),
        "count": len(items),
        "items": items,
    }


@router.post("/runs")
async def create_command_run(req: CommandRunRequest) -> dict[str, typing.Any]:
    """Execute an allowlisted CLI command in-process and return signed Tier 1 receipt."""
    try:
        result = _dispatcher.dispatch(
            command_id=req.command_id,
            params=req.params,
            run_id=req.run_id,
        )
        return result
    except CommandExecutionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/runs/{run_id}")
async def get_command_run(run_id: str) -> dict[str, typing.Any]:
    """Retrieve stored run status, output, and cryptographic receipt."""
    record = _evidence_store.get_run(run_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return record


@router.post("/receipts/verify")
async def verify_command_receipt(req: ReceiptVerifyRequest) -> dict[str, typing.Any]:
    """Cryptographically verify a Tier 1 CommandExecutionReceipt signature."""
    receipt_copy = dict(req.receipt)
    signature = receipt_copy.pop("signature", None)
    receipt_copy.pop("algorithm", None)

    if not signature or not isinstance(signature, str):
        return {
            "valid": False,
            "reason": "Missing or invalid signature field in receipt.",
        }

    is_valid = verify_receipt_signature(receipt_copy, signature)
    return {
        "valid": is_valid,
        "run_id": receipt_copy.get("run_id"),
        "command_id": receipt_copy.get("command_id"),
        "algorithm": "HMAC-SHA256",
        "domain_verification": receipt_copy.get("domain_verification"),
    }


@router.get("/gates")
async def list_company_gates() -> dict[str, typing.Any]:
    """List Tier 2 L0–L5 Company Milestone Gates and their verification status."""
    gates = _evidence_store.list_gates()
    unlocked_count = sum(1 for g in gates if g.get("status") == "SEALED_VERIFIED")
    return {
        "gate_tier": "TIER_2_COMPANY_MILESTONE",
        "total_gates": len(gates),
        "unlocked_count": unlocked_count,
        "gates": gates,
    }


@router.post("/gates/{gate_id}/reconcile")
async def reconcile_company_gate(gate_id: str, req: GateReconcileRequest) -> dict[str, typing.Any]:
    """Unlock a Tier 2 Company Milestone Gate with external reconciliation proof."""
    updated = _evidence_store.unlock_gate_with_reconciliation(
        gate_id=gate_id,
        transaction_id=req.transaction_id,
        evidence_ref=req.evidence_ref,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Milestone gate '{gate_id}' not found.")
    return {
        "gate_id": gate_id,
        "status": "SEALED_VERIFIED",
        "reconciled_transaction_id": req.transaction_id,
        "evidence_ref": req.evidence_ref,
    }
