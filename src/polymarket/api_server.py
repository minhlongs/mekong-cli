"""CashClaw API server — FastAPI routes for trading signals.

Endpoints:
  GET  /v1/health          — health check
  GET  /v1/markets         — scanned market opportunities
  GET  /v1/predict/{id}    — AI prediction for a market
  GET  /v1/signals         — ranked trading signals
  POST /v1/paper/start     — start paper trading
  GET  /v1/paper/status    — paper trading status
  POST /v1/paper/stop      — stop paper trading
  GET  /v1/status          — pipeline status
  GET  /public/signals     — free tier: 1 signal (no auth)
"""

from __future__ import annotations

import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from src.polymarket.sdk import Tier, TierLimits

logger = logging.getLogger(__name__)

router = APIRouter(tags=["CashClaw Trading API"])


# ---------------------------------------------------------------------------
# Auth + Rate Limiting
# ---------------------------------------------------------------------------

# In-memory rate limit tracking (use Redis in production)
_rate_limit_store: dict[str, list[float]] = defaultdict(list)

TIER_RATE_LIMITS: dict[str, int] = {
    "starter": 100,   # 100 req/hr
    "pro": 500,       # 500 req/hr
    "elite": 2000,    # 2000 req/hr
}


class APIKeyInfo(BaseModel):
    """Resolved API key information."""
    key: str
    tier: str
    user_id: str
    active: bool


def _resolve_api_key(authorization: str) -> Optional[APIKeyInfo]:
    """Resolve a Bearer token to API key info.

    In production, validates against Polar.sh subscription database.
    """
    if not authorization.startswith("Bearer "):
        return None

    token = authorization[7:]
    if not token:
        return None

    # TODO: Validate against subscription database
    # For now, accept any non-empty token for development
    return APIKeyInfo(
        key=token,
        tier="starter",
        user_id="dev-user",
        active=True,
    )


async def require_auth(request: Request) -> APIKeyInfo:
    """Dependency: require valid API key."""
    auth_header = request.headers.get("Authorization", "")
    info = _resolve_api_key(auth_header)

    if info is None or not info.active:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Get one at cashclaw.io",
        )

    # Rate limiting
    now = time.time()
    window_start = now - 3600  # 1 hour window
    requests = _rate_limit_store[info.key]
    requests[:] = [t for t in requests if t > window_start]

    limit = TIER_RATE_LIMITS.get(info.tier, 100)
    if len(requests) >= limit:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limit}/hr for {info.tier} tier)",
            headers={"Retry-After": "60"},
        )
    requests.append(now)

    return info


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str = "1.0.0"
    timestamp: str = ""


class MarketResponse(BaseModel):
    """Market data response."""
    market_id: str
    question: str
    volume_24h: float
    days_to_resolution: float
    yes_price: float
    no_price: float


class SignalResponse(BaseModel):
    """Trading signal response."""
    market_id: str
    question: str
    direction: str
    predicted_probability: float
    market_price: float
    edge: float
    confidence: float
    kelly_fraction: float
    position_size_pct: float
    rank: int


class PipelineStatusResponse(BaseModel):
    """Pipeline status response."""
    mode: str
    capital: float
    pnl: float
    trade_count: int
    win_rate: float
    tier: int
    circuit_breaker: str


# ---------------------------------------------------------------------------
# Pipeline singleton (lazy init)
# ---------------------------------------------------------------------------

_pipeline = None


def _get_pipeline():
    """Get or create pipeline singleton."""
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


# ---------------------------------------------------------------------------
# Public Endpoints (no auth)
# ---------------------------------------------------------------------------

@router.get("/v1/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/public/signals")
async def public_signals(request: Request) -> dict:
    """Free tier: 1 top signal, no auth required.

    Rate limited to 10 req/min per IP.
    """
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
        "signal_count": 1,
        "tier": "free",
        "upgrade_url": "https://cashclaw.io/pricing",
        "pipeline_mode": status["mode"],
        "note": "Upgrade to Pro for 20 signals/day",
    }


# ---------------------------------------------------------------------------
# Authenticated Endpoints
# ---------------------------------------------------------------------------

@router.get("/v1/markets")
async def get_markets(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    """Get scanned market opportunities."""
    pipeline = _get_pipeline()
    # Return scanner state (in production, cache scan results)
    return {
        "markets": [],
        "count": 0,
        "tier": auth.tier,
        "filters": {
            "volume": "1K-100K",
            "resolution": "7-30 days",
            "exclude_price": True,
        },
    }


@router.get("/v1/predict/{market_id}")
async def predict_market(
    market_id: str,
    auth: APIKeyInfo = Depends(require_auth),
) -> dict:
    """Get AI prediction for a specific market."""
    limits = TierLimits.for_tier(Tier(auth.tier))

    return {
        "market_id": market_id,
        "ensemble_n": limits.ensemble_n,
        "tier": auth.tier,
        "prediction": None,
        "note": "Connect Polymarket API for live predictions",
    }


@router.get("/v1/signals")
async def get_signals(
    limit: int = 10,
    auth: APIKeyInfo = Depends(require_auth),
) -> dict:
    """Get ranked trading signals (tier-gated)."""
    tier_limits = TierLimits.for_tier(Tier(auth.tier))
    max_signals = min(limit, tier_limits.signals_per_day)

    return {
        "signals": [],
        "count": 0,
        "max_signals": max_signals,
        "tier": auth.tier,
        "ensemble_n": tier_limits.ensemble_n,
    }


@router.post("/v1/paper/start")
async def paper_start(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    """Start paper trading loop."""
    pipeline = _get_pipeline()
    return {
        "status": "started",
        "mode": "paper",
        "capital": pipeline.config.initial_capital,
    }


@router.get("/v1/paper/status")
async def paper_status(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    """Get paper trading status."""
    pipeline = _get_pipeline()
    return pipeline.get_status()


@router.post("/v1/paper/stop")
async def paper_stop(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    """Stop paper trading loop."""
    pipeline = _get_pipeline()
    pipeline.stop()
    return {"status": "stopped"}


@router.get("/v1/status")
async def pipeline_status(auth: APIKeyInfo = Depends(require_auth)) -> dict:
    """Get full pipeline status."""
    pipeline = _get_pipeline()
    return pipeline.get_status()
