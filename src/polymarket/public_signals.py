# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Public signals API — free tier signal endpoint + performance transparency."""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from src.polymarket.public_signals_queries import (
    empty_performance,
    get_calibration_data,
    get_latest_signal,
    get_performance_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["Public (Free Tier)"])

DB_PATH = os.getenv("DATABASE_PATH", "data/algo-trade.db")

_ip_requests: dict[str, list[float]] = defaultdict(list)


def _check_ip_rate_limit(client_ip: str, max_per_min: int = 10) -> None:
    now = time.time()
    requests = _ip_requests[client_ip]
    requests[:] = [t for t in requests if t > now - 60]
    if len(requests) >= max_per_min:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: {max_per_min} requests per minute",
            headers={"Retry-After": "60"},
        )
    requests.append(now)


@router.get("/signals")
async def public_signal(request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    _check_ip_rate_limit(client_ip)

    import src.polymarket.public_signals as _ps

    signal = _ps._get_latest_signal()

    return {
        "signal": signal,
        "tier": "free",
        "signals_shown": 1,
        "upgrade_cta": "Get 20 signals/day with CashClaw Pro ($149/mo)",
        "pricing_url": "https://cashclaw.io/pricing",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/performance")
async def public_performance(request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    _check_ip_rate_limit(client_ip, max_per_min=30)

    import src.polymarket.public_signals as _ps

    perf = _ps._get_performance_summary()
    return {
        "performance": perf,
        "note": "Amounts anonymized. Percentages are real.",
        "updated_at": datetime.utcnow().isoformat(),
    }


@router.get("/calibration")
async def public_calibration(request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    _check_ip_rate_limit(client_ip, max_per_min=30)

    import src.polymarket.public_signals as _ps

    calibration = _ps._get_calibration_data()
    return {
        "calibration": calibration,
        "updated_at": datetime.utcnow().isoformat(),
    }


def _get_latest_signal() -> Optional[dict]:
    import src.polymarket.public_signals as _ps

    return get_latest_signal(_ps.DB_PATH)


def _get_performance_summary() -> dict:
    import src.polymarket.public_signals as _ps

    return get_performance_summary(_ps.DB_PATH)


def _get_calibration_data() -> dict:
    import src.polymarket.public_signals as _ps

    return get_calibration_data(_ps.DB_PATH)


def _empty_performance() -> dict:
    return empty_performance()


__all__ = [
    "DB_PATH", "_check_ip_rate_limit", "_empty_performance",
    "_get_calibration_data", "_get_latest_signal", "_get_performance_summary",
    "_ip_requests", "empty_performance", "get_calibration_data",
    "get_latest_signal", "get_performance_summary", "public_calibration",
    "public_performance", "public_signal", "router",
]
