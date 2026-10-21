# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models, exceptions, and panel formation helpers for dispute resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DisputeType(Enum):
    """Types of disputes that can be arbitrated."""

    GOVERNANCE_PROCEDURE = "governance_procedure"
    MEMBER_CONDUCT = "member_conduct"
    RESOURCE_ALLOCATION = "resource_allocation"
    AMENDMENT_INTERPRETATION = "amendment_interpretation"
    SANCTIONS_APPEAL = "sanctions_appeal"
    ELECTION_DISPUTE = "election_dispute"


class DisputeStatus(Enum):
    """Status of a dispute."""

    FILED = "filed"
    ACCEPTED = "accepted"
    ARBITRATOR_ASSIGNED = "arbitrator_assigned"
    EVIDENCE_COLLECTION = "evidence_collection"
    HEARING_SCHEDULED = "hearing_scheduled"
    HEARING_HELD = "hearing_held"
    DELIBERATION = "deliberation"
    RULING_ISSUED = "ruling_issued"
    RESOLVED = "resolved"
    CLOSED = "closed"
    WITHDRAWN = "withdrawn"


class RulingType(Enum):
    """Types of rulings."""

    BINDING = "binding"
    RECOMMENDATION = "recommendation"
    DECLARATORY = "declaratory"
    DISMISSED = "dismissed"


@dataclass
class Arbitrator:
    """An arbitrator serving on a panel."""

    id: str
    name: str
    expertise: List[str]
    is_impartial: bool = True
    conflicts_of_interest: List[str] = field(default_factory=list)
    cases_heard: int = 0
    avg_resolution_days: float = 0.0
    is_active: bool = True


@dataclass
class Evidence:
    """Evidence submitted in a dispute."""

    id: str
    dispute_id: str
    submitter_id: str
    evidence_type: str
    description: str
    content_reference: str
    submitted_at: datetime
    is_confidential: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Ruling:
    """Ruling issued by arbitration panel."""

    id: str
    dispute_id: str
    ruling_type: RulingType
    decision: str
    findings: List[str]
    reasoning: str
    issued_at: datetime
    effective_date: datetime
    remedies: List[Dict[str, Any]] = field(default_factory=list)
    dissent: Optional[Dict[str, str]] = None
    appealable: bool = True
    appeal_deadline: Optional[datetime] = None


@dataclass
class Dispute:
    """A formal dispute filed for arbitration."""

    id: str
    dispute_type: DisputeType
    title: str
    description: str
    filing_party: str
    respondent: str
    filed_at: datetime
    status: DisputeStatus = DisputeStatus.FILED
    arbitrators: List[Arbitrator] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    hearing_date: Optional[datetime] = None
    ruling: Optional[Ruling] = None
    related_proposals: List[str] = field(default_factory=list)
    urgency_level: int = 1
    is_confidential: bool = False


@dataclass
class ArbitrationPanel:
    """An arbitration panel assembled for a dispute."""

    id: str
    dispute_id: str
    chair: Arbitrator
    members: List[Arbitrator]
    formed_at: datetime
    quorum_required: int = 3
    decision_method: str = "majority"
    decision_threshold: float = 0.5


class DisputeError(Exception):
    """Base exception for dispute resolution errors."""


class PanelFormationError(DisputeError):
    """Raised when panel cannot be formed."""


class EvidenceError(DisputeError):
    """Raised when evidence submission fails."""


def create_panel_with_expertise_rotation(
    dispute_id: str,
    arbitrators: List[Arbitrator],
    required_expertise: List[str],
    panel_size: int = 3,
) -> ArbitrationPanel:
    """Create panel using expertise-based rotation."""
    scored = []
    for arb in arbitrators:
        score = sum(1 for exp in required_expertise if exp in arb.expertise)
        scored.append((score, arb))

    scored.sort(key=lambda x: (-x[0], x[1].cases_heard))
    selected = [sa[1] for sa in scored[:panel_size]]

    return ArbitrationPanel(
        id=f"PAN-{dispute_id}",
        dispute_id=dispute_id,
        chair=selected[0],
        members=selected,
        formed_at=datetime.utcnow(),
        quorum_required=panel_size // 2 + 1,
    )
