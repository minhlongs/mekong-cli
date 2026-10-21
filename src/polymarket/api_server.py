# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CashClaw API server — FastAPI routes for trading signals."""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from src.polymarket.api_models import (
    APIKeyInfo,
    HealthResponse,
    MarketResponse,
    PipelineStatusResponse,
    SignalResponse,
)
from src.polymarket.sdk import Tier, TierLimits

logger = logging.getLogger(__name__)
router = APIRouter(tags=["CashClaw Trading API"])

_rate_limit_store: dict[str, list[float]] = defaultdict(list)

TIER_RATE_LIMITS: dict[str, int] = {
    "starter": 100,
    "pro": 500,
    "elite": 2000,
}


def _resolve_api_key(authorization: str) -> Optional[APIKeyInfo]:
    if not authorization.startswith("Bearer "):
        return None
    token = authorization[7:]
    if not token:
        return None
    return APIKeyInfo(key=token, tier="starter", user_id="dev-user", active=True)


async def require_auth(request: Request) -> APIKeyInfo:
    auth_header = request.headers.get("Authorization", "")
    info = _resolve_api_key(auth_header)
    if info is None or not info.active:
        raise HTTPException(status_code=401, detail="Invalid or missing API key. Get one at cashclaw.io")

    now = time.time()
    window_start = now - 3600
    requests = _rate_limit_store[info.key]
    requests[:] = [t for t in requests if t > window_start]

    limit = TIER_RATE_LIMITS.get(info.tier, 100)
    if len(requests) >= limit:
        raise HTTPException(
            status_code=429, detail=f"Rate limit exceeded ({limit}/hr for {info.tier} tier)", headers={"Retry-After": "60"}
        )
    requests.append(now)
    return info


_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        from src.polymarket.trading_pipeline import PipelineConfig, TradingPipeline
        config = PipelineConfig(
            initial_capital=float(os.getenv("CAPITAL_USDC", "200")),
            paper_trading=os.getenv("PAPER_TRADING", "true").lower() == "true",
            db_path=os.getenv("DATABASE_PATH", "data/algo-trade.db"),
        )
        _pipeline = TradingPipeline(config)
    return _pipeline


@router.get("/v1/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0", timestamp=datetime.utcnow().isoformat())


@router.get("/public/signals")
async def public_signals(request: Request) -> dict:
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    key = f"public:{client_ip}"
    requests = _rate_limit_store[key]
    requests[:] = [t for t in requests if t > now - 60]
    if len(requests) >= 10:
        raise HTTPException(status_code=429, detail="Rate limit: 10 req/min")
    requests.append(now)

    pipeline = _get_pipeline()
    status = pipeline.get_status()
    return {
        "signal_count": 1, "tier": "free", "upgrade_url": "https://cashclaw.io/pricing",
        "pipeline_mode": status["mode"], "note": "Upgrade to Pro for 20 signals/day",
    }


@router.get("/v1/markets")
async def get_markets(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    _get_pipeline()
    return {
        "markets": [], "count": 0, "tier": auth.tier,
        "filters": {"volume": "1K-100K", "resolution": "7-30 days", "exclude_price": True},
    }


@router.get("/v1/predict/{market_id}")
async def predict_market(market_id: str, auth: APIKeyInfo = Depends(require_auth)) -> dict:
    limits = TierLimits.for_tier(Tier(auth.tier))
    return {
        "market_id": market_id, "ensemble_n": limits.ensemble_n, "tier": auth.tier,
        "prediction": None, "note": "Connect Polymarket API for live predictions",
    }


@router.get("/v1/signals")
async def get_signals(limit: int = 10, auth: APIKeyInfo = Depends(require_auth)) -> dict:
    tier_limits = TierLimits.for_tier(Tier(auth.tier))
    max_signals = min(limit, tier_limits.signals_per_day)
    return {"signals": [], "count": 0, "max_signals": max_signals, "tier": auth.tier, "ensemble_n": tier_limits.ensemble_n}


@router.post("/v1/paper/start")
async def paper_start(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    pipeline = _get_pipeline()
    return {"status": "started", "mode": "paper", "capital": pipeline.config.initial_capital}


@router.get("/v1/paper/status")
async def paper_status(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    return _get_pipeline().get_status()


@router.post("/v1/paper/stop")
async def paper_stop(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    pipeline = _get_pipeline()
    pipeline.stop()
    return {"status": "stopped"}


@router.get("/v1/status")
async def pipeline_status(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    return _get_pipeline().get_status()


__all__ = [
    "APIKeyInfo", "HealthResponse", "MarketResponse", "PipelineStatusResponse",
    "SignalResponse", "TIER_RATE_LIMITS", "_get_pipeline", "_rate_limit_store",
    "_resolve_api_key", "get_markets", "get_signals", "health_check",
    "paper_start", "paper_status", "paper_stop", "pipeline_status",
    "predict_market", "public_signals", "require_auth", "router",
]
