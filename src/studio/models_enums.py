# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Enums and evaluation/dashboard models for VC Studio Platform."""

from datetime import datetime
from enum import Enum
from typing import Optional
import uuid
from pydantic import BaseModel, Field


def _now_iso() -> str:
    return datetime.now().isoformat()


def _short_id() -> str:
    return str(uuid.uuid4())[:8]


class DealStage(str, Enum):
    SOURCED = "sourced"
    SCREENING = "screening"
    FIRST_MEETING = "first_meeting"
    DILIGENCE = "diligence"
    TERM_SHEET = "term_sheet"
    NEGOTIATION = "negotiation"
    CLOSING = "closing"
    CLOSED = "closed"
    PASSED = "passed"


class CompanyStage(str, Enum):
    IDEA = "idea"
    VALIDATION = "validation"
    MVP = "mvp"
    SEED = "seed"
    SERIES_A = "series_a"
    GROWTH = "growth"
    EXIT = "exit"


class PartyRole(str, Enum):
    VC = "vc"
    EXPERT = "expert"
    FOUNDER = "founder"


class TerrainType(str, Enum):
    """Sun Tzu 6 terrain types for market analysis."""

    ACCESSIBLE = "accessible"
    ENTANGLING = "entangling"
    TEMPORIZING = "temporizing"
    NARROW_PASS = "narrow_pass"
    PRECIPITOUS = "precipitous"
    DISTANT = "distant"


class MomentumLevel(str, Enum):
    SURGING = "surging"
    BUILDING = "building"
    STEADY = "steady"
    FADING = "fading"
    STALLED = "stalled"


class ExpertEngagement(BaseModel):
    """Active expert engagement with a portfolio company."""
    id: str = Field(default_factory=_short_id)
    expert_id: str
    company_id: str
    scope: str
    type: str = "advisory"
    compensation: str = "equity"
    equity_pct: Optional[float] = None
    start_date: str = Field(default_factory=_now_iso)
    end_date: Optional[str] = None
    status: str = "active"
    rating: Optional[float] = None


class FiveFactorEvaluation(BaseModel):
    """道天地將法 — Complete evaluation for a deal or company."""
    target_name: str
    evaluated_at: str = Field(default_factory=_now_iso)
    dao: dict = {}
    thien: dict = {}
    dia: dict = {}
    tuong: dict = {}
    phap: dict = {}
    composite_score: float = 0
    recommendation: str = ""
    confidence: float = 0


class CrossPortfolioInsight(BaseModel):
    """Intelligence derived from cross-portfolio patterns."""
    id: str = Field(default_factory=_short_id)
    type: str
    description: str
    source_companies: list[str]
    applicable_to: list[str]
    confidence: float = 0.5
    status: str = "proposed"
    created_at: str = Field(default_factory=_now_iso)


class StudioDashboard(BaseModel):
    """Studio-wide dashboard data."""
    total_portfolio_companies: int = 0
    active_companies: int = 0
    total_invested_usd: float = 0
    portfolio_value_usd: float = 0
    total_mrr: float = 0
    avg_health_score: float = 0
    deals_in_pipeline: int = 0
    experts_active: int = 0
    founders_available: int = 0
    top_momentum: list[dict] = []
    alerts: list[dict] = []
    cross_portfolio_insights: int = 0


__all__ = [
    "DealStage", "CompanyStage", "PartyRole", "TerrainType", "MomentumLevel",
    "ExpertEngagement", "FiveFactorEvaluation", "CrossPortfolioInsight",
    "StudioDashboard", "_now_iso", "_short_id",
]
