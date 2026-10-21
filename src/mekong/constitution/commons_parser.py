# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""commons_parser.py — Parse ZENOS-COMMONS.md into structured config."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from src.mekong.constitution.commons_extractors import (
    _ALLOCATION_ROW_RE,
    _CONCENTRATION_RE,
    _THRESHOLD_TEXT_RE,
    _TIER_HEADER_RE,
    ContributionFormula,
    ProposalTierSpec,
    TreasuryAllocation,
    _extract_allocations,
    _extract_cap,
    _extract_quorum_floor,
    _extract_status,
    _extract_sunset,
    _extract_tiers,
    _extract_version,
    _normalize_threshold,
    _quorum_from_table,
)


@dataclass
class CommonsConfig:
    """Structured representation of ZENOS-COMMONS.md."""

    source: str
    version: str = "0.1"
    status: str = "proposed"
    tiers: dict[str, ProposalTierSpec] = field(default_factory=dict)
    allocations: list[TreasuryAllocation] = field(default_factory=list)
    anti_concentration_cap: float = 0.25
    member_quorum_floor_transition_members: int = 10
    founder_veto: bool = True
    contribution: ContributionFormula = field(default_factory=ContributionFormula)
    sunset_years: int = 20
    emergency_expiry_days: int = 90
    governance_branches: list[str] = field(
        default_factory=lambda: ["Legislation", "Execution", "Adjudication"]
    )
    parse_warnings: list[str] = field(default_factory=list)

    def tier(self, label: str) -> Optional[ProposalTierSpec]:
        return self.tiers.get(label.upper())


def parse_commons_charter(path: str | Path) -> CommonsConfig:
    """Parse a ZENOS-COMMONS.md charter file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Commons charter not found: {path}")

    text = path.read_text(encoding="utf-8")
    warnings: list[str] = []

    version = _extract_version(text, warnings)
    status = _extract_status(text, warnings)
    tiers = _extract_tiers(text, warnings)
    allocations = _extract_allocations(text, warnings)
    cap = _extract_cap(text, warnings)
    floor = _extract_quorum_floor(text, warnings)
    sunset, emergency = _extract_sunset(text, warnings)

    return CommonsConfig(
        source=str(path),
        version=version,
        status=status,
        tiers=tiers,
        allocations=allocations,
        anti_concentration_cap=cap,
        member_quorum_floor_transition_members=floor,
        sunset_years=sunset,
        emergency_expiry_days=emergency,
        parse_warnings=warnings,
    )


__all__ = [
    "CommonsConfig",
    "ContributionFormula",
    "ProposalTierSpec",
    "TreasuryAllocation",
    "_ALLOCATION_ROW_RE",
    "_CONCENTRATION_RE",
    "_THRESHOLD_TEXT_RE",
    "_TIER_HEADER_RE",
    "_extract_allocations",
    "_extract_cap",
    "_extract_quorum_floor",
    "_extract_status",
    "_extract_sunset",
    "_extract_tiers",
    "_extract_version",
    "_normalize_threshold",
    "_quorum_from_table",
    "parse_commons_charter",
]
