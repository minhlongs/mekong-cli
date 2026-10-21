# Mekong CLI — MIT License. Copyright (c) 2026 MekongMind.

"""Enums, audit models, and theme models for the Design Intelligence layer."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductType(StrEnum):
    """Product archetypes supported by `mekong ui` commands."""

    MARKETING_SITE = "marketing-site"
    LANDING_PAGE = "landing-page"
    SAAS_DASHBOARD = "saas-dashboard"
    ADMIN_CONSOLE = "admin-console"
    CRM = "crm"
    ERP = "erp"
    ANALYTICS = "analytics"
    AI_WORKSPACE = "ai-workspace"
    AGENT_CONSOLE = "agent-console"
    TRADING_TERMINAL = "trading-terminal"
    CONTENT_FACTORY = "content-factory"
    ECOMMERCE = "ecommerce"
    MOBILE_APP = "mobile-app"
    DEVELOPER_TOOL = "developer-tool"
    DOCUMENTATION = "documentation"
    INTERNAL_TOOL = "internal-tool"


class Density(StrEnum):
    """Information density stance."""

    SPARSE = "sparse"
    COMFORTABLE = "comfortable"
    COMPACT = "compact"
    DENSE = "dense"


class Genre(StrEnum):
    """Design genre clusters (adapted from Hallmark's 4 genres)."""

    EDITORIAL = "editorial"
    MODERN_MINIMAL = "modern-minimal"
    ATMOSPHERIC = "atmospheric"
    PLAYFUL = "playful"


class EvidenceTier(StrEnum):
    """What evidence backs a finding. Never claim visual without rendering."""

    OBJECTIVE = "objective"
    HEURISTIC = "heuristic"
    OPINION = "opinion"


class VisualQATier(StrEnum):
    """Level of visual evidence available for an audit."""

    FULL = "full"
    SCREENSHOT = "screenshot"
    STATIC = "static"


class AuditFinding(BaseModel):
    """A single audit finding with explicit evidence classification."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(..., min_length=1)
    location: str | None = Field(default=None, description="File/selector if known")
    evidence: EvidenceTier
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Required for heuristic findings",
    )
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")

    @field_validator("confidence")
    @classmethod
    def _heuristic_needs_confidence(cls, v: float | None, info: object) -> float | None:
        data = getattr(info, "data", {})
        if data.get("evidence") == EvidenceTier.HEURISTIC and v is None:
            msg = "heuristic findings must expose a confidence value"
            raise ValueError(msg)
        return v


class AxisScores(BaseModel):
    """Nine scoring axes of the DESIGN SCORE block, each 0-100."""

    model_config = ConfigDict(extra="forbid")

    structure: int = Field(..., ge=0, le=100)
    typography: int = Field(..., ge=0, le=100)
    hierarchy: int = Field(..., ge=0, le=100)
    color: int = Field(..., ge=0, le=100)
    density: int = Field(..., ge=0, le=100)
    interaction: int = Field(..., ge=0, le=100)
    accessibility: int = Field(..., ge=0, le=100)
    distinctiveness: int = Field(..., ge=0, le=100)
    anti_slop: int = Field(..., ge=0, le=100)


class AuditReport(BaseModel):
    """Output of `mekong ui audit` — scores, failures, and evidence tiers."""

    model_config = ConfigDict(extra="forbid")

    target: str = Field(..., min_length=1)
    visual_qa_tier: VisualQATier
    scores: AxisScores
    critical_failures: list[str] = Field(default_factory=list)
    recommended_fixes: list[str] = Field(default_factory=list)
    findings: list[AuditFinding] = Field(default_factory=list)


class Theme(BaseModel):
    """A named theme: palette anchor, fonts, diversification axes."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    genre: Genre
    anchor_color: str = Field(..., min_length=1, description="Named token or color value")
    surface: str | None = Field(default=None, description="Paper/band treatment")
    display_font: str | None = None
    body_font: str | None = None
    diversification_notes: list[str] = Field(
        default_factory=list,
        description="Axes that differ from the last 3 used themes",
    )
