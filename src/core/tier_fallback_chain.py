"""Mekong CLI — Tier Fallback Chain.

Tier-balanced LLM fallback chain that degrades model selection when a
provider/model pair fails or is blocked by license/tier policy. Mirrors
OmniRoute's Auto-Combo fallback behavior scoped to tier affinity.

Public surface (Phase 2 go-live slice):
- TierFallbackChain — ordered fallback list for a tier
- FallbackCandidate — structured tier-aware model ref
- resolve_tier_chain() — helper returning the chain for a given tier
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Sequence

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FallbackCandidate:
    """One candidate in a tier fallback chain."""

    tier: str
    provider: str
    model: str
    reason: str = ""

    def model_ref(self) -> str:
        """Return colon-separated provider:model ref for ProviderRegistry."""
        return f"{self.provider}:{self.model}"


@dataclass(frozen=True)
class TierFallbackChain:
    """Ordered fallback chain for a billing tier."""

    tier: str
    primary: FallbackCandidate
    fallbacks: Sequence[FallbackCandidate] = field(default_factory=tuple)

    def candidates(self) -> list[FallbackCandidate]:
        """Return ordered candidate list including primary."""
        return [self.primary, *self.fallbacks]

    def select(self, index: int) -> FallbackCandidate:
        """Select candidate by index with bounds safety."""
        candidates = self.candidates()
        if index < 0 or index >= len(candidates):
            raise IndexError(
                f"Tier fallback chain for '{self.tier}' has "
                f"{len(candidates)} candidates; index {index} out of range."
            )
        return candidates[index]


def resolve_tier_chain(tier: str) -> TierFallbackChain:
    """Return a tier fallback chain for known tiers.

    Defaults (MVP slice):
    - BASIC: local/small models -> openai:gpt-4o-mini
    - PREMIUM: mid-tier models -> openai:gpt-4o -> gemini fallback
    - ENTERPRISE: best available -> gemini:gemini-2.5-pro -> openai:gpt-4o
    - MASTER: unrestricted -> reserved for future highest-tier models

    Args:
        tier: Billing tier string (BASIC | PREMIUM | ENTERPRISE | MASTER).

    Returns:
        TierFallbackChain populated with tier-appropriate candidates.

    Raises:
        ValueError: if tier is not recognized.
    """

    if tier == "BASIC":
        return TierFallbackChain(
            tier=tier,
            primary=FallbackCandidate(
                tier=tier, provider="openai", model="gpt-4o-mini", reason="default basic"
            ),
            fallbacks=(
                FallbackCandidate(
                    tier=tier, provider="gemini", model="gemini-1.5-flash", reason="basic fallback"
                ),
            ),
        )

    if tier == "PREMIUM":
        return TierFallbackChain(
            tier=tier,
            primary=FallbackCandidate(
                tier=tier, provider="openai", model="gpt-4o", reason="default premium"
            ),
            fallbacks=(
                FallbackCandidate(
                    tier=tier, provider="gemini", model="gemini-2.0-flash", reason="premium fallback"
                ),
            ),
        )

    if tier == "ENTERPRISE":
        return TierFallbackChain(
            tier=tier,
            primary=FallbackCandidate(
                tier=tier, provider="gemini", model="gemini-2.5-pro", reason="default enterprise"
            ),
            fallbacks=(
                FallbackCandidate(
                    tier=tier, provider="openai", model="gpt-4o", reason="enterprise fallback"
                ),
                FallbackCandidate(
                    tier=tier, provider="openai", model="gpt-4o-mini", reason="enterprise degraded"
                ),
            ),
        )

    if tier == "MASTER":
        return TierFallbackChain(
            tier=tier,
            primary=FallbackCandidate(
                tier=tier, provider="gemini", model="gemini-3-pro-high", reason="default master"
            ),
            fallbacks=(
                FallbackCandidate(
                    tier=tier, provider="gemini", model="gemini-2.5-pro", reason="master fallback"
                ),
                FallbackCandidate(
                    tier=tier, provider="openai", model="gpt-4o", reason="master degraded"
                ),
            ),
        )

    raise ValueError(
        f"Unknown billing tier '{tier}'. "
        "Expected one of: BASIC, PREMIUM, ENTERPRISE, MASTER."
    )


__all__ = [
    "FallbackCandidate",
    "TierFallbackChain",
    "resolve_tier_chain",
]