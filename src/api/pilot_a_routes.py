"""Production FastAPI HTTP Endpoints for Pilot A (Zalo OA Lead-to-Quote + VietQR + 1-Tap Approval + MISA Draft)."""
from __future__ import annotations

import dataclasses
from decimal import Decimal
import hashlib
import hmac
import json
import os
from pathlib import Path
import sqlite3
import time
from typing import Annotated, Any

from fastapi import APIRouter, Header, HTTPException, Query, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from src.api.pilot_a_card_view import build_owner_notification_cards, render_mobile_approval_card_html
from src.opc.accounting_draft import (
    DRAFT_STATUS_PENDING_TVAN,
    VietQrSettlementConflictError,
    VietQrWebhookError,
    build_accounting_draft_export,
    reconcile_signed_vietqr_webhook,
)
from src.opc.approval import ApprovalSecurityError, compute_action_digest
from src.opc.connectors.zalo_http import (
    ZaloOAConnector,
    ZaloTierPolicyError,
    ZaloWebhookMacError,
    verify_zalo_webhook_mac,
)
from src.opc.dr_backup import PilotAKillSwitchError, enforce_pilot_a_kill_switch
from src.opc.misa_export import DraftExportComplianceError, export_draft_bundle
from src.opc.models import ActionPayload, ApprovalDecision, BusinessProfile, WorkflowStatus
from src.opc.pilot_a import (
    ZALO_INTERACTION_WINDOW_SECONDS,
    ApprovalCard,
    PilotAWorkflow,
    ZaloInteractionWindowError,
    ZaloSandboxConnector,
    ZaloWebhookEvent,
)
from src.opc.privacy_guard import (
    ConsentRequiredError,
    TenantIsolationError,
    redact_vietnamese_pii,
    resolve_tenant_db_path,
)
from src.opc.quarantine import QuarantineViolationError
from src.opc.quota import WorkflowQuotaExceededError
from src.opc.selective_router import extract_deterministic_citations
from src.opc.state_graph import GovernedStateGraph, GraphStage
from src.opc.tenant_provisioner import verify_tenant_api_key

router = APIRouter(prefix="/v1/opc/pilot-a", tags=["OPC Pilot A"])

DEFAULT_PILOT_A_SERVICES: dict[str, Decimal] = {
    "zalo_oa_lead_to_quote": Decimal("600000"),
    "vietqr_reconciliation_setup": Decimal("400000"),
    "misa_sapo_tvan_draft": Decimal("350000"),
    "tu_van_ai": Decimal("600000"),
    "tich_hop_vietqr": Decimal("400000"),
    "architecture_review": Decimal("3750000"),
    "cloud_migration_plan": Decimal("4500000"),
    "security_audit": Decimal("5000000"),
}

ServiceSlug = Annotated[str, Field(min_length=1, max_length=64)]


class PilotAZaloWebhookRequest(BaseModel):
    event_id: str = Field(..., min_length=1, max_length=128)
    oa_id: str = Field("oa_mekong_vn_01", min_length=1, max_length=128)
    sender_id: str = Field(..., min_length=1, max_length=128)
    sender_name: str = Field(..., min_length=1, max_length=200)
    message_text: str = Field(..., min_length=1, max_length=4000)
    timestamp: int | None = None
    last_user_interaction_ts: int | None = None
    requested_services: list[ServiceSlug] = Field(
        default_factory=lambda: ["tu_van_ai", "tich_hop_vietqr"],
        min_length=1,
        max_length=20,
    )
    estimated_hours: int = Field(10, ge=1, le=2000)
    project_title: str = Field("Báo giá dịch vụ Zalo OA & VietQR", min_length=1, max_length=240)
    currency: str = Field("VND", min_length=3, max_length=8)
    language: str = Field("vi", min_length=2, max_length=8)
    extraction_confidence: float | None = Field(None, ge=0.0, le=1.0, allow_inf_nan=False)
    vat_rate_pct: int = Field(8)
    tenant_id: str = Field("default", min_length=2, max_length=63)
    sme_tier: str = Field("pilot_a")
    connector: str = Field("zalo_oa_sandbox")
    oa_tier: str = Field("growth")
    require_consent: bool = False
    grant_consent: bool = False
    runtime_engine: str | None = None
    app_id: str = ""
    service_rates_vnd: dict[str, int] | None = None


class PilotADecideRequest(BaseModel):
    run_id: str = Field(..., min_length=1, max_length=128)
    tenant_id: str = Field("default", min_length=2, max_length=63)
    decision: str = Field("approve", description="approve | reject | revise | handoff")
    action_digest: str = Field(..., min_length=16, max_length=128)
    revision_notes: str = Field("", max_length=1000)
    idempotency_key: str | None = None
    card_sig: str = Field("", max_length=128)


_CARD_CSP = (
    "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
    "connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
)


def _is_public_or_production() -> bool:
    env_name = os.getenv("MEKONG_ENV", "development").strip().lower()
    return (
        env_name in ("production", "staging", "public")
        or os.getenv("MEKONG_PUBLIC_GATEWAY", "").strip() == "1"
    )


def _allow_dev_sandbox_webhook() -> bool:
    return (
        not _is_public_or_production()
        and os.getenv("MEKONG_ALLOW_DEV_SANDBOX_WEBHOOK", "").strip() == "1"
    )


