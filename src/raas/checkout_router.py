# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Checkout and license management endpoints for Dual-Rail (VietQR + NOWPayments).

Zero dependencies on api.polar.sh.
Endpoints:
    POST /v1/checkout        — create VietQR Napas 247 or NOWPayments USDT session
    GET  /v1/checkout/status — polling endpoint for checkout status & license key
    POST /v1/license/activate— activate cryptographically signed RAAS_LICENSE_KEY
    GET  /v1/license/status  — inspect active license and credit status
    GET  /v1/success         — backward-compatible post-checkout redirect
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import logging
import os
from pathlib import Path
import secrets
import sqlite3
import uuid
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, EmailStr, Field

from src.core.raas_license_verifier import (
    CanonicalLicenseTier,
    normalize_commercial_tier,
    sign_license_key,
    verify_license_key,
)
from src.core.vietqr_engine import VietQrEngine
from src.raas.credits import CreditStore
from src.raas.tenant import TenantStore

logger = logging.getLogger(__name__)
router = APIRouter()

COMMERCIAL_TIERS: dict[str, dict[str, int]] = {
    "basic": {"usd": 199, "vnd": 4_975_000, "mcu": 1_500},
    "premium": {"usd": 399, "vnd": 9_975_000, "mcu": 4_000},
    "enterprise": {"usd": 799, "vnd": 19_975_000, "mcu": 10_000},
    "master": {"usd": 4999, "vnd": 124_975_000, "mcu": 100_000},
}

VN_SME_WORKFLOW_TIERS: dict[str, dict[str, int]] = {
    "starter": {"vnd": 790_000, "usd": 31, "workflows": 300},
    "pilot_a": {"vnd": 990_000, "usd": 39, "workflows": 500},
    "growth": {"vnd": 1_990_000, "usd": 78, "workflows": 1_000},
    "agency": {"vnd": 4_900_000, "usd": 195, "workflows": 3_500},
}

VN_SME_COMMITMENT_PRICING: dict[str, dict[str, Optional[int]]] = {
    "starter": {"commitment_6m_vnd": 690_000, "setup_fee_vnd": 0},
    "pilot_a": {"commitment_6m_vnd": None, "setup_fee_vnd": 0},
    "growth": {"commitment_6m_vnd": 1_690_000, "setup_fee_vnd": 0},
    "agency": {"commitment_6m_vnd": None, "setup_fee_vnd": 5_000_000},
}


class CheckoutRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier: basic | premium | enterprise | master")
    email: EmailStr = Field(..., description="Customer email")
    rail: str = Field("vietqr", description="Payment rail: vietqr | nowpayments")
    org_id: str = Field("default", description="Organization identifier")
    jurisdiction: Optional[str] = Field(
        None, description="ISO 3166-1 alpha-2 jurisdiction; resolved from the tenant record when omitted"
    )


# Rails a Vietnamese licensee may settle on. Domestic Vietnamese entities
# cannot lawfully hold or settle in crypto, so USDT is never offered to them
# regardless of which rail a client asks for.
_VN_ALLOWED_RAILS = ["vietqr"]
_NON_VN_ALLOWED_RAILS = ["vietqr", "nowpayments"]


def rails_allowed_for_jurisdiction(jurisdiction: str) -> list[str]:
    """Return the payment rails permitted to *jurisdiction*. Fails closed to VN-only on missing/malformed codes."""
    normalised = (jurisdiction or "").strip().upper()
    if len(normalised) != 2 or not normalised.isalpha() or normalised == "VN":
        return list(_VN_ALLOWED_RAILS)
    return list(_NON_VN_ALLOWED_RAILS)


_BOOT_RAAS_DB = os.environ.get("MEKONG_RAAS_DB", "").strip()


def _is_production() -> bool:
    return os.getenv("MEKONG_ENV", "").strip().lower() == "production"


def _get_tenant_store() -> TenantStore:
    env_db = os.environ.get("MEKONG_RAAS_DB", "").strip()
    if env_db and env_db != _BOOT_RAAS_DB:
        return TenantStore(Path(env_db))
    return TenantStore()


def _get_credit_store() -> CreditStore:
    env_db = os.environ.get("MEKONG_RAAS_DB", "").strip()
    if env_db and env_db != _BOOT_RAAS_DB:
        return CreditStore(Path(env_db))
    return CreditStore()


