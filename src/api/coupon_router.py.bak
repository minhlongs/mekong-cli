"""Coupon/promo code API for Sophia + MekongMind.

Endpoints:
    POST /api/coupons/apply — validate coupon, return discount info
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Coupons"])

# Coupon definitions — add new coupons here
COUPONS: dict[str, dict] = {
    "FREE50": {
        "discount_percent": 100,
        "description": "Free 50 MCU credits on signup",
        "max_uses": 9999,
        "uses": 0,
        "expires": None,
        "projects": ["sophia", "mekongmind"],
    },
    "LAUNCH25": {
        "discount_percent": 25,
        "description": "25% off launch promotion",
        "max_uses": 100,
        "uses": 0,
        "expires": "2026-12-31",
        "projects": ["sophia", "mekongmind"],
    },
}

# Sophia tier pricing (USD/month)
SOPHIA_PRICING = {
    "BASIC": 199,
    "PREMIUM": 399,
    "MASTER": 799,
}


class CouponRequest(BaseModel):
    code: str = Field(..., description="Coupon code")
    tier: str = Field("BASIC", description="Pricing tier")
    project: str = Field("sophia", description="Project: sophia or mekongmind")


class CouponResponse(BaseModel):
    success: bool
    discountPercent: int = 0
    originalPrice: int = 0
    finalPrice: int = 0
    error: str = ""


@router.post("/coupons/apply", response_model=CouponResponse)
async def apply_coupon(req: CouponRequest) -> CouponResponse:
    """Validate coupon code, return discount info."""
    code = req.code.strip().upper()
    coupon = COUPONS.get(code)

    if not coupon:
        return CouponResponse(success=False, error="Mã giảm giá không hợp lệ hoặc đã hết hạn.")

    # Check project
    if req.project not in coupon["projects"]:
        return CouponResponse(success=False, error="Mã không áp dụng cho sản phẩm này.")

    # Check expiry
    if coupon["expires"]:
        exp = datetime.fromisoformat(coupon["expires"]).replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            return CouponResponse(success=False, error="Mã giảm giá đã hết hạn.")

    # Check usage
    if coupon["uses"] >= coupon["max_uses"]:
        return CouponResponse(success=False, error="Mã giảm giá đã hết lượt sử dụng.")

    # Calculate discount
    original = SOPHIA_PRICING.get(req.tier.upper(), 199)
    discount = coupon["discount_percent"]
    final = max(0, int(original * (100 - discount) / 100))

    coupon["uses"] += 1
    logger.info("Coupon %s applied: %s %d%% off → $%d→$%d", code, req.tier, discount, original, final)

    return CouponResponse(
        success=True,
        discountPercent=discount,
        originalPrice=original,
        finalPrice=final,
    )