def _no_leak_headers(*, include_card_csp: bool = False) -> dict[str, str]:
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate, private",
        "Pragma": "no-cache",
        "Referrer-Policy": "no-referrer",
        "X-Content-Type-Options": "nosniff",
    }
    if include_card_csp:
        headers["Content-Security-Policy"] = _CARD_CSP
    return headers


def _apply_no_leak_headers(response: Response, *, include_card_csp: bool = False) -> None:
    for header_name, header_value in _no_leak_headers(include_card_csp=include_card_csp).items():
        response.headers[header_name] = header_value


def _pilot_base_dir() -> Path:
    raw = os.getenv("MEKONG_PILOT_A_DB_DIR", "").strip()
    base = Path(raw) if raw else (Path(".mekong") / "pilot_a_tenants")
    base.mkdir(parents=True, exist_ok=True)
    return base.resolve()


def _load_tenant_cfg(base_dir: Path, tenant_id: str) -> dict[str, Any] | None:
    db_path = resolve_tenant_db_path(base_dir, tenant_id, active_tenant_id=tenant_id)
    cfg_path = db_path.parent / f"{db_path.stem}.tenant.json"
    if not cfg_path.is_file():
        return None
    loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
    return dict(loaded) if isinstance(loaded, dict) else None


def _extract_presented_api_key(authorization: str | None, x_api_key: str | None) -> str:
    if x_api_key and x_api_key.strip():
        return x_api_key.strip()
    if authorization and authorization.strip().lower().startswith("bearer "):
        return authorization.strip()[7:].strip()
    return ""


def _resolve_presented_card_sig(x_card_sig: str | None, card_sig: str = "") -> str:
    if x_card_sig is not None and x_card_sig.strip():
        return x_card_sig.strip()
    return card_sig.strip()


def _resolve_approval_secret() -> bytes:
    secret = os.getenv("MEKONG_APPROVAL_SECRET", "").strip()
    if not secret and os.getenv("PYTEST_CURRENT_TEST"):
        secret = "pytest-ephemeral-approval-secret-key"
    secret_bytes = secret.encode("utf-8")
    if len(secret_bytes) < 16:
        raise ApprovalSecurityError("MEKONG_APPROVAL_SECRET (>=16 bytes) required for card signature.")
    return secret_bytes


def _compute_card_sig(tenant_id: str, run_id: str, action_digest: str) -> str:
    secret_bytes = _resolve_approval_secret()
    msg = f"{tenant_id.strip()}:{run_id.strip()}:{action_digest.strip()}".encode("utf-8")
    return hmac.new(secret_bytes, msg, hashlib.sha256).hexdigest()


def _unauthorized_owner_error() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={
            "error": "unauthorized_pilot_a_owner",
            "message": "Valid tenant API key (X-API-Key / Bearer) or signed card token (X-Card-Sig / sig) is required.",
        },
    )


def _prepare_existing_tenant_for_owner_route(
    *,
    tenant_id: str,
    authorization: str | None,
    x_api_key: str | None,
    x_card_sig: str | None = None,
    card_sig: str = "",
) -> tuple[Path, str]:
    """Validate slug, approval secret, credentials, and tenant existence before touching SQLite."""
    base_dir = _pilot_base_dir()
    db_path = resolve_tenant_db_path(base_dir, tenant_id, active_tenant_id=tenant_id)
    _resolve_approval_secret()
    api_key = _extract_presented_api_key(authorization, x_api_key)
    eff_card_sig = _resolve_presented_card_sig(x_card_sig, card_sig)
    if api_key:
        if not verify_tenant_api_key(base_dir, tenant_id, api_key):
            raise _unauthorized_owner_error()
    elif not eff_card_sig:
        raise _unauthorized_owner_error()
    tenant_cfg = _load_tenant_cfg(base_dir, tenant_id)
    if tenant_cfg is None and not db_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "run_not_found", "tenant_id": tenant_id},
        )
    return base_dir, eff_card_sig


def _verify_owner_access(
    *,
    base_dir: Path,
    tenant_id: str,
    run_id: str,
    action_digest: str,
    authorization: str | None,
    x_api_key: str | None,
    x_card_sig: str | None = None,
    card_sig: str = "",
) -> bool:
    """Require valid tenant API key or HMAC card signature (preferring X-Card-Sig header) across all environments."""
    api_key = _extract_presented_api_key(authorization, x_api_key)
    if api_key:
        if verify_tenant_api_key(base_dir, tenant_id, api_key):
            return True
        raise _unauthorized_owner_error()
    presented_sig = _resolve_presented_card_sig(x_card_sig, card_sig)
    if presented_sig and action_digest:
        expected_sig = _compute_card_sig(tenant_id, run_id, action_digest)
        if hmac.compare_digest(expected_sig, presented_sig):
            return True
    raise _unauthorized_owner_error()


