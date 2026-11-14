# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
VN Pricing API Routes — Hiển thị giá VND nội địa cho thị trường Việt Nam.

GET /v1/pricing/vn             → Bảng giá VND + VN SME workflow tiers + services VN (VietQR Napas 247)
GET /v1/pricing/vn/services    → Chỉ danh sách dịch vụ VN
GET /v1/pricing/vn/tier/{key}  → Chi tiết 1 tier VN
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

from src.raas.checkout_router import VN_SME_COMMITMENT_PRICING, VN_SME_WORKFLOW_TIERS

router = APIRouter(prefix="/v1/pricing", tags=["VN Pricing"])

_PRICING_FILE = Path(__file__).resolve().parents[2] / "factory" / "contracts" / "pricing.json"


def _load_pricing() -> dict[str, Any]:
    if not _PRICING_FILE.exists():
        raise HTTPException(status_code=500, detail="pricing.json not found")
    try:
        with _PRICING_FILE.open(encoding="utf-8") as f:
            loaded = json.load(f)
            return dict(loaded) if isinstance(loaded, dict) else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"pricing.json invalid: {exc}") from exc


def _sanitize_vn_product(product: dict[str, Any]) -> dict[str, Any]:
    """Strip legacy foreign gateway/USD fields from domestic VN product cards."""
    cleaned = {
        k: v
        for k, v in product.items()
        if "polar" not in k.lower() and k != "price_usd"
    }
    cleaned["rails"] = ["vietqr"]
    return cleaned


def _build_vn_sme_workflow_tiers() -> list[dict[str, Any]]:
    """Build canonical Section 10.3 VN SME outcome-priced workflow tiers."""
    items: list[dict[str, Any]] = []
    for tier_key, info in VN_SME_WORKFLOW_TIERS.items():
        commitment = VN_SME_COMMITMENT_PRICING.get(tier_key, {})
        items.append(
            {
                "tier": tier_key,
                "price_vnd": info["vnd"],
                "commitment_6m_vnd": commitment.get("commitment_6m_vnd"),
                "setup_fee_vnd": commitment.get("setup_fee_vnd", 0),
                "verified_workflows_per_month": info["workflows"],
                "workflow_quota": info["workflows"],
                "billing_unit": "verified_workflows_per_month",
                "rails": ["vietqr"],
                "checkout_url": f"/v1/checkout?tier={tier_key}",
            }
        )
    return items


@router.get("/vn")
async def get_vn_pricing() -> dict[str, Any]:
    """Bảng giá VND nội địa cho doanh nghiệp Việt Nam thanh toán qua VietQR Napas 247."""
    data = _load_pricing()
    vn_products = data.get("vn_products", {})
    vn_services = data.get("vn_services", [])
    if not vn_products:
        raise HTTPException(status_code=404, detail="VN products chưa cấu hình")
    sanitized_tiers = {
        key: _sanitize_vn_product(val)
        for key, val in vn_products.items()
        if isinstance(val, dict)
    }
    return {
        "currency_display": "VND",
        "currency_billing": "VND",
        "allowed_rails": ["vietqr"],
        "note": "Thanh toán nội địa bằng VND qua chuyển khoản nhanh VietQR Napas 247.",
        "tiers": sanitized_tiers,
        "vn_sme_workflow_tiers": _build_vn_sme_workflow_tiers(),
        "services": vn_services,
    }


@router.get("/vn/services")
async def list_vn_services() -> dict[str, Any]:
    """Danh sách dịch vụ VN-specific với credit cost."""
    data = _load_pricing()
    return {
        "count": len(data.get("vn_services", [])),
        "services": data.get("vn_services", []),
    }


@router.get("/vn/tier/{tier_key}")
async def get_vn_tier(tier_key: str) -> dict[str, Any]:
    """Chi tiết 1 tier VN."""
    data = _load_pricing()
    tier = data.get("vn_products", {}).get(tier_key)
    if isinstance(tier, dict):
        return _sanitize_vn_product(tier)
    for sme_tier in _build_vn_sme_workflow_tiers():
        if sme_tier["tier"] == tier_key:
            return sme_tier
    raise HTTPException(status_code=404, detail=f"Tier '{tier_key}' không tồn tại")


@router.get("/free")
async def get_free_plan() -> dict[str, Any]:
    """Free tier baseline limits."""
    return {
        "plan": "free",
        "currency": "VND",
        "limits": {
            "commands_per_day": 100,
            "concurrent_agents": 1,
            "storage_mb": 500,
        },
    }


@router.get("/paid")
async def get_paid_plan() -> dict[str, Any]:
    """Paid domestic tiers via VietQR Napas 247 (VND)."""
    try:
        data = _load_pricing()
    except HTTPException:
        data = {}
    vn_products = data.get("vn_products", {})
    sanitized = {
        k: _sanitize_vn_product(v)
        for k, v in vn_products.items()
        if isinstance(v, dict)
    }
    return {
        "plan": "paid",
        "currency": "VND",
        "allowed_rails": ["vietqr"],
        "tiers": sanitized,
        "vn_sme_workflow_tiers": _build_vn_sme_workflow_tiers(),
    }


__all__ = ["router"]
