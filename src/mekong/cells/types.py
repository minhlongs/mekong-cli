"""Data types for the AI Cell Runtime Engine.

Defines the core dataclasses that flow through the execution pipeline:
cell configuration, recommendations, and compliance results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CellPrivileges:
    """Access and cost limits for an AI Cell.

    Attributes:
        max_budget: Maximum allowed cost per execution in USD. Zero or negative
            means the cell is disabled.
        requires_approval: When True, the cell's recommendation must be
            explicitly approved before any downstream action is taken.
    """

    max_budget: float = 0.0
    requires_approval: bool = False


@dataclass
class CellBoundaries:
    """Filesystem access boundaries for an AI Cell.

    Attributes:
        read: List of glob patterns for paths the cell is allowed to read.
        write: List of glob patterns for paths the cell is allowed to create
            or modify.
    """

    read: list[str] = field(default_factory=list)
    write: list[str] = field(default_factory=list)


@dataclass
class CellConfig:
    """Complete configuration for a single AI Cell.

    Attributes:
        role: Role identifier (e.g. ``"strategist"``, ``"compliance"``).
        model: LLM model identifier to use for inference (e.g.
            ``"anthropic/claude-sonnet-4"``).
        capabilities: List of capability tags describing what the cell can do.
        privileges: Cost and approval privileges for this cell.
        boundaries: Filesystem read/write boundaries.
        metadata: Optional extensible metadata dict for provider-specific or
            domain-specific extras.
    """

    role: str = ""
    model: str = ""
    capabilities: list[str] = field(default_factory=list)
    privileges: CellPrivileges = field(default_factory=CellPrivileges)
    boundaries: CellBoundaries = field(default_factory=CellBoundaries)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CellRecommendation:
    """Output produced by an AI Cell after execution.

    Attributes:
        recommendation: The text of the recommendation or analysis.
        confidence: Confidence score between 0.0 and 1.0.
        rationale: Explanation of how the cell arrived at the recommendation.
        risk_factors: List of identified risk factors.
        estimated_impact: Qualitative impact estimate (``"low"``, ``"medium"``,
            or ``"high"``).
    """

    recommendation: str = ""
    confidence: float = 0.0
    rationale: str = ""
    risk_factors: list[str] = field(default_factory=list)
    estimated_impact: str = "medium"


@dataclass
class ComplianceResult:
    """Outcome of a constitutional compliance check on a recommendation.

    Attributes:
        verdict: Overall outcome — ``"PASS"``, ``"WARNINGS"``, or ``"FAIL"``.
        checked_articles: List of constitution article numbers that were
            checked against the recommendation.
        violations: List of violation descriptions (FAIL-level findings).
        warnings: List of warning descriptions (WARNING-level findings).
    """

    verdict: str = "PASS"
    checked_articles: list[int] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