def _build_profile(
    tenant_cfg: dict[str, Any] | None = None,
    custom_rates: dict[str, int] | None = None,
) -> BusinessProfile:
    services = dict(DEFAULT_PILOT_A_SERVICES)
    if custom_rates:
        for k, v in custom_rates.items():
            if int(v) < 0:
                raise ValueError(f"Negative rate not allowed for '{k}'.")
            services[str(k)] = Decimal(int(v))
    biz_name = (
        str(tenant_cfg["business_name"])
        if tenant_cfg and tenant_cfg.get("business_name")
        else os.getenv("MEKONG_PILOT_BUSINESS_NAME", "CÔNG TY TNHH MEKONG SME OPS")
    )
    owner_name = (
        str(tenant_cfg["owner_name"])
        if tenant_cfg and tenant_cfg.get("owner_name")
        else os.getenv("MEKONG_PILOT_OWNER_NAME", "Chủ Doanh Nghiệp")
    )
    bank_id = (
        str(tenant_cfg["bank_id"])
        if tenant_cfg and tenant_cfg.get("bank_id")
        else os.getenv("MEKONG_BANK_ID", "MB")
    )
    account_no = (
        str(tenant_cfg["account_no"])
        if tenant_cfg and tenant_cfg.get("account_no")
        else os.getenv("MEKONG_BANK_ACCOUNT_NO", "0988889999")
    )
    return BusinessProfile(
        business_name=biz_name,
        owner_name=owner_name,
        language="vi",
        locale="vi_VN",
        timezone="Asia/Ho_Chi_Minh",
        currency="VND",
        services=services,
        payment_terms="Thanh toán 100% qua chuyển khoản nhanh VietQR Napas 247",
        jurisdiction="VN",
        preferences={"bank_id": bank_id, "account_no": account_no},
    )


def _build_workflow(
    *,
    tenant_id: str = "default",
    sme_tier: str = "pilot_a",
    connector_name: str = "zalo_oa_sandbox",
    oa_tier: str = "growth",
    enforce_consent: bool = False,
    runtime_engine: str | None = None,
    custom_rates: dict[str, int] | None = None,
    require_existing_tenant: bool = True,
    require_webhook_mac: bool | None = None,
) -> tuple[PilotAWorkflow, dict[str, Any] | None]:
    base_dir = _pilot_base_dir()
    db_path = resolve_tenant_db_path(base_dir, tenant_id, active_tenant_id=tenant_id)
    _resolve_approval_secret()
    tenant_cfg = _load_tenant_cfg(base_dir, tenant_id)
    if require_existing_tenant and tenant_cfg is None and not db_path.exists():
        raise TenantIsolationError(f"Tenant '{tenant_id}' is not provisioned.")
    eff_tier = str(tenant_cfg["sme_tier"]) if tenant_cfg and tenant_cfg.get("sme_tier") else sme_tier
    quota_lim = (
        int(tenant_cfg["monthly_workflow_quota"])
        if tenant_cfg and tenant_cfg.get("monthly_workflow_quota") is not None
        else None
    )
    conn: Any = ZaloOAConnector(oa_tier=oa_tier) if connector_name.strip().lower() == "zalo_oa" else ZaloSandboxConnector()
    wf = PilotAWorkflow(
        db_path=None,
        profile=_build_profile(tenant_cfg, custom_rates),
        zalo_connector=conn,
        enforce_consent=enforce_consent or (connector_name.strip().lower() == "zalo_oa"),
        tenant_id=tenant_id,
        tenant_db_dir=base_dir,
        sme_tier=eff_tier,
        workflow_quota_limit=quota_lim,
        require_webhook_mac=require_webhook_mac,
        runtime_engine=runtime_engine,
        handoff_on_low_confidence=True,
    )
    return wf, tenant_cfg


def _reconstruct_action_payload(action_dict: dict[str, Any]) -> ActionPayload:
    return ActionPayload(
        principal=str(action_dict["principal"]),
        capability=str(action_dict["capability"]),
        connector=str(action_dict["connector"]),
        recipient=str(action_dict["recipient"]),
        content=str(action_dict["content"]),
        parameters=dict(action_dict["parameters"]),
        attachments=tuple(action_dict.get("attachments", [])),
        budget_amount=str(action_dict["budget_amount"]),
        budget_currency=str(action_dict["budget_currency"]),
        expires_at=int(action_dict["expires_at"]),
    )


def _lookup_vietqr_bank_tx_id(vietqr_db_path: Path, run_id: str) -> str | None:
    if not vietqr_db_path.exists():
        return None
    with sqlite3.connect(str(vietqr_db_path), timeout=10.0) as conn:
        row = conn.execute(
            "SELECT bank_tx_id FROM transactions WHERE matched_order_id = ? ORDER BY received_at DESC, rowid DESC LIMIT 1",
            (run_id,),
        ).fetchone()
    return str(row[0]) if row and row[0] else None