def _normalize_checkout_org_id(raw_org_id: Optional[str], email: str) -> str:
    clean_email = str(email).strip().lower()
    raw_org = (raw_org_id or "").strip()
    if not raw_org:
        return clean_email
    if raw_org.lower() == "default":
        digest = hashlib.sha256(clean_email.encode("utf-8")).hexdigest()[:12]
        return f"org-{digest}"
    return raw_org


def resolve_org_jurisdiction(
    req: CheckoutRequest,
    eff_org_id: Optional[str] = None,
    *,
    authenticated_tenant_id: Optional[str] = None,
) -> str:
    """Resolve authoritative jurisdiction from persisted TenantStore for an authenticated tenant only.

    Caller-supplied ``req.jurisdiction`` and unverified ``req.email`` are never trusted as
    regulatory authority. Unauthenticated, unverified, missing, or ambiguous tenants fail closed
    to ``VN`` so restricted payment rails cannot be unlocked without verified tenant authentication.
    """
    clean_tid = (authenticated_tenant_id or "").strip()
    if not clean_tid or clean_tid.lower() == "default":
        return "VN"
    store = _get_tenant_store()
    persisted = store.get_persisted_jurisdiction(clean_tid)
    return persisted if persisted is not None else "VN"


class JurisdictionUpdateRequest(BaseModel):
    jurisdiction: str = Field(..., description="New ISO 3166-1 alpha-2 jurisdiction code")
    actor_id: str = Field(..., description="Authenticated compliance/admin actor identifier")
    evidence_ref: str = Field(..., description="Supporting KYC/incorporation evidence reference")


class JurisdictionUpdateResponse(BaseModel):
    audit_id: str
    tenant_id: str
    old_jurisdiction: str
    new_jurisdiction: str
    actor_id: str
    evidence_ref: str
    changed_at: str


class CheckoutResponse(BaseModel):
    checkout_url: str
    order_id: str
    tier: str
    rail: str
    amount_usd: int
    amount_vnd: int
    qr_payload: Optional[str] = None
    workflow_quota: Optional[int] = None
    checkout_secret: Optional[str] = None


class CheckoutStatusResponse(BaseModel):
    order_id: str
    status: str
    tier: str
    license_key: Optional[str] = None
    tenant_id: str
    workflow_quota: Optional[int] = None


class LicenseActivateRequest(BaseModel):
    license_key: str = Field(..., description="Signed MEKONG-RAAS-v1 or SOPHIA-RAAS-v1 token")


class LicenseStatusResponse(BaseModel):
    valid: bool
    tier: str
    tenant_id: str
    expires_at: Optional[int] = None
    features: list[str] = Field(default_factory=list)


def _authorize_checkout_status(
    order: Optional[dict],
    x_checkout_secret: Optional[str],
    authorization: Optional[str],
    x_api_key: Optional[str],
) -> tuple[bool, bool]:
    """Return (is_authorized, matched_checkout_secret) for GET /v1/checkout/status."""
    if order is None:
        return (False, False)

    expected_hash = str(order.get("checkout_secret_sha256") or "")
    if x_checkout_secret and x_checkout_secret.strip() and expected_hash:
        candidate_hash = hashlib.sha256(
            x_checkout_secret.strip().encode("utf-8")
        ).hexdigest()
        if hmac.compare_digest(candidate_hash, expected_hash):
            return (True, True)

    api_keys: list[str] = []
    if x_api_key and x_api_key.strip():
        api_keys.append(x_api_key.strip())
    if authorization and authorization.strip().lower().startswith("bearer "):
        bearer_tok = authorization.strip()[7:].strip()
        if bearer_tok:
            api_keys.append(bearer_tok)

    if api_keys:
        store = _get_tenant_store()
        target_org = str(order.get("org_id") or "")
        for key in api_keys:
            tenant = store.get_by_api_key(key)
            if (
                tenant is not None
                and tenant.is_active
                and target_org
                and (tenant.id == target_org or tenant.name == target_org)
            ):
                return (True, False)

    return (False, False)


def _ensure_tenant_for_activation(tenant_store: TenantStore, exact_tenant_id: str) -> str:
    """Atomically resolve or register a TenantStore record bound to exact_tenant_id."""
    conn = sqlite3.connect(str(tenant_store.db_path), timeout=30.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id FROM tenants WHERE id = ? OR name = ? ORDER BY created_at ASC LIMIT 1",
            (exact_tenant_id, exact_tenant_id),
        ).fetchone()
        if row is not None:
            conn.execute("COMMIT")
            return str(row["id"])

        raw_key = f"mk_{secrets.token_hex(16)}"
        key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
        created_at = datetime.now(timezone.utc).isoformat()
        conn.execute(
            "INSERT INTO tenants (id, name, api_key_hash, created_at, is_active, jurisdiction) "
            "VALUES (?, ?, ?, ?, 1, 'VN')",
            (exact_tenant_id, exact_tenant_id, key_hash, created_at),
        )
        conn.execute("COMMIT")
        return exact_tenant_id
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


