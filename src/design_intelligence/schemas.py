# Mekong CLI — MIT License. Copyright (c) 2026 MekongMind.

"""Pydantic v2 schemas for the Design Intelligence layer.

Covers the four core objects: DesignDNA (~21 axes), DesignBrief, AuditReport,
Theme. Product types span all archetypes the master command requires
(landing pages, SaaS dashboards, admin systems, AI workspaces, agent consoles,
trading terminals, ERP, CRM, content factories, mobile apps, data-heavy apps).

Schema derivation adapted from Hallmark's `study` verb (MIT) — rewritten as
typed data, not copied prompt text.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.design_intelligence.schema_models import (
    AuditFinding,
    AuditReport,
    AxisScores,
    Density,
    EvidenceTier,
    Genre,
    ProductType,
    Theme,
    VisualQATier,
)


class DesignDNA(BaseModel):
    """Reusable design identity extracted by study or built from a brief.

    All optional axes default to None so partial studies (low confidence,
    limited evidence) stay valid; required axes enforce a usable minimum.
    """

    model_config = ConfigDict(extra="forbid")

    # Identity axes
    identity: str = Field(..., min_length=1, description="One-line design identity statement")
    product_type: ProductType
    audience: str = Field(..., min_length=1, description="Who this is designed for")
    brand_character: list[str] = Field(default_factory=list, description="3-6 brand adjectives")

    # Structure axes
    macrostructure: str | None = Field(default=None, description="Named layout fingerprint")
    information_architecture: list[str] = Field(default_factory=list, description="Page/section order")

    # Typography axes
    typography: str | None = Field(default=None, description="Typographic stance")
    type_pairing: dict[str, str] = Field(default_factory=dict, description="role -> family")

    # Color axes
    color_system: str | None = Field(default=None, description="Palette approach (tokens, OKLCH...)")
    color_anchor: str | None = Field(default=None, description="Dominant anchor color")

    # Space & surface axes
    spacing: str | None = Field(default=None, description="Spacing rhythm description")
    density: Density = Density.COMFORTABLE
    surface_treatment: str | None = Field(default=None, description="Cards, borders, shadows stance")

    # Behavior axes
    interaction_language: str | None = Field(default=None)
    motion: str | None = Field(default=None, description="Motion stance, including reduced-motion")
    responsive_behavior: str | None = Field(default=None)

    # Content axes
    imagery: str | None = Field(default=None)
    iconography: str | None = Field(default=None)
    component_archetypes: list[str] = Field(default_factory=list)

    # Guard axes
    accessibility: list[str] = Field(default_factory=list, description="A11y commitments")
    anti_patterns: list[str] = Field(default_factory=list, description="Explicitly avoided patterns")
    inspiration_sources: list[str] = Field(default_factory=list, description="References, never clones")

    # Meta
    confidence: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence 0-1")

    @field_validator("identity", "audience", "macrostructure")
    @classmethod
    def _strip_required_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if stripped == "":
            msg = "value must not be blank"
            raise ValueError(msg)
        return stripped


class DesignBrief(BaseModel):
    """Input brief for `mekong ui build` / pipeline entry."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1)
    product_type: ProductType
    goal: str = Field(..., min_length=1, description="What the product must achieve")
    audience: str = Field(..., min_length=1)
    brand_constraints: list[str] = Field(default_factory=list)
    genre: Genre | None = Field(default=None, description="Inferred or explicit")
    platform: str = Field(default="web", description="web / mobile / desktop / embedded")
    tech_stack: list[str] = Field(default_factory=list)
    design_dna: DesignDNA | None = Field(default=None, description="Seed DNA if available")


__all__ = [
    "AuditFinding",
    "AuditReport",
    "AxisScores",
    "Density",
    "DesignBrief",
    "DesignDNA",
    "EvidenceTier",
    "Genre",
    "ProductType",
    "Theme",
    "VisualQATier",
]