@router.post("/webhook/zalo")
async def receive_pilot_a_zalo_webhook(
    req: PilotAZaloWebhookRequest,
    request: Request,
    response: Response,
    x_zevent_mac: str | None = Header(default=None, alias="X-ZEvent-Mac"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> dict[str, Any]:
    """Ingest Zalo OA inbound message, run GovernedStateGraph stages 1-4, and emit 1-tap ApprovalCard or Handoff."""
    _apply_no_leak_headers(response)
    try:
        enforce_pilot_a_kill_switch("intake")
    except PilotAKillSwitchError as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "PILOT_A_KILL_SWITCH_ACTIVE", "stage": exc.stage, "message": str(exc)},
        ) from exc
    raw_body = await request.body()
    now_ts = int(req.timestamp) if req.timestamp is not None else int(time.time())
    last_ts = int(req.last_user_interaction_ts) if req.last_user_interaction_ts is not None else (now_ts - 300)
    services = tuple(req.requested_services)
    try:
        base_dir = _pilot_base_dir()
        resolve_tenant_db_path(base_dir, req.tenant_id, active_tenant_id=req.tenant_id)
        presented_key = _extract_presented_api_key(authorization, x_api_key)
        if presented_key and not verify_tenant_api_key(base_dir, req.tenant_id, presented_key):
            raise _unauthorized_owner_error()
        is_owner_authed = bool(presented_key)
        tenant_cfg = _load_tenant_cfg(base_dir, req.tenant_id)

        zalo_secret = os.getenv("ZALO_OA_SECRET_KEY", "").strip()
        has_zalo_secret = bool(zalo_secret)
        allow_unauth_dev_sandbox = (
            not is_owner_authed
            and _allow_dev_sandbox_webhook()
            and tenant_cfg is None
            and req.connector.strip().lower() == "zalo_oa_sandbox"
            and x_zevent_mac is None
            and not has_zalo_secret
        )
        must_enforce_external_mac = not is_owner_authed and not allow_unauth_dev_sandbox
        if not is_owner_authed:
            if (
                req.grant_consent
                or req.service_rates_vnd is not None
                or req.sme_tier.strip().lower() != "pilot_a"
            ):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "privileged_webhook_fields_forbidden",
                        "message": "Tenant API key required for consent, rate, or tier overrides.",
                    },
                )
            if must_enforce_external_mac:
                if not has_zalo_secret:
                    raise HTTPException(
                        status_code=401,
                        detail={
                            "error": "missing_zalo_webhook_secret",
                            "message": "ZALO_OA_SECRET_KEY or owner X-API-Key required.",
                        },
                    )
                if req.timestamp is None or abs(int(time.time()) - now_ts) > 300:
                    raise ZaloWebhookMacError("Zalo OA webhook timestamp missing or outside 300s replay window.")
                if not verify_zalo_webhook_mac(req.app_id, raw_body, now_ts, zalo_secret, x_zevent_mac or ""):
                    raise ZaloWebhookMacError("Zalo OA webhook MAC verification failed (fail-closed).")
                if tenant_cfg is None:
                    raise TenantIsolationError(f"Tenant '{req.tenant_id}' is not provisioned.")
        allow_custom_rates = req.service_rates_vnd if is_owner_authed else None
        allow_grant_consent = bool(req.grant_consent and is_owner_authed)
        eff_sme_tier = req.sme_tier if is_owner_authed else "pilot_a"

        wf, _ = _build_workflow(
            tenant_id=req.tenant_id,
            sme_tier=eff_sme_tier,
            connector_name=req.connector,
            oa_tier=req.oa_tier,
            enforce_consent=req.require_consent,
            runtime_engine=req.runtime_engine,
            custom_rates=allow_custom_rates,
            require_existing_tenant=not allow_unauth_dev_sandbox,
            require_webhook_mac=must_enforce_external_mac,
        )
        if allow_grant_consent:
            wf.privacy_guard.record_subject_consent(req.sender_id)
        event = ZaloWebhookEvent(
            event_id=req.event_id,
            oa_id=req.oa_id,
            sender_id=req.sender_id,
            sender_name=req.sender_name,
            message_text=req.message_text,
            timestamp=now_ts,
            last_user_interaction_ts=last_ts,
            requested_services=services,
            estimated_hours=req.estimated_hours,
            project_title=req.project_title,
            currency=req.currency,
            language=req.language,
            extraction_confidence=req.extraction_confidence,
        )
        outcome = wf.handle_webhook_or_handoff(
            event,
            webhook_mac=(x_zevent_mac or "") if must_enforce_external_mac else None,
            app_id=req.app_id,
            raw_webhook_data=raw_body,
        )
    except HTTPException:
        raise
    except ZaloWebhookMacError as exc:
        raise HTTPException(status_code=401, detail={"error": "invalid_zalo_webhook_mac", "message": str(exc)}) from exc
    except (ConsentRequiredError, ZaloTierPolicyError, ZaloInteractionWindowError, TenantIsolationError) as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except WorkflowQuotaExceededError as exc:
        raise HTTPException(status_code=429, detail={"error": "workflow_quota_exceeded", "message": str(exc)}) from exc
    except QuarantineViolationError as exc:
        raise HTTPException(status_code=422, detail={"error": "quarantine_violation", "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_request", "message": str(exc)}) from exc

    if isinstance(outcome, dict):
        return outcome

    if not isinstance(outcome, ApprovalCard):
        raise HTTPException(status_code=500, detail={"error": "unexpected_outcome_type"})
    digest = outcome.approval_token.action_digest
    base_card_url = f"/v1/opc/pilot-a/card/{outcome.run_id}?tenant_id={req.tenant_id}"
    memo = f"OPC {outcome.run_id}"
    resp_body: dict[str, Any] = {
        "status": "INTERRUPT_AUTHORIZE",
        "workflow_status": WorkflowStatus.PENDING_APPROVAL.value,
        "run_id": outcome.run_id,
        "tenant_id": req.tenant_id,
        "event_id": outcome.event_id,
        "runtime_engine": outcome.runtime_engine,
        "client_name": outcome.client_name,
        "project_title": outcome.project_title,
        "total_amount_vnd": outcome.total_amount_vnd,
        "currency": outcome.currency,
        "vietqr_emvco": outcome.vietqr_emvco,
        "vietqr_quicklink": outcome.vietqr_quicklink,
        "vietqr_memo": memo,
        "action_digest": digest,
        "approval_token_id": outcome.approval_token.token_id,
        "card_url": base_card_url,
        "accounting_draft_status": DRAFT_STATUS_PENDING_TVAN,
        "line_items": list(outcome.line_items),
        "citations": list(outcome.citations),
        "redacted_notes": outcome.redacted_notes,
    }
    if is_owner_authed:
        card_sig = _compute_card_sig(req.tenant_id, outcome.run_id, digest)
        signed_card_url = f"{base_card_url}&sig={card_sig}"
        resp_body["card_sig"] = card_sig
        resp_body["card_url"] = signed_card_url
        resp_body["notification_cards"] = build_owner_notification_cards(
            run_id=outcome.run_id,
            client_name=outcome.client_name,
            project_title=outcome.project_title,
            total_amount_vnd=outcome.total_amount_vnd,
            action_digest=digest,
            card_url=signed_card_url,
            vietqr_memo=memo,
        )
    return resp_body


