# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Marketplace API — browse and install skills & commands."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.credits import CreditStore
from src.raas.marketplace.license import verify_license_key, verify_purchase
from src.raas.marketplace.payout import monthly_settlement_report
from src.raas.marketplace_router_catalog import (
    _DEFAULT_COMMANDS, _DEFAULT_SKILLS, MarketplaceItem, _get_catalog, _parse_frontmatter, _scan_commands, _scan_skills,
)
from src.raas.marketplace_router_install import (
    _DEFAULT_USER_COMMANDS, _DEFAULT_USER_SKILLS, _deduct_and_install, _install_command, _install_skill,
)

logger = logging.getLogger(__name__)

SKILL_INSTALL_COST = 1
COMMAND_INSTALL_COST = 1
_MARKETPLACE_SKILLS: Path = _DEFAULT_SKILLS
_MARKETPLACE_COMMANDS: Path = _DEFAULT_COMMANDS
_USER_SKILLS: Path = _DEFAULT_USER_SKILLS
_USER_COMMANDS: Path = _DEFAULT_USER_COMMANDS

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


def _filter_items(items: List[MarketplaceItem], q: Optional[str]) -> List[MarketplaceItem]:
    if not q:
        return items
    ql = q.lower()
    return [i for i in items if ql in i.name.lower() or ql in i.description.lower()]


def _paginate(key: str, items: List[MarketplaceItem], limit: int, offset: int) -> Dict[str, Any]:
    return {key: [i.to_dict() for i in items[offset : offset + limit]], "total": len(items), "limit": limit, "offset": offset}


@router.get("/browse")
def browse_marketplace(
    item_type: Optional[str] = Query(None, description="Filter: skill/command"),
    q: Optional[str] = Query(None, description="Search query"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    catalog = _get_catalog()
    raw = (
        catalog["skills"] if item_type == "skill"
        else catalog["commands"] if item_type == "command"
        else catalog["skills"] + catalog["commands"]
    )
    return _paginate("items", _filter_items(raw, q), limit, offset)


@router.get("/skills")
def list_skills(
    q: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    return _paginate("skills", _filter_items(_get_catalog()["skills"], q), limit, offset)


@router.get("/commands")
def list_commands(
    q: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0),
    tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    return _paginate("commands", _filter_items(_get_catalog()["commands"], q), limit, offset)


@router.get("/skills/{name}")
def get_skill_detail(name: str, tenant: TenantContext = Depends(get_tenant_context)) -> Dict[str, Any]:
    skill = next((s for s in _get_catalog()["skills"] if s.name == name), None)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found.")
    return skill.to_dict()


@router.get("/commands/{name}")
def get_command_detail(name: str, tenant: TenantContext = Depends(get_tenant_context)) -> Dict[str, Any]:
    cmd = next((c for c in _get_catalog()["commands"] if c.name == name), None)
    if not cmd:
        raise HTTPException(status_code=404, detail=f"Command '{name}' not found.")
    return cmd.to_dict()


@router.post("/install/skill/{name}")
def install_skill(name: str, tenant: TenantContext = Depends(get_tenant_context)) -> Dict[str, Any]:
    return _deduct_and_install(tenant.tenant_id, "skill", name, SKILL_INSTALL_COST, _install_skill)


@router.post("/install/command/{name}")
def install_command(name: str, tenant: TenantContext = Depends(get_tenant_context)) -> Dict[str, Any]:
    return _deduct_and_install(tenant.tenant_id, "command", name, COMMAND_INSTALL_COST, _install_command)


@router.post("/license/validate")
def validate_plugin_license(
    license_key: str = Query(...), plugin_id: str = Query(...), tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    try:
        return verify_license_key(license_key, plugin_id, tenant.tenant_id)
    except Exception as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/license/verify-purchase")
def verify_plugin_purchase(
    purchase_id: str = Query(...), plugin_id: str = Query(...), amount_cents: int = Query(..., ge=0),
) -> Dict[str, Any]:
    return verify_purchase(purchase_id, plugin_id, amount_cents)


@router.get("/admin/revenue-summary")
def revenue_summary(tenant: TenantContext = Depends(get_tenant_context)) -> Dict[str, Any]:
    return {
        "tenant_id": tenant.tenant_id, "credit_balance": CreditStore().get_balance(tenant.tenant_id),
        "marketplace_installs_today": 0, "revenue_today_cents": 0, "top_plugins": [],
    }


@router.get("/admin/payout-report")
def payout_report(
    plugin_id: Optional[str] = Query(None), tenant: TenantContext = Depends(get_tenant_context),
) -> Dict[str, Any]:
    report = monthly_settlement_report(plugin_id=plugin_id or "all", transactions=[])
    report["tenant_id"] = tenant.tenant_id
    return report


__all__ = [
    "MarketplaceItem", "_MARKETPLACE_COMMANDS", "_MARKETPLACE_SKILLS",
    "_USER_COMMANDS", "_USER_SKILLS", "_get_catalog", "_install_command",
    "_install_skill", "_parse_frontmatter", "_scan_commands", "_scan_skills", "router",
]