@router.post("/v1/admin/tenants/{tenant_id}/jurisdiction", response_model=JurisdictionUpdateResponse)
async def admin_update_tenant_jurisdiction(
    tenant_id: str,
    req: JurisdictionUpdateRequest,
    x_admin_secret: Optional[str] = Header(default=None, alias="X-Admin-Secret"),
) -> JurisdictionUpdateResponse:
    """Separately authenticated administrative workflow for updating persisted tenant jurisdiction."""
    configured = os.environ.get("MEKONG_JURISDICTION_ADMIN_SECRET", "").strip()
    if len(configured) < 16:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "jurisdiction_admin_unconfigured",
                "message": "MEKONG_JURISDICTION_ADMIN_SECRET (>= 16 chars) is required for jurisdiction updates.",
            },
        )
    if not x_admin_secret or not hmac.compare_digest(x_admin_secret.strip(), configured):
        raise HTTPException(
            status_code=401,
            detail={"error": "admin_auth_required", "message": "Valid X-Admin-Secret header is required."},
        )
    store = _get_tenant_store()
    try:
        audit = store.update_jurisdiction_admin(
            tenant_id,
            req.jurisdiction,
            actor_id=req.actor_id,
            evidence_ref=req.evidence_ref,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": "tenant_not_found", "message": str(exc)}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "invalid_jurisdiction_update", "message": str(exc)}) from exc
    except (sqlite3.Error, RuntimeError, OSError) as exc:
        raise HTTPException(
            status_code=503,
            detail={"error": "tenant_store_unavailable", "message": "Tenant store unavailable (fail-closed)."},
        ) from exc
    return JurisdictionUpdateResponse(**audit)


@router.post("/v1/checkout", response_model=CheckoutResponse)
async def create_checkout(
    req: CheckoutRequest,
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> CheckoutResponse:
    raw_tier = req.tier.strip().lower()
    order_id = f"mk-{uuid.uuid4().hex[:16]}"
    checkout_secret = f"chk_{secrets.token_urlsafe(24)}"
    checkout_secret_sha256 = hashlib.sha256(checkout_secret.encode("utf-8")).hexdigest()
    clean_email = str(req.email).strip().lower()
    eff_org_id = _normalize_checkout_org_id(req.org_id, clean_email)
    app_base = os.environ.get("APP_BASE_URL", "https://mekongmind.com")
    requested_rail = req.rail.strip().lower()

    # Enforce tenant authentication and prevent cross-tenant checkout / jurisdiction hijacking
    presented_key = (x_api_key or "").strip()
    if not presented_key and authorization and authorization.strip().lower().startswith("bearer "):
        presented_key = authorization.strip()[7:].strip()
    store = _get_tenant_store()
    authenticated_tenant_id: Optional[str] = None
    if presented_key:
        caller_tenant = store.get_by_api_key(presented_key)
        if caller_tenant is None or not caller_tenant.is_active:
            raise HTTPException(
                status_code=401,
                detail={"error": "invalid_tenant_api_key", "message": "Presented tenant API key is invalid or inactive."},
            )
        if eff_org_id not in (caller_tenant.id, caller_tenant.name):
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "cross_tenant_checkout_forbidden",
                    "message": "Authenticated tenant cannot create a checkout session for another tenant.",
                },
            )
        authenticated_tenant_id = caller_tenant.id
        eff_org_id = caller_tenant.id
    elif requested_rail != "nowpayments":
        try:
            exists = store.tenant_exists_by_id_or_name(eff_org_id)
        except (sqlite3.Error, RuntimeError, OSError) as exc:
            logger.error("Tenant store lookup failed during checkout (fail-closed): %s", exc)
            raise HTTPException(
                status_code=503,
                detail={"error": "tenant_store_unavailable", "message": "Tenant store unavailable (fail-closed)."},
            ) from exc
        if exists:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "tenant_auth_required",
                    "message": "Authenticated tenant API key is required to create a checkout session for an existing tenant.",
                },
            )

    jurisdiction = resolve_org_jurisdiction(
        req,
        eff_org_id=eff_org_id,
        authenticated_tenant_id=authenticated_tenant_id,
    )

    if raw_tier in VN_SME_WORKFLOW_TIERS:
        if requested_rail != "vietqr":
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "rail_not_permitted_for_jurisdiction",
                    "message": (
                        f"Domestic VN SME workflow tier '{raw_tier}' settles exclusively via Napas 247 (rail 'vietqr') "
                        "under Decree 52/2024/NĐ-CP."
                    ),
                    "jurisdiction": jurisdiction,
                    "requested_rail": requested_rail,
                    "allowed_rails": list(_VN_ALLOWED_RAILS),
                },
            )
        sme_info = VN_SME_WORKFLOW_TIERS[raw_tier]
        sme_canonical = (
            CanonicalLicenseTier.ENTERPRISE if raw_tier == "agency"
            else (CanonicalLicenseTier.PREMIUM if raw_tier == "growth" else CanonicalLicenseTier.BASIC)
        )
        engine = VietQrEngine()
        engine.create_checkout_order(
            order_id=order_id,
            org_id=eff_org_id,
            customer_email=clean_email,
            expected_amount_vnd=sme_info["vnd"],
            expected_amount_usd=sme_info["usd"],
            currency="VND",
            rail="vietqr",
            display_tier=raw_tier,
            canonical_tier=sme_canonical.value,
            workflow_quota=sme_info["workflows"],
            checkout_secret_sha256=checkout_secret_sha256,
        )
        qr_res = engine.generate_qr(
            amount_vnd=sme_info["vnd"],
            memo=f"MEKONG {eff_org_id} {order_id}",
        )
        return CheckoutResponse(
            checkout_url=str(qr_res.get("quicklink_url", "")),
            order_id=order_id,
            tier=raw_tier,
            rail="vietqr",
            amount_usd=sme_info["usd"],
            amount_vnd=sme_info["vnd"],
            qr_payload=str(qr_res.get("emvco_payload", "")),
            workflow_quota=sme_info["workflows"],
            checkout_secret=checkout_secret,
        )

    canonical_enum = normalize_commercial_tier(req.tier)
    norm_tier = canonical_enum.value.lower()
    tier_info = COMMERCIAL_TIERS.get(norm_tier, COMMERCIAL_TIERS["basic"])
    allowed_rails = rails_allowed_for_jurisdiction(jurisdiction)
    if requested_rail not in allowed_rails:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "rail_not_permitted_for_jurisdiction",
                "message": (
                    f"Rail '{requested_rail}' is not available for jurisdiction '{jurisdiction}'. "
                    "Vietnamese licensees settle domestically via Napas 247 (rail 'vietqr')."
                ),
                "jurisdiction": jurisdiction,
                "requested_rail": requested_rail,
                "allowed_rails": allowed_rails,
            },
        )

    engine = VietQrEngine()
    if requested_rail == "nowpayments":
        engine.create_checkout_order(
            order_id=order_id,
            org_id=eff_org_id,
            customer_email=clean_email,
            expected_amount_vnd=tier_info["vnd"],
            expected_amount_usd=tier_info["usd"],
            currency="USD",
            rail="nowpayments",
            display_tier=canonical_enum.value,
            canonical_tier=canonical_enum.value,
            workflow_quota=None,
            checkout_secret_sha256=checkout_secret_sha256,
        )
        from src.raas.nowpayments_checkout import create_invoice
        try:
            inv = create_invoice(norm_tier, order_id=order_id, customer_email=clean_email,
                                 jurisdiction=jurisdiction)
            checkout_url = inv.get("invoice_url") or f"{app_base}/checkout?order_id={order_id}"
        except Exception:
            checkout_url = f"{app_base}/checkout/nowpayments?order_id={order_id}"
        return CheckoutResponse(
            checkout_url=checkout_url, order_id=order_id, tier=norm_tier,
            rail="nowpayments", amount_usd=tier_info["usd"], amount_vnd=tier_info["vnd"],
            checkout_secret=checkout_secret,
        )

    # Default to VietQR Napas 247
    engine.create_checkout_order(
        order_id=order_id,
        org_id=eff_org_id,
        customer_email=clean_email,
        expected_amount_vnd=tier_info["vnd"],
        expected_amount_usd=tier_info["usd"],
        currency="VND",
        rail="vietqr",
        display_tier=canonical_enum.value,
        canonical_tier=canonical_enum.value,
        workflow_quota=None,
        checkout_secret_sha256=checkout_secret_sha256,
    )
    qr_res = engine.generate_qr(
        amount_vnd=tier_info["vnd"],
        memo=f"MEKONG {eff_org_id} {order_id}",
    )
    return CheckoutResponse(
        checkout_url=str(qr_res.get("quicklink_url", "")), order_id=order_id, tier=norm_tier,
        rail="vietqr", amount_usd=tier_info["usd"], amount_vnd=tier_info["vnd"],
        qr_payload=str(qr_res.get("emvco_payload", "")),
        checkout_secret=checkout_secret,
    )