@router.get("/runs/{run_id}")
async def get_pilot_a_run(
    run_id: str,
    response: Response,
    tenant_id: str = Query("default", min_length=2, max_length=63),
    sig: str = Query("", max_length=128),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_card_sig: str | None = Header(default=None, alias="X-Card-Sig"),
) -> dict[str, Any]:
    """Inspect persisted Pilot A run state, SQLite WAL graph checkpoint, and honest usage summary."""
    _apply_no_leak_headers(response)
    try:
        base_dir, _ = _prepare_existing_tenant_for_owner_route(
            tenant_id=tenant_id,
            authorization=authorization,
            x_api_key=x_api_key,
            x_card_sig=x_card_sig,
            card_sig=sig,
        )
        wf, _ = _build_workflow(tenant_id=tenant_id, require_existing_tenant=True)
    except TenantIsolationError as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc

    run_data = wf.state.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail={"error": "run_not_found", "run_id": run_id})

    action_dict = run_data.get("action_payload") or {}
    digest = compute_action_digest(_reconstruct_action_payload(action_dict)) if action_dict else ""
    _verify_owner_access(
        base_dir=base_dir,
        tenant_id=tenant_id,
        run_id=run_id,
        action_digest=digest,
        authorization=authorization,
        x_api_key=x_api_key,
        x_card_sig=x_card_sig,
        card_sig=sig,
    )
    eff_sig = _compute_card_sig(tenant_id, run_id, digest) if digest else ""
    cp = wf.checkpointer.get(run_id) if wf.checkpointer is not None else None
    costs = wf.usage.aggregate_run_costs(run_id)
    cost_acct = dataclasses.asdict(wf.usage.summarize_cost_accounting(run_id))
    draft_info = run_data.get("proposal_draft") or {}
    return {
        "run_id": run_id,
        "tenant_id": tenant_id,
        "status": run_data["status"].value,
        "payment_state": run_data.get("payment_state", "unpaid"),
        "paid_amount_vnd": run_data.get("paid_amount_vnd", 0),
        "bank_tx_id": run_data.get("bank_tx_id", ""),
        "paid_at": run_data.get("paid_at"),
        "checkpoint_stage": cp.current_stage.value if cp else None,
        "checkpoint_interrupted": cp.interrupted if cp else False,
        "action_digest": digest,
        "card_sig": eff_sig,
        "card_url": f"/v1/opc/pilot-a/card/{run_id}?tenant_id={tenant_id}&sig={eff_sig}" if eff_sig else "",
        "proposal_draft": draft_info,
        "amount_vnd": action_dict.get("parameters", {}).get("amount_vnd", 0),
        "vietqr_emvco": action_dict.get("parameters", {}).get("vietqr_emvco", ""),
        "accounting_draft_status": DRAFT_STATUS_PENDING_TVAN,
        "economics": costs,
        "cost_accounting": cost_acct,
    }


@router.get("/card/{run_id}", response_class=HTMLResponse)
async def get_pilot_a_mobile_card(
    run_id: str,
    tenant_id: str = Query("default", min_length=2, max_length=63),
    sig: str = Query("", max_length=128),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_card_sig: str | None = Header(default=None, alias="X-Card-Sig"),
) -> HTMLResponse:
    """Serve <15KB self-contained Vietnamese mobile HTML approval card for 10-30s shop owner review."""
    try:
        base_dir, _ = _prepare_existing_tenant_for_owner_route(
            tenant_id=tenant_id,
            authorization=authorization,
            x_api_key=x_api_key,
            x_card_sig=x_card_sig,
            card_sig=sig,
        )
        wf, _ = _build_workflow(tenant_id=tenant_id, require_existing_tenant=True)
    except TenantIsolationError as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc

    run_data = wf.state.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail={"error": "run_not_found", "run_id": run_id})

    action_dict = run_data.get("action_payload") or {}
    payload = _reconstruct_action_payload(action_dict)
    digest = compute_action_digest(payload)
    _verify_owner_access(
        base_dir=base_dir,
        tenant_id=tenant_id,
        run_id=run_id,
        action_digest=digest,
        authorization=authorization,
        x_api_key=x_api_key,
        x_card_sig=x_card_sig,
        card_sig=sig,
    )
    eff_sig = _compute_card_sig(tenant_id, run_id, digest)
    params = payload.parameters
    intake = run_data.get("proposal_input") or {}
    draft = run_data.get("proposal_draft") or {}
    now_s = int(time.time())
    last_ts = params.get("last_user_interaction_ts")
    age_s = max(0, now_s - int(last_ts)) if last_ts is not None else max(0, int(params.get("interaction_age_seconds", 0)))
    rem_hours = max(0.0, (ZALO_INTERACTION_WINDOW_SECONDS - age_s) / 3600.0)
    raw_notes = redact_vietnamese_pii(str(intake.get("notes") or payload.content)).redacted_text
    cits = [dataclasses.asdict(c) for c in extract_deterministic_citations(raw_notes, wf.profile.services)[1]]

    html = render_mobile_approval_card_html(
        run_id=run_id,
        status=run_data["status"].value,
        client_name=str(intake.get("client_name", "Khách hàng Zalo OA")),
        project_title=str(params.get("project_title", "Báo giá dịch vụ")),
        customer_notes=raw_notes,
        line_items=list(draft.get("line_items", [])),
        citations=cits,
        total_amount_vnd=int(params.get("amount_vnd", 0)),
        action_digest=digest,
        vietqr_memo=f"OPC {run_id}",
        window_remaining_hours=rem_hours,
        tenant_id=tenant_id,
        card_sig=eff_sig,
    )
    return HTMLResponse(
        content=html,
        status_code=200,
        headers=_no_leak_headers(include_card_csp=True),
    )


