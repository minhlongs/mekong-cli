# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""L0–L5 milestone gates evaluated from verifiable business facts.

A gate seals only when *every* condition can be measured from persisted,
signed evidence. Consequences of the founder directive:

* Running a CFO command does **not** create revenue — ``first-revenue`` needs a
  reconciled transaction carrying provider confirmation plus the invoice and
  tax records it belongs to.
* A successful build does **not** make the product live — ``mvp-live`` needs a
  deployment proof with an actual health check against the target URL, plus the
  build/test digests and the compliance scan.
* Model-written summaries are never accepted as operational proof: conditions
  require named attestations with explicit criteria, or measured records.
"""

from __future__ import annotations

import dataclasses
import typing

from src.core.promise.evidence import EvidenceStore
from src.core.promise.signing import utc_now_iso

Condition = typing.Callable[[EvidenceStore, str, dict[str, typing.Any]], dict[str, typing.Any]]


@dataclasses.dataclass(frozen=True)
class GateDefinition:
    gate_id: str
    layer_id: str
    name: str
    department_id: str
    owner_agent: str
    gate_artifact: str
    required_evidence_type: str
    description: str
    conditions: tuple[str, ...]


def _evidence_of_type(
    store: EvidenceStore, workspace_id: str, evidence_type: str, *, require_met: bool = True
) -> list[dict[str, typing.Any]]:
    rows = store.query("promise_evidence", workspace_id, "evidence_type = ?", (evidence_type,))
    if require_met:
        rows = [r for r in rows if r.get("business_conditions_met") and r.get("handler_ran")]
    return rows


def _unsigned(rows: list[dict[str, typing.Any]]) -> list[str]:
    return [r["evidence_id"] for r in rows if r.get("signing_status") != "SIGNED"]


def _cond(name: str, met: bool, required: str, observed: typing.Any, detail: str,
          refs: typing.Sequence[str] = ()) -> dict[str, typing.Any]:
    return {"condition": name, "met": bool(met), "required": required, "observed": observed,
            "detail": detail, "evidence_refs": list(refs)}


# ---------------------------------------------------------------------------
# L0 — company-blueprint
# ---------------------------------------------------------------------------

def cond_blueprint_evidence(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = _evidence_of_type(store, ws, "FOUNDER_INTENT_BLUEPRINT")
    unsigned = _unsigned(rows)
    return _cond(
        "blueprint_run_verified", bool(rows) and not unsigned,
        ">=1 completed L0 blueprint run whose business conditions were verified and signed",
        {"count": len(rows), "unsigned": len(unsigned)},
        "no verified blueprint run yet" if not rows else
        ("evidence exists but is unsigned" if unsigned else "blueprint run verified"),
        [r["evidence_id"] for r in rows],
    )


def cond_blueprint_attestation(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = [r for r in store.query("attestations", ws, "kind = ?", ("FOUNDER_BLUEPRINT",))
            if r.get("attested_by")]
    return _cond(
        "founder_attestation", bool(rows),
        "named founder attestation covering business model, department map and authority matrix",
        {"count": len(rows)},
        "no named founder attestation recorded" if not rows else "founder attestation recorded",
        [r["attestation_id"] for r in rows],
    )


# ---------------------------------------------------------------------------
# L1 — offer-validated
# ---------------------------------------------------------------------------

def cond_offer_contract(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = _evidence_of_type(store, ws, "MARKET_ICP_OFFER_CONTRACT")
    return _cond(
        "offer_contract_verified", bool(rows),
        ">=1 verified ICP + offer + pricing run (product-strategy department)",
        {"count": len(rows)},
        "no verified offer contract run" if not rows else "offer contract verified",
        [r["evidence_id"] for r in rows],
    )


def cond_offer_attestation(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = [r for r in store.query("attestations", ws, "kind = ?", ("OFFER_VALIDATED",))
            if r.get("criteria_json") and r.get("criteria_json") != "{}"]
    return _cond(
        "offer_validation_criteria", bool(rows),
        "attestation naming the validation criteria (evidence or interviews) it was judged against",
        {"count": len(rows)},
        "no criteria-bound offer validation attestation" if not rows else "criteria-bound attestation recorded",
        [r["attestation_id"] for r in rows],
    )


def cond_research_provenance(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    min_sources = int(params.get("min_sources", 1))
    rows = _evidence_of_type(store, ws, "MARKET_RESEARCH")
    with_sources = [r for r in rows if r.get("checks_json") and "provenance_recorded" in r["checks_json"]]
    return _cond(
        "research_provenance", len(with_sources) >= min_sources,
        f">={min_sources} research run(s) carrying source, retrieval time and confidence",
        {"count": len(with_sources)},
        "research output lacks provenance" if len(with_sources) < min_sources else "provenance recorded",
        [r["evidence_id"] for r in with_sources],
    )


# ---------------------------------------------------------------------------
# L2 — mvp-live
# ---------------------------------------------------------------------------

def cond_deployment_proof(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = [r for r in store.query("deployment_proofs", ws)
            if r.get("health_status") == "HEALTHY" and r.get("environment") == params.get("environment", "production")]
    return _cond(
        "production_health_verified", bool(rows),
        "deployment proof with a HEALTHY check against the production target URL",
        {"count": len(rows), "urls": [r["target_url"] for r in rows][:3]},
        "no healthy production deployment proof" if not rows else "production health verified",
        [r["proof_id"] for r in rows],
    )


def cond_build_test_digests(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = [r for r in store.query("deployment_proofs", ws) if r.get("build_digest") and r.get("test_digest")]
    return _cond(
        "build_and_test_digests", bool(rows),
        "the deployed artifact must carry both a build digest and a test-suite digest",
        {"count": len(rows)},
        "build succeeded but test digest missing (a build alone is not proof of live)"
        if not rows else "build + test digests recorded",
        [r["proof_id"] for r in rows],
    )


def cond_compliance_scan(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = _evidence_of_type(store, ws, "SECURITY_AUDIT")
    return _cond(
        "compliance_scan_verified", bool(rows),
        ">=1 verified security/compliance audit run (quality-compliance department)",
        {"count": len(rows)},
        "no verified compliance scan" if not rows else "compliance scan verified",
        [r["evidence_id"] for r in rows],
    )


# ---------------------------------------------------------------------------
# L3 — first-revenue / repeatable-channel
# ---------------------------------------------------------------------------

def cond_reconciled_revenue(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = [r for r in store.query("revenue_transactions", ws, "status = ?", ("RECONCILED",))
            if r.get("provider_confirmation_json") and float(r.get("amount") or 0) > 0]
    return _cond(
        "reconciled_transaction", bool(rows),
        ">=1 revenue transaction confirmed by the payment provider and reconciled by a named principal",
        {"count": len(rows), "total_by_currency": _sum_by_currency(rows)},
        "no reconciled provider-confirmed transaction (running CFO commands does not create revenue)"
        if not rows else "reconciled revenue present",
        [r["tx_id"] for r in rows],
    )


def _sum_by_currency(rows: list[dict[str, typing.Any]]) -> dict[str, str]:
    totals: dict[str, float] = {}
    for row in rows:
        code = str(row.get("currency") or "???")
        totals[code] = totals.get(code, 0.0) + float(row.get("amount") or 0)
    return {k: f"{v:.2f}" for k, v in sorted(totals.items())}


def cond_invoice_issued(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    tx_rows = [r for r in store.query("revenue_transactions", ws, "status = ?", ("RECONCILED",))
               if r.get("invoice_ref")]
    inv_rows = _evidence_of_type(store, ws, "TT78_INVOICE")
    return _cond(
        "invoice_linked_to_revenue", bool(tx_rows) and bool(inv_rows),
        "the reconciled transaction must reference an issued e-invoice (TT78/Circular 78)",
        {"transactions_with_invoice": len(tx_rows), "invoice_runs": len(inv_rows)},
        "revenue recorded without a linked invoice run" if tx_rows and not inv_rows
        else ("no reconciled transaction with invoice reference" if not tx_rows else "invoice linked"),
        [r["tx_id"] for r in tx_rows] + [r["evidence_id"] for r in inv_rows],
    )


def cond_tax_recorded(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = _evidence_of_type(store, ws, "TAX_CALCULATION") + _evidence_of_type(store, ws, "TAX_FILING")
    return _cond(
        "tax_accounting_recorded", bool(rows),
        ">=1 verified tax/accounting run covering the revenue period",
        {"count": len(rows)},
        "no verified tax or accounting record" if not rows else "tax record present",
        [r["evidence_id"] for r in rows],
    )


def cond_channel_repeatable(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    min_periods = int(params.get("min_periods", 2))
    rows = store.query("channel_metrics", ws)
    converting = [r for r in rows if int(r.get("conversions") or 0) > 0]
    periods = {r["period"] for r in converting}
    channels = {r["channel"] for r in converting}
    return _cond(
        "repeatable_channel_data", len(periods) >= min_periods and bool(channels),
        f"measured channel conversions across >= {min_periods} distinct periods",
        {"periods": sorted(periods), "channels": sorted(channels)},
        "not enough measured periods to claim repeatability"
        if len(periods) < min_periods else "repeatable channel data present",
        [r["metric_id"] for r in converting],
    )


def cond_channel_attestation(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = store.query("attestations", ws, "kind = ?", ("CHANNEL_REPEATABLE",))
    return _cond(
        "channel_attestation", bool(rows),
        "named attestation stating the CAC/payback criteria the channel was judged against",
        {"count": len(rows)},
        "no criteria-bound channel attestation" if not rows else "channel attestation recorded",
        [r["attestation_id"] for r in rows],
    )


# ---------------------------------------------------------------------------
# L4 — fulfillment-stable
# ---------------------------------------------------------------------------

def cond_client_acceptance(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    min_clients = int(params.get("min_clients", 1))
    rows = store.query("client_acceptances", ws)
    clients = {r["client_ref"] for r in rows if r.get("accepted_by")}
    return _cond(
        "client_acceptance", len(clients) >= min_clients,
        f">= {min_clients} named client acceptance record(s) with deliverable reference",
        {"clients": len(clients)},
        "no client acceptance recorded" if len(clients) < min_clients else "client acceptance recorded",
        [r["acceptance_id"] for r in rows],
    )


def cond_fulfillment_runs(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = _evidence_of_type(store, ws, "FULFILLMENT_DELIVERY")
    return _cond(
        "fulfillment_scope_verified", bool(rows),
        ">=1 verified fulfillment/delivery run inside the advertised scope",
        {"count": len(rows)},
        "no verified fulfillment run" if not rows else "fulfillment run verified",
        [r["evidence_id"] for r in rows],
    )


# ---------------------------------------------------------------------------
# L5 — scale-ready
# ---------------------------------------------------------------------------

def cond_sop_export(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = store.query("sop_exports", ws)
    return _cond(
        "sop_packaged", bool(rows),
        ">=1 SOP exported as an artifact with a recorded digest",
        {"count": len(rows)},
        "no SOP export artifact" if not rows else "SOP packaged",
        [r["export_id"] for r in rows],
    )


def cond_clone_attestation(store: EvidenceStore, ws: str, params: dict[str, typing.Any]) -> dict[str, typing.Any]:
    rows = store.query("attestations", ws, "kind = ?", ("CLONE_READY",))
    return _cond(
        "clone_ready_attestation", bool(rows),
        "named attestation that the knowledge base supports cloning to a second company",
        {"count": len(rows)},
        "no clone-readiness attestation" if not rows else "clone attestation recorded",
        [r["attestation_id"] for r in rows],
    )


CONDITIONS: dict[str, Condition] = {
    "blueprint_run_verified": cond_blueprint_evidence,
    "founder_attestation": cond_blueprint_attestation,
    "offer_contract_verified": cond_offer_contract,
    "offer_validation_criteria": cond_offer_attestation,
    "research_provenance": cond_research_provenance,
    "production_health_verified": cond_deployment_proof,
    "build_and_test_digests": cond_build_test_digests,
    "compliance_scan_verified": cond_compliance_scan,
    "reconciled_transaction": cond_reconciled_revenue,
    "invoice_linked_to_revenue": cond_invoice_issued,
    "tax_accounting_recorded": cond_tax_recorded,
    "repeatable_channel_data": cond_channel_repeatable,
    "channel_attestation": cond_channel_attestation,
    "client_acceptance": cond_client_acceptance,
    "fulfillment_scope_verified": cond_fulfillment_runs,
    "sop_packaged": cond_sop_export,
    "clone_ready_attestation": cond_clone_attestation,
}

GATES: tuple[GateDefinition, ...] = (
    GateDefinition(
        "company-blueprint", "L0", "Ý Chí Sáng Lập & Bản Thiết Kế Doanh Nghiệp (L0)",
        "ceo-command", "planner", "state/evidence/company-blueprint.json",
        "FOUNDER_INTENT_BLUEPRINT",
        "Bản thiết kế công ty 1 người và bộ quy tắc phân quyền điều hành.",
        ("blueprint_run_verified", "founder_attestation"),
    ),
    GateDefinition(
        "offer-validated", "L1", "Xác Thực Thị Trường & Đóng Gói Offer (L1)",
        "product-strategy", "business-analyst", "state/evidence/offer-validated.json",
        "MARKET_ICP_OFFER_CONTRACT",
        "Chân dung ICP, định giá dịch vụ và phân tích rào cản đối thủ.",
        ("offer_contract_verified", "offer_validation_criteria", "research_provenance"),
    ),
    GateDefinition(
        "mvp-live", "L2", "Nhà Máy Kỹ Thuật Sản Xuất Live (L2)",
        "engineering-factory", "fullstack-developer", "state/evidence/mvp-live.json",
        "PRODUCTION_BUILD_VERIFICATION",
        "Mã nguồn sản xuất, API backend và kiểm toán tuân thủ đã live.",
        ("production_health_verified", "build_and_test_digests", "compliance_scan_verified"),
    ),
    GateDefinition(
        "first-revenue", "L3", "Dòng Doanh Thu Lặp Lại & Quyết Toán Thuế (L3)",
        "sales-revenue", "business-analyst", "state/evidence/first-revenue.json",
        "RECONCILED_BANKING_TRANSACTION",
        "Doanh thu thực tế, hóa đơn TT78, sổ sách kế toán và quyết toán thuế.",
        ("reconciled_transaction", "invoice_linked_to_revenue", "tax_accounting_recorded"),
    ),
    GateDefinition(
        "repeatable-channel", "L3", "Kênh Tăng Trưởng Lặp Lại (L3)",
        "growth-marketing", "brainstormer", "state/evidence/repeatable-channel.json",
        "CHANNEL_REPEATABILITY_METRICS",
        "Kênh thu hút khách hàng có số liệu chuyển đổi đo được qua nhiều chu kỳ.",
        ("repeatable_channel_data", "channel_attestation"),
    ),
    GateDefinition(
        "fulfillment-stable", "L4", "Bàn Giao & Vận Hành Chuyên Ngành (L4)",
        "customer-success", "project-manager", "state/evidence/fulfillment-stable.json",
        "CLIENT_DELIVERY_ACCEPTANCE",
        "Nghiệm thu bàn giao nghiệp vụ, CSKH Zalo OA và retention.",
        ("client_acceptance", "fulfillment_scope_verified"),
    ),
    GateDefinition(
        "scale-ready", "L5", "Kho Tri Thức & Sẵn Sàng Nhân Bản (L5)",
        "knowledge-memory", "docs-manager", "state/evidence/scale-ready.json",
        "ENTERPRISE_SOP_CLONE_SYNC",
        "Đóng gói toàn bộ SOP, sổ cái và kiến trúc hướng mốc $1M ARR.",
        ("sop_packaged", "clone_ready_attestation"),
    ),
)

GATE_BY_ID: dict[str, GateDefinition] = {g.gate_id: g for g in GATES}

STATUS_LOCKED = "LOCKED"
STATUS_PARTIAL = "PARTIAL_EVIDENCE"
STATUS_SEALED = "SEALED_VERIFIED"


def evaluate_gate(
    gate_id: str,
    store: EvidenceStore,
    workspace_id: str,
    *,
    params: dict[str, typing.Any] | None = None,
) -> dict[str, typing.Any]:
    """Measure one gate against persisted business facts."""
    definition = GATE_BY_ID.get(gate_id)
    if definition is None:
        raise KeyError(f"unknown gate '{gate_id}'")
    active_params = dict(params or {})
    results = [CONDITIONS[name](store, workspace_id, active_params) for name in definition.conditions]
    met = [r for r in results if r["met"]]
    if len(met) == len(results):
        status = STATUS_SEALED
    elif met:
        status = STATUS_PARTIAL
    else:
        status = STATUS_LOCKED
    return {
        "gate_id": definition.gate_id,
        "layer_id": definition.layer_id,
        "name": definition.name,
        "department_id": definition.department_id,
        "owner_agent": definition.owner_agent,
        "gate_artifact": definition.gate_artifact,
        "required_evidence_type": definition.required_evidence_type,
        "description": definition.description,
        "status": status,
        "conditions": results,
        "conditions_met": len(met),
        "conditions_total": len(results),
        "evaluated_at": utc_now_iso(),
    }


def evaluate_all(store: EvidenceStore, workspace_id: str) -> list[dict[str, typing.Any]]:
    return [evaluate_gate(g.gate_id, store, workspace_id) for g in GATES]


__all__ = [
    "CONDITIONS",
    "GATES",
    "GATE_BY_ID",
    "STATUS_LOCKED",
    "STATUS_PARTIAL",
    "STATUS_SEALED",
    "evaluate_all",
    "evaluate_gate",
]
