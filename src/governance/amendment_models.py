# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models and exceptions for governance amendments."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from .voting import VotingConfig, VotingResults


class AmendmentStatus(Enum):
    """Status of an amendment through its lifecycle."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEW = "review"
    REJECTED_IN_REVIEW = "rejected_in_review"
    DELIBERATION = "deliberation"
    MONITORING = "monitoring"
    VOTING = "voting"
    PASSED = "passed"
    FAILED = "failed"
    WITHDRAWN = "withdrawn"
    RATIFIED = "ratified"
    IMPLEMENTED = "implemented"


@dataclass
class Amendment:
    """A proposed amendment to governance rules."""

    id: str
    title: str
    description: str
    proposed_text: str
    current_text: str
    proposer_id: str
    co_sponsors: List[str] = field(default_factory=list)
    submitted_at: Optional[datetime] = None
    status: AmendmentStatus = AmendmentStatus.DRAFT

    review_started_at: Optional[datetime] = None
    review_completed_at: Optional[datetime] = None
    deliberation_started_at: Optional[datetime] = None
    deliberation_completed_at: Optional[datetime] = None
    monitoring_started_at: Optional[datetime] = None
    voting_started_at: Optional[datetime] = None
    voting_ended_at: Optional[datetime] = None
    ratified_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None

    review_notes: List[str] = field(default_factory=list)
    feedback: Dict[str, List[str]] = field(default_factory=dict)
    concerns: List[Dict[str, str]] = field(default_factory=list)

    voting_config: Optional[VotingConfig] = None
    voting_results: Optional[VotingResults] = None

    tags: List[str] = field(default_factory=list)
    priority: int = 1
    estimated_impact: str = ""
    requires_quorum: bool = True
    minimum_support_period_hours: int = 48


@dataclass
class AmendmentConfig:
    """Configuration for amendment process."""

    review_hours: int = 24
    deliberation_hours: int = 72
    minimum_monitoring_hours: int = 48
    voting_hours: int = 168

    minimum_co_sponsors: int = 1
    maximum_active_amendments: int = 10
    require_review_approval: bool = True
    allow_withdrawal_after_voting: bool = False

    auto_reject_duplicate: bool = True
    duplicate_similarity_threshold: float = 0.8

    default_voting_threshold: float = 0.6
    default_quorum: float = 0.4


class AmendmentError(Exception):
    """Base exception for amendment errors."""


class StageTransitionError(AmendmentError):
    """Raised when stage transition is invalid."""


class QuorumError(AmendmentError):
    """Raised when quorum requirements fail."""