@router.post("/decide")
async def decide_pilot_a_run(
    req: PilotADecideRequest,
    response: Response,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_card_sig: str | None = Header(default=None, alias="X-Card-Sig"),
) -> dict[str, Any]:
    """Verify payload_sha256 anti-TOCTOU binding and execute 1-tap approve, reject, revise, or handoff."""
    _apply_no_leak_headers(response)
    norm_dec = req.decision.strip().lower()
    if norm_dec not in ("approve", "reject", "revise", "handoff"):
        raise HTTPException(status_code=400, detail={"error": "invalid_decision", "decision": req.decision})
    if norm_dec == "approve":
        try:
            enforce_pilot_a_kill_switch("dispatch")
        except PilotAKillSwitchError as exc:
            raise HTTPException(
                status_code=503,
                detail={"error": "PILOT_A_KILL_SWITCH_ACTIVE", "stage": exc.stage, "message": str(exc)},
            ) from exc
    try:
        base_dir, _ = _prepare_existing_tenant_for_owner_route(
            tenant_id=req.tenant_id,
            authorization=authorization,
            x_api_key=x_api_key,
            x_card_sig=x_card_sig,
            card_sig=req.card_sig,
        )
        wf_probe, _ = _build_workflow(tenant_id=req.tenant_id, require_existing_tenant=True)
    except TenantIsolationError as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc

    run_data = wf_probe.state.get_run(req.run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail={"error": "run_not_found", "run_id": req.run_id})
    action_dict = run_data.get("action_payload")
    if not action_dict:
        raise HTTPException(status_code=409, detail={"error": "missing_action_payload", "run_id": req.run_id})

    payload = _reconstruct_action_payload(action_dict)
    expected_digest = compute_action_digest(payload)
    _verify_owner_access(
        base_dir=base_dir,
        tenant_id=req.tenant_id,
        run_id=req.run_id,
        action_digest=expected_digest,
        authorization=authorization,
        x_api_key=x_api_key,
        x_card_sig=x_card_sig,
        card_sig=req.card_sig,
    )
    if not hmac.compare_digest(expected_digest, req.action_digest.strip()):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "tamper_detected_digest_mismatch",
                "message": "Action digest does not match persisted payload_sha256 (TOCTOU blocked).",
            },
        )

    try:
        wf, _ = _build_workflow(
            tenant_id=req.tenant_id,
            connector_name=payload.connector,
            require_existing_tenant=True,
        )
    except (ZaloTierPolicyError, TenantIsolationError) as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc

    cur_status: WorkflowStatus = run_data["status"]
    cp_cur = wf.checkpointer.get(req.run_id) if wf.checkpointer is not None else None
    if cp_cur is not None and cp_cur.current_stage == GraphStage.HANDOFF_ZALO_OA_MANAGER and norm_dec == "approve":
        raise HTTPException(status_code=409, detail={"error": "run_already_handed_off", "run_id": req.run_id})

    if norm_dec in ("handoff", "reject", "revise"):
        if cur_status not in (WorkflowStatus.PENDING_APPROVAL, WorkflowStatus.REVISE_REQUESTED):
            raise HTTPException(
                status_code=409,
                detail={"error": "invalid_run_state_transition", "current_status": cur_status.value},
            )
        if norm_dec == "handoff":
            wf.state.save_run(
                req.run_id,
                run_data["pack_id"],
                WorkflowStatus.REJECTED,
                run_data["business_profile"],
                run_data["proposal_input"],
                int(time.time()),
                run_data.get("proposal_draft"),
                action_dict,
            )
            if wf.checkpointer is not None:
                wf.checkpointer.put(
                    req.run_id,
                    GraphStage.HANDOFF_ZALO_OA_MANAGER,
                    {"run_id": req.run_id, "notes": redact_vietnamese_pii(req.revision_notes).redacted_text},
                    interrupted=False,
                    payload_sha256=expected_digest,
                )
            return {
                "run_id": req.run_id,
                "status": GraphStage.HANDOFF_ZALO_OA_MANAGER.value,
                "handoff_status": GraphStage.HANDOFF_ZALO_OA_MANAGER.value,
                "action_digest": expected_digest,
            }

        dec_enum = ApprovalDecision.REJECT if norm_dec == "reject" else ApprovalDecision.REVISE
        tok = wf.engine.approval_engine.issue_token(req.run_id, payload, decision=dec_enum, revision_notes=req.revision_notes)
        wf.state.save_approval(tok)
        new_st = WorkflowStatus.REJECTED if norm_dec == "reject" else WorkflowStatus.REVISE_REQUESTED
        wf.state.save_run(
            req.run_id,
            run_data["pack_id"],
            new_st,
            run_data["business_profile"],
            run_data["proposal_input"],
            int(tok.created_at),
            run_data.get("proposal_draft"),
            action_dict,
        )
        return {"run_id": req.run_id, "status": new_st.value, "action_digest": expected_digest}

    if cur_status == WorkflowStatus.REJECTED:
        raise HTTPException(status_code=409, detail={"error": "run_already_rejected", "run_id": req.run_id})
    if cur_status in (WorkflowStatus.FAILED, WorkflowStatus.RECONCILIATION_REQUIRED):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "run_requires_reconciliation_or_failed",
                "run_id": req.run_id,
                "current_status": cur_status.value,
            },
        )
    if cur_status == WorkflowStatus.COMPLETED:
        return {
            "run_id": req.run_id,
            "status": "deduplicated",
            "workflow_status": WorkflowStatus.COMPLETED.value,
            "side_effect_deduplicated": True,
            "action_digest": expected_digest,
        }

    now_s = int(time.time())
    last_ts = payload.parameters.get("last_user_interaction_ts")
    if last_ts is not None:
        live_age = now_s - int(last_ts)
        if live_age < 0 or live_age > ZALO_INTERACTION_WINDOW_SECONDS:
            raise HTTPException(
                status_code=403,
                detail={"error": "ZaloInteractionWindowError", "message": f"Zalo OA 48h window expired (age={live_age}s)."},
            )

    idem_key = req.idempotency_key or f"pilot_a_{req.run_id}"
    tok_approve = wf.engine.approval_engine.issue_token(req.run_id, payload, decision=ApprovalDecision.APPROVE)
    wf.state.save_approval(tok_approve)
    try:
        if wf.checkpointer is not None and wf.checkpointer.get(req.run_id) is not None:
            graph = GovernedStateGraph(wf.checkpointer)
            cp_done = graph.resume(
                req.run_id,
                tok_approve.token_id,
                expected_digest,
                commit_fn=lambda _st: wf.engine.execute_approved_action(
                    tok_approve, payload, idempotency_key=idem_key, now=now_s
                ),
            )
            dedup = bool(cp_done.state.get("side_effect_deduplicated", False))
            commit_res = dict(cp_done.state.get("commit_result") or {})
            raw_commit_status = str(commit_res.get("status", "completed"))
            out_status = "deduplicated" if (dedup and raw_commit_status in ("completed", "deduplicated")) else raw_commit_status
        else:
            commit_res = wf.engine.execute_approved_action(tok_approve, payload, idempotency_key=idem_key, now=now_s)
            out_status = str(commit_res.get("status", "completed"))
            dedup = out_status == "deduplicated"
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=409, detail={"error": "approval_security_error", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "connector_dispatch_error", "message": str(exc)}) from exc

    if out_status == "in_flight":
        raise HTTPException(status_code=409, detail={"error": "action_in_flight", "run_id": req.run_id})

    final_wf_status = (
        WorkflowStatus.COMPLETED
        if out_status in ("completed", "deduplicated")
        else (
            WorkflowStatus.RECONCILIATION_REQUIRED
            if out_status == "reconciliation_required"
            else WorkflowStatus.FAILED
        )
    )
    wf.state.save_run(
        req.run_id,
        run_data["pack_id"],
        final_wf_status,
        run_data["business_profile"],
        run_data["proposal_input"],
        now_s,
        run_data.get("proposal_draft"),
        action_dict,
    )
    return {
        "run_id": req.run_id,
        "status": out_status,
        "workflow_status": final_wf_status.value,
        "side_effect_deduplicated": dedup,
        "action_digest": expected_digest,
    }


