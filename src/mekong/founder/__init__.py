"""Founder genome assessment module — types, question sets, scoring, and graph integration.

This module provides the core data structures and algorithms for
assessing founder personality, risk tolerance, values, fears, and
cognitive biases using validated instruments (TIPI-10, Schwartz Values)
and structured self-assessment forms.  Results are stored in the
ZenOS behavior graph for later review and listing.
"""

from __future__ import annotations

from src.mekong.founder.assess import (
    assess_founder,
    genome_to_dict,
    list_founders,
    review_founder,
)
from src.mekong.founder.questions import (
    BIAS_QUESTIONS,
    FEAR_FIELDS,
    FEAR_QUESTIONS,
    RISK_DIMENSIONS,
    RISK_QUESTIONS,
    SCHWARTZ_VALUES,
    TIPI_QUESTIONS,
)
from src.mekong.founder.scoring import (
    BIAS_DIMENSION_MAP,
    classify_risk_level,
    extract_biases,
    score_big_five,
    score_risk,
)
from src.mekong.founder.types import FounderGenome

__all__ = [
    # Types
    "FounderGenome",
    # Question sets
    "TIPI_QUESTIONS",
    "SCHWARTZ_VALUES",
    "FEAR_FIELDS",
    "FEAR_QUESTIONS",
    "RISK_DIMENSIONS",
    "RISK_QUESTIONS",
    "BIAS_QUESTIONS",
    # Scoring
    "score_big_five",
    "score_risk",
    "classify_risk_level",
    "extract_biases",
    "BIAS_DIMENSION_MAP",
    # Assessment orchestration
    "assess_founder",
    "review_founder",
    "list_founders",
    "genome_to_dict",
]
