"""
VN Pricing API Routes — Hiển thị giá VND cho thị trường Việt Nam.

GET /v1/pricing/vn       → 3 tiers VND + services VN
GET /v1/pricing/vn/services → chỉ danh sách dịch vụ VN
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/v1/pricing", tags=["VN Pricing"])

_PRICING_FILE = Path(__file__).resolve().parents[2] / "factory" / "contracts" / "pricing.json"


def _load_pricing() -> dict[str, Any]:
    if not _PRICING_FILE.exists():
        raise HTTPException(status_code=500, detail="pricing.json not found")
    try:
        with _PRICING_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"pricing.json invalid: {exc}") from exc


@router.get("/vn")
async def get_vn_pricing() -> dict[str, Any]:
    """3 tiers VND + services VN. Giá USD billed qua Polar.sh, hiển thị VND."""
    data = _load_pricing()
    vn_products = data.get("vn_products", {})
    vn_services = data.get("vn_services", [])
    if not vn_products:
        raise HTTPException(status_code=404, detail="VN products chưa cấu hình")
    return {
        "currency_display": "VND",
        "currency_billing": "USD",
        "note": "Thanh toán qua Polar.sh bằng USD. Giá VND hiển thị theo tỷ giá tháng.",
        "tiers": vn_products,
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
    if not tier:
        raise HTTPException(status_code=404, detail=f"Tier '{tier_key}' không tồn tại")
    return tier


__all__ = ["router"]

@router.get("/free")
async def get_free_plan() -> dict[str, Any]:
    """Free tier limits (no VND display — always USD baseline)."""
    return {
        "plan": "free",
        "currency": "USD",
        "limits": {
            "commands_per_day": 100,
            "concurrent_agents": 1,
            "storage_mb": 500,
        },
    }


@router.get("/paid")
async def get_paid_plan() -> dict[str, Any]:
    """Paid tiers — priced in USD, billed via Polar."""
    try:
        data = _load_pricing()
    except HTTPException:
        data = {}
    usd_tiers = data.get("usd_products", {})
    return {
        "plan": "paid",
        "currency": "USD",
        "gateway": "polar",
        "tiers": usd_tiers,
    }