@router.get("/v1/checkout/status", response_model=CheckoutStatusResponse)
async def get_checkout_status(
    order_id: str,
    simulate_paid: bool = False,
    x_checkout_secret: Optional[str] = Header(default=None, alias="X-Checkout-Secret"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> CheckoutStatusResponse:
    if _is_production() and simulate_paid:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "simulation_forbidden_in_production",
                "message": "Simulated payment settlement is forbidden in production.",
            },
        )

    engine = VietQrEngine()
    order = engine.get_checkout_order(order_id)
    is_authed, matched_secret = _authorize_checkout_status(
        order, x_checkout_secret, authorization, x_api_key
    )
    if not is_authed or order is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized_checkout_status",
                "message": "Valid X-Checkout-Secret or owning tenant API key is required.",
            },
        )

    allow_sim = bool(
        simulate_paid
        and not _is_production()
        and bool(os.getenv("PYTEST_CURRENT_TEST"))
        and matched_secret
    )
    settled = engine.settle_checkout_order_atomic(
        order_id=order_id,
        license_signer=lambda org_id, tier: sign_license_key(tenant_id=org_id, tier=tier),
        allow_test_simulation=allow_sim,
    )
    if settled is None:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized_checkout_status",
                "message": "Valid X-Checkout-Secret or owning tenant API key is required.",
            },
        )

    is_paid = settled.get("payment_state") == "paid" and bool(settled.get("issued_license_key"))
    return CheckoutStatusResponse(
        order_id=str(settled["order_id"]),
        status="paid" if is_paid else "pending",
        tier=str(settled["display_tier"]),
        license_key=str(settled["issued_license_key"]) if is_paid else None,
        tenant_id=str(settled["org_id"]),
        workflow_quota=settled.get("workflow_quota"),
    )


