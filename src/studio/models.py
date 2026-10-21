# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pydantic models for VC Studio Platform entities."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from src.studio.models_enums import (
    CompanyStage, CrossPortfolioInsight, DealStage, ExpertEngagement,
    FiveFactorEvaluation, MomentumLevel, PartyRole, StudioDashboard,
    TerrainType, _now_iso, _short_id,
)


class StudioConfig(BaseModel):
    """Top-level studio configuration."""
    name: str
    thesis_file: str = "thesis.yaml"
    default_equity_pct: float = 30.0
    max_portfolio_size: int = 20
    target_check_size_usd: float = 100000
    currency: str = "USD"
    regions: list[str] = ["global"]
    languages: list[str] = ["en", "vi", "zh"]
    openclaw_model: str = "anthropic/claude-sonnet-4"
    created_at: str = Field(default_factory=_now_iso)


class InvestmentThesis(BaseModel):
    """Investment thesis — filters all deal flow."""
    version: str = "1.0"
    focus_sectors: list[str]
    stage_preference: list[CompanyStage]
    geo_focus: list[str]
    check_size: dict = {"min": 25000, "max": 500000, "sweet_spot": 100000}
    target_ownership_pct: dict = {"min": 15, "max": 40, "target": 30}
    anti_thesis: list[str] = []
    evaluation_weights: dict = {"dao": 0.20, "thien": 0.25, "dia": 0.20, "tuong": 0.20, "phap": 0.15}
    updated_at: str = Field(default_factory=_now_iso)


class PortfolioCompany(BaseModel):
    """A company in the studio portfolio."""
    id: str = Field(default_factory=_short_id)
    slug: str
    name: str
    stage: CompanyStage
    sector: str
    one_liner: str
    founder_id: Optional[str] = None
    founder_name: Optional[str] = None
    equity_pct: float = 30.0
    invested_usd: float = 0
    valuation_usd: Optional[float] = None
    mrr: float = 0
    arr: float = 0
    burn_rate: float = 0
    runway_months: Optional[float] = None
    team_size: int = 1
    openclaw_active: bool = True
    experts_assigned: list[str] = []
    health_score: float = 50.0
    momentum: MomentumLevel = MomentumLevel.STEADY
    five_factor_scores: dict = {}
    tags: list[str] = []
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)


class Deal(BaseModel):
    """Deal in the pipeline."""
    id: str = Field(default_factory=_short_id)
    company_name: str
    sector: str
    stage: DealStage = DealStage.SOURCED
    source: str
    one_liner: str
    founder_name: Optional[str] = None
    founder_email: Optional[str] = None
    ask_usd: Optional[float] = None
    valuation_usd: Optional[float] = None
    thesis_fit_score: Optional[float] = None
    five_factor_scores: dict = {}
    terrain_type: Optional[TerrainType] = None
    momentum: Optional[MomentumLevel] = None
    notes: list[dict] = []
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    pass_reason: Optional[str] = None
    created_at: str = Field(default_factory=_now_iso)
    updated_at: str = Field(default_factory=_now_iso)


class Expert(BaseModel):
    """Expert in the pool."""
    id: str = Field(default_factory=_short_id)
    name: str
    email: str
    specialties: list[str]
    regions: list[str] = ["global"]
    languages: list[str] = ["en"]
    hourly_rate_usd: Optional[float] = None
    equity_open: bool = True
    availability: str = "available"
    rating: float = 0
    engagement_count: int = 0
    bio: str = ""
    portfolio_companies: list[str] = []
    created_at: str = Field(default_factory=_now_iso)


class Founder(BaseModel):
    """Founder in the pool."""
    id: str = Field(default_factory=_short_id)
    name: str
    email: str
    background: str
    skills: list[str]
    sectors_interested: list[str]
    stage_preference: list[CompanyStage] = []
    regions: list[str] = ["global"]
    languages: list[str] = ["en"]
    tuong_score: Optional[dict] = None
    matched_company_id: Optional[str] = None
    status: str = "available"
    created_at: str = Field(default_factory=_now_iso)


__all__ = [
    "DealStage", "CompanyStage", "PartyRole", "TerrainType", "MomentumLevel",
    "StudioConfig", "InvestmentThesis", "PortfolioCompany", "Deal", "Expert",
    "Founder", "ExpertEngagement", "FiveFactorEvaluation",
    "CrossPortfolioInsight", "StudioDashboard",
]