@router.post("/webhook/vietqr")
async def reconcile_pilot_a_vietqr_webhook(
    request: Request,
    response: Response,
    run_id: str = Query(..., min_length=1, max_length=128),
    tenant_id: str = Query("default", min_length=2, max_length=63),
    vat_rate_pct: int = Query(8),
    target_provider: str = Query("misa_meinvoice"),
    x_vietqr_signature: str = Header(..., alias="X-VietQR-Signature"),
) -> dict[str, Any]:
    """Verify HMAC-SHA256 bank webhook, prevent cross-order replay, and emit DRAFT_PENDING_TVAN draft."""
    _apply_no_leak_headers(response)
    secret = os.getenv("VIETQR_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise HTTPException(status_code=503, detail={"error": "missing_vietqr_webhook_secret"})
    raw_body = await request.body()
    expected_sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    if not x_vietqr_signature or not hmac.compare_digest(expected_sig.lower(), x_vietqr_signature.strip().lower()):
        raise HTTPException(
            status_code=403,
            detail={"error": "vietqr_webhook_rejected", "message": "Invalid VietQR webhook HMAC-SHA256 signature (fail-closed)."},
        )
    try:
        base_dir = _pilot_base_dir()
        db_path = resolve_tenant_db_path(base_dir, tenant_id, active_tenant_id=tenant_id)
        _resolve_approval_secret()
        tenant_cfg = _load_tenant_cfg(base_dir, tenant_id)
        if tenant_cfg is None and not _allow_dev_sandbox_webhook():
            raise TenantIsolationError(f"Tenant '{tenant_id}' is not provisioned.")
        if tenant_cfg is None and not db_path.exists():
            raise HTTPException(status_code=404, detail={"error": "run_not_found", "run_id": run_id})
        wf, _ = _build_workflow(tenant_id=tenant_id, require_existing_tenant=True)
    except TenantIsolationError as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc

    run_data = wf.state.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail={"error": "run_not_found", "run_id": run_id})
    action_dict = run_data.get("action_payload") or {}
    params = action_dict.get("parameters", {})
    expected_vnd = int(params.get("amount_vnd", 0))
    draft_info = run_data.get("proposal_draft") or {}
    subtotal_vnd = int(params.get("subtotal_vnd", draft_info.get("subtotal_vnd", expected_vnd)))
    eff_vat_pct = int(params.get("vat_rate_pct", draft_info.get("vat_rate_pct", vat_rate_pct)))
    intake_info = run_data.get("proposal_input") or {}
    try:
        recon = reconcile_signed_vietqr_webhook(wf.vietqr, raw_body, x_vietqr_signature, secret, run_id, expected_vnd)
        wf.state.record_run_payment(run_id, recon["bank_tx_id"], int(recon["amount_vnd"]))
        acc_draft = build_accounting_draft_export(
            run_id,
            str(intake_info.get("client_name", "Khách hàng SME")),
            list(draft_info.get("line_items", [])),
            subtotal_vnd,
            vat_rate_pct=eff_vat_pct,
            target_provider=target_provider,
            bank_tx_id=recon["bank_tx_id"],
            settled_amount_vnd=recon["amount_vnd"],
        )
    except VietQrSettlementConflictError as exc:
        raise HTTPException(status_code=409, detail={"error": "vietqr_settlement_conflict", "message": str(exc)}) from exc
    except VietQrWebhookError as exc:
        raise HTTPException(status_code=403, detail={"error": "vietqr_webhook_rejected", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "invalid_draft_parameters", "message": str(exc)}) from exc

    return {
        "reconciliation": recon,
        "accounting_draft": dataclasses.asdict(acc_draft),
    }


