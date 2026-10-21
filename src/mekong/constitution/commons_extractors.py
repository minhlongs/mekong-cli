# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Regex extractors for ZENOS-COMMONS.md charter files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ProposalTierSpec:
    label: str  # "L1" | "L2" | "L3"
    threshold: float  # e.g. 0.666 for 2/3 supermajority
    cooling_days: int
    voting_days: int
    quorum_fraction: float  # fraction of eligible votes required
    scope: str = ""


@dataclass(frozen=True)
class TreasuryAllocation:
    name: str
    fraction: float  # 0–1


@dataclass(frozen=True)
class ContributionFormula:
    base: float = 1.0
    exponent: float = 0.5
    cap_multiplier: float = 5.0
    source: str = "git non-merge commit count"


_TIER_HEADER_RE = re.compile(
    r"^\|\s*\*\*(L\d)\s*[—\-]\s*(.+?)\s*\*\*\s*\|"
    r"\s*(.+?)\s*\|"
    r"\s*(\d+)\s*days?\s*\|"
    r"\s*(\d+)\s*days?\s*\|"
    r"\s*(.+?)\s*\|",
    re.IGNORECASE | re.MULTILINE,
)
_THRESHOLD_TEXT_RE = re.compile(
    r"(?:threshold|supermajority|majority)[^\d]*(\d+)\s*/\s*(\d+)",
    re.IGNORECASE,
)
_ALLOCATION_ROW_RE = re.compile(
    r"^\|\s*([a-z_]+)\s*\|\s*(\d+)\s*%\s*\|",
    re.IGNORECASE | re.MULTILINE,
)
_CONCENTRATION_RE = re.compile(
    r"no single member may control\s*>\s*(\d+)%", re.IGNORECASE
)


def _extract_version(text: str, warnings: list[str]) -> str:
    m = re.search(r"version:\s*([0-9]+\.[0-9]+)", text, re.IGNORECASE)
    if m:
        return m.group(1)
    warnings.append("No version line found — defaulting to 0.1")
    return "0.1"


def _extract_status(text: str, warnings: list[str]) -> str:
    m = re.search(r">\s*\*\*Status:\*\*\s*(\w+)", text)
    if m:
        return m.group(1).lower()
    warnings.append("No status marker found — defaulting to 'draft'")
    return "draft"


def _extract_tiers(
    text: str, warnings: list[str]
) -> dict[str, ProposalTierSpec]:
    tiers: dict[str, ProposalTierSpec] = {}
    for m in _TIER_HEADER_RE.finditer(text):
        label, scope, cooling_s, window_s, quorum_raw = m.groups()
        threshold = _normalize_threshold(quorum_raw)
        if threshold is None:
            warnings.append(
                f"Could not parse threshold for {label} tier from '{quorum_raw}'"
            )
            threshold = 0.5
        tier = ProposalTierSpec(
            label=label.upper(),
            threshold=threshold,
            cooling_days=int(cooling_s),
            voting_days=int(window_s),
            quorum_fraction=_quorum_from_table(quorum_raw),
            scope=scope.strip(),
        )
        tiers[tier.label] = tier
    if not tiers:
        warnings.append("No proposal tier rows found — charter may be malformed")
    return tiers


def _normalize_threshold(raw: str) -> Optional[float]:
    m = re.search(r"(\d+)\s*/\s*(\d+)", raw)
    if m:
        return int(m.group(1)) / max(int(m.group(2)), 1)
    m = re.search(r"(\d+)\s*%", raw)
    if m:
        return int(m.group(1)) / 100.0
    return None


def _quorum_from_table(raw: str) -> float:
    mapping = {
        "2/3 of eligible votes": 2 / 3,
        "1/2 of eligible votes": 1 / 2,
        "1/3 of eligible votes": 1 / 3,
    }
    key = raw.strip().lower()
    for k, v in mapping.items():
        if k in key:
            return v
    return 0.33


def _extract_allocations(
    text: str, warnings: list[str]
) -> list[TreasuryAllocation]:
    seen: dict[str, TreasuryAllocation] = {}
    for m in _ALLOCATION_ROW_RE.finditer(text):
        name, pct = m.groups()
        name = name.strip().lower().replace(" ", "_")
        if name in seen:
            warnings.append(f"Duplicate allocation entry '{name}' — last wins")
        seen[name] = TreasuryAllocation(
            name=name, fraction=int(pct) / 100.0
        )
    out = list(seen.values())
    if not out:
        warnings.append("No allocation rows found — using per-charter defaults may apply")
    return out


def _extract_cap(text: str, warnings: list[str]) -> float:
    m = _CONCENTRATION_RE.search(text)
    if m:
        return int(m.group(1)) / 100.0
    warnings.append("Anti-concentration cap not found in charter — defaulting to 25%")
    return 0.25


def _extract_quorum_floor(text: str, warnings: list[str]) -> int:
    m = re.search(
        r"minimum quorum floor is\s*(\d+)\s+active members", text, re.IGNORECASE
    )
    if m:
        return int(m.group(1))
    warnings.append(
        "Quorum floor transition member count not found — defaulting to 10"
    )
    return 10


def _extract_sunset(text: str, warnings: list[str]) -> tuple[int, int]:
    years = 20
    expiry = 90
    ym = re.search(r"expires\s+(\d+)\s+years", text, re.IGNORECASE)
    if ym:
        years = int(ym.group(1))
    em = re.search(r"auto-expire\s+(\d+)\s+days", text, re.IGNORECASE)
    if em:
        expiry = int(em.group(1))
    return years, expiry
