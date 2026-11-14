"""Multi-tenant isolated SQLite WAL & hashed API-key provisioner (< 1s onboarding)."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.core.vietqr_engine import VietQrEngine
from src.opc.privacy_guard import PilotPrivacyGuard, TenantIsolationError, resolve_tenant_db_path
from src.opc.quota import VN_SME_TIER_WORKFLOW_QUOTAS
from src.opc.state import StateStore
from src.opc.state_graph import SqliteGraphCheckpointer
from src.opc.usage import UsageLedger


@dataclass(frozen=True)
class ProvisionedTenantResult:
    """Result returned once at tenant creation (plaintext tenant_api_key is never persisted)."""

    tenant_id: str
    business_name: str
    owner_name: str
    sme_tier: str
    monthly_workflow_quota: int
    db_path: str
    vietqr_db_path: str
    privacy_db_path: str
    config_path: str
    tenant_api_key: str
    tenant_api_key_sha256: str
    elapsed_ms: float


def provision_isolated_tenant(
    base_dir: str | Path,
    tenant_id: str,
    business_name: str,
    owner_name: str,
    sme_tier: str = "starter",
    bank_id: str = "MB",
    account_no: str = "",
) -> ProvisionedTenantResult:
    """Provision isolated tenant SQLite WAL DBs and SHA-256 hashed API key in < 1 second."""
    t0 = time.monotonic()
    clean_biz = (business_name or "").strip()
    clean_owner = (owner_name or "").strip()
    if not clean_biz or not clean_owner:
        raise ValueError("Both 'business_name' and 'owner_name' must be non-empty.")

    norm_tier = (sme_tier or "starter").strip().lower()
    if norm_tier not in VN_SME_TIER_WORKFLOW_QUOTAS:
        raise ValueError(f"Unsupported sme_tier '{sme_tier}' (expected one of {sorted(VN_SME_TIER_WORKFLOW_QUOTAS)}).")

    db_path = resolve_tenant_db_path(base_dir, tenant_id, active_tenant_id=tenant_id)
    slug = db_path.stem
    tenant_root = db_path.parent
    vietqr_db = (tenant_root / f"{slug}_vietqr.db").resolve()
    privacy_db = (tenant_root / f"{slug}_privacy.db").resolve()
    config_file = (tenant_root / f"{slug}.tenant.json").resolve()
    if vietqr_db.parent != tenant_root or privacy_db.parent != tenant_root or config_file.parent != tenant_root:
        raise TenantIsolationError(f"Path traversal blocked for tenant '{tenant_id}'.")

    StateStore(db_path)
    UsageLedger(db_path)
    SqliteGraphCheckpointer(db_path)
    VietQrEngine(db_path=vietqr_db)
    PilotPrivacyGuard(privacy_db, opc_db_path=db_path)

    raw_api_key = f"mk_opc_{secrets.token_urlsafe(24)}"
    key_sha256 = hashlib.sha256(raw_api_key.encode("utf-8")).hexdigest()
    quota_limit = VN_SME_TIER_WORKFLOW_QUOTAS[norm_tier]
    tenant_cfg: dict[str, Any] = {
        "schema_version": "opc-tenant/v1",
        "tenant_id": slug,
        "business_name": clean_biz,
        "owner_name": clean_owner,
        "sme_tier": norm_tier,
        "monthly_workflow_quota": quota_limit,
        "bank_id": (bank_id or "MB").strip().upper(),
        "account_no": (account_no or "").strip(),
        "db_path": str(db_path),
        "vietqr_db_path": str(vietqr_db),
        "privacy_db_path": str(privacy_db),
        "tenant_api_key_sha256": key_sha256,
        "created_at": int(time.time()),
    }
    config_file.write_text(json.dumps(tenant_cfg, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    elapsed_ms = (time.monotonic() - t0) * 1000.0

    return ProvisionedTenantResult(
        tenant_id=slug,
        business_name=clean_biz,
        owner_name=clean_owner,
        sme_tier=norm_tier,
        monthly_workflow_quota=quota_limit,
        db_path=str(db_path),
        vietqr_db_path=str(vietqr_db),
        privacy_db_path=str(privacy_db),
        config_path=str(config_file),
        tenant_api_key=raw_api_key,
        tenant_api_key_sha256=key_sha256,
        elapsed_ms=round(elapsed_ms, 3),
    )


def verify_tenant_api_key(base_dir: str | Path, tenant_id: str, presented_api_key: str) -> bool:
    """Constant-time verification of a presented tenant API key against stored SHA-256 hash."""
    db_path = resolve_tenant_db_path(base_dir, tenant_id, active_tenant_id=tenant_id)
    cfg_path = db_path.parent / f"{db_path.stem}.tenant.json"
    if not cfg_path.is_file() or not presented_api_key:
        return False
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    expected = str(cfg.get("tenant_api_key_sha256", "")).strip().lower()
    actual = hashlib.sha256(presented_api_key.strip().encode("utf-8")).hexdigest()
    return len(expected) == 64 and hmac.compare_digest(expected, actual)