@router.get("/draft-export/{run_id}")
async def export_pilot_a_misa_sapo_draft(
    run_id: str,
    fmt: str = Query("json", description="json | csv | xml"),
    tenant_id: str = Query("default", min_length=2, max_length=63),
    vat_rate_pct: int = Query(8),
    target_provider: str = Query("misa_meinvoice"),
    sig: str = Query("", max_length=128),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    x_card_sig: str | None = Header(default=None, alias="X-Card-Sig"),
) -> PlainTextResponse:
    """Export uncertified DRAFT_PENDING_TVAN pre-accounting file (CSV, XML, or JSON) for MISA / Sapo."""
    try:
        base_dir, _ = _prepare_existing_tenant_for_owner_route(
            tenant_id=tenant_id,
            authorization=authorization,
            x_api_key=x_api_key,
            x_card_sig=x_card_sig,
            card_sig=sig,
        )
        wf, _ = _build_workflow(tenant_id=tenant_id, require_existing_tenant=True)
    except TenantIsolationError as exc:
        raise HTTPException(status_code=403, detail={"error": type(exc).__name__, "message": str(exc)}) from exc
    except ApprovalSecurityError as exc:
        raise HTTPException(status_code=503, detail={"error": "approval_security_error", "message": str(exc)}) from exc

    run_data = wf.state.get_run(run_id)
    if not run_data:
        raise HTTPException(status_code=404, detail={"error": "run_not_found", "run_id": run_id})

    action_dict = run_data.get("action_payload") or {}
    digest = compute_action_digest(_reconstruct_action_payload(action_dict)) if action_dict else ""
    _verify_owner_access(
        base_dir=base_dir,
        tenant_id=tenant_id,
        run_id=run_id,
        action_digest=digest,
        authorization=authorization,
        x_api_key=x_api_key,
        x_card_sig=x_card_sig,
        card_sig=sig,
    )
    params = action_dict.get("parameters", {})
    expected_vnd = int(params.get("amount_vnd", 0))
    draft_info = run_data.get("proposal_draft") or {}
    subtotal_vnd = int(params.get("subtotal_vnd", draft_info.get("subtotal_vnd", expected_vnd)))
    eff_vat_pct = int(params.get("vat_rate_pct", draft_info.get("vat_rate_pct", vat_rate_pct)))
    intake_info = run_data.get("proposal_input") or {}
    bank_tx_id = _lookup_vietqr_bank_tx_id(wf.vietqr.db_path, run_id)
    try:
        acc_draft = build_accounting_draft_export(
            run_id,
            str(intake_info.get("client_name", "Khách hàng SME")),
            list(draft_info.get("line_items", [])),
            subtotal_vnd,
            vat_rate_pct=eff_vat_pct,
            target_provider=target_provider,
            bank_tx_id=bank_tx_id,
            settled_amount_vnd=expected_vnd if expected_vnd > 0 else None,
        )
        serialized = export_draft_bundle(acc_draft, fmt=fmt)
    except (DraftExportComplianceError, ValueError) as exc:
        raise HTTPException(status_code=400, detail={"error": "draft_export_error", "message": str(exc)}) from exc

    media_map = {
        "csv": "text/csv; charset=utf-8",
        "xml": "application/xml; charset=utf-8",
        "json": "application/json; charset=utf-8",
    }
    norm_fmt = fmt.strip().lower()
    return PlainTextResponse(
        content=serialized,
        media_type=media_map.get(norm_fmt, "text/plain; charset=utf-8"),
        headers=_no_leak_headers(),
    )


__all__ = ["router"]