@router.post("/v1/license/activate", response_model=LicenseStatusResponse)
async def activate_license(req: LicenseActivateRequest) -> LicenseStatusResponse:
    res = verify_license_key(req.license_key)
    if not res.valid or not res.tier:
        raise HTTPException(status_code=400, detail={"error": "invalid_license_key", "reason": res.error})
    exact_tenant_id = (res.tenant_id or "").strip()
    if not exact_tenant_id:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_license_key", "reason": "missing_tenant_id"},
        )

    idem_key = f"act_{hashlib.sha256(req.license_key.encode('utf-8')).hexdigest()}"
    tenant_store = _get_tenant_store()
    resolved_tenant_id = _ensure_tenant_for_activation(tenant_store, exact_tenant_id)
    mcu = COMMERCIAL_TIERS.get(res.tier.value.lower(), {}).get("mcu", 1500)
    _get_credit_store().add_credits(
        tenant_id=resolved_tenant_id,
        amount=mcu,
        reason="license_activation",
        idempotency_key=idem_key,
    )
    return LicenseStatusResponse(
        valid=True,
        tier=res.tier.value,
        tenant_id=exact_tenant_id,
        expires_at=res.expires_at,
        features=list(res.features),
    )


@router.get("/v1/license/status", response_model=LicenseStatusResponse)
async def license_status() -> LicenseStatusResponse:
    from src.core.license_manager import get_license_manager
    mgr = get_license_manager()
    lic = mgr.get_license()
    if not lic or mgr.is_valid() is False:
        return LicenseStatusResponse(valid=False, tier="FREE", tenant_id="none", features=["cli:basic"])
    return LicenseStatusResponse(
        valid=True, tier=lic.tier.upper(), tenant_id=lic.tenant_id,
        features=lic.features or ["cli:basic", "cli:cook"],
    )


@router.get("/v1/success")
async def checkout_success(tier: str = "basic", email: str = "") -> dict:
    return {"status": "ok", "message": "Checkout complete. License provisioned via status endpoint."}
