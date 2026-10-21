# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pydantic schemas and models for the CashClaw API."""

from __future__ import annotations

from pydantic import BaseModel


class APIKeyInfo(BaseModel):
    """Resolved API key information."""
    key: str
    tier: str
    user_id: str
    active: bool


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
