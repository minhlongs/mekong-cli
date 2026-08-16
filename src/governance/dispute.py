# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Dispute resolution module — Arbitration panel for governance conflicts.

Implements Ostrom principle #6: Conflict resolution mechanisms

Features:
- Arbitration panel formation (3-5 impartial arbitrators)
- Evidence submission and review
- Hearing procedures
- Binding and non-binding rulings
- Appeal mechanisms
- Transparency and audit trail
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DisputeType(Enum):
    """Types of disputes that can be arbitrated"""

    GOVERNANCE_PROCEDURE = "governance_procedure"  # Challenge to process
    MEMBER_CONDUCT = "member_conduct"  # Alleged violation or unfair treatment
    RESOURCE_ALLOCATION = "resource_allocation"  # Dispute over resource distribution
    AMENDMENT_INTERPRETATION = "amendment_interpretation"  # Constitution/bylaw interpretation
    SANCTIONS_APPEAL = "sanctions_appeal"  # Appeal of sanction
    ELECTION_DISPUTE = "election_dispute"  # Challenge to election outcome


class DisputeStatus(Enum):
    """Status of a dispute"""

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
    """Types of rulings"""

    BINDING = "binding"  # Must be followed
    RECOMMENDATION = "recommendation"  # Advisory only
    DECLARATORY = "declaratory"  # Interpretation without order
    DISMISSED = "dismissed"  # Dismissed without merit finding


@dataclass
class Arbitrator:
    """An arbitrator serving on a panel"""

    id: str
    name: str
    expertise: List[str]  # e.g., ["governance", "law", "conflict_resolution"]
    is_impartial: bool = True
    conflicts_of_interest: List[str] = field(default_factory=list)
    cases_heard: int = 0
    avg_resolution_days: float = 0.0
    is_active: bool = True


@dataclass
class Evidence:
    """Evidence submitted in a dispute"""

    id: str
    dispute_id: str
    submitter_id: str
    evidence_type: str  # "document", "testimony", "data", "expert_report"
    description: str
    content_reference: str  # Reference to actual evidence (file, statement, etc.)
    submitted_at: datetime
    is_confidential: bool = False
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class Dispute:
    """A formal dispute filed for arbitration"""

    id: str
    dispute_type: DisputeType
    title: str
    description: str
    filing_party: str  # Member ID who filed
    respondent: str  # Member or body being challenged
    filed_at: datetime
    status: DisputeStatus = DisputeStatus.FILED
    arbitrators: List[Arbitrator] = field(default_factory=list)
    evidence: List[Evidence] = field(default_factory=list)
    hearing_date: Optional[datetime] = None
    ruling: Optional[Ruling] = None
    related_proposals: List[str] = field(default_factory=list)  # Related amendment proposals
    urgency_level: int = 1  # 1=normal, 2=expedited
    is_confidential: bool = False


@dataclass
class Ruling:
    """Ruling issued by arbitration panel"""

    id: str
    dispute_id: str
    ruling_type: RulingType
    decision: str  # Summary decision
    findings: List[str]  # Detailed findings of fact
    reasoning: str  # Legal/Governance reasoning
    issued_at: datetime
    effective_date: datetime
    remedies: List[Dict[str, any]] = field(default_factory=list)  # Required actions
    dissent: Optional[Dict[str, str]] = None  # Dissenting opinion if any
    appealable: bool = True
    appeal_deadline: Optional[datetime] = None


@dataclass
class ArbitrationPanel:
    """An arbitration panel assembled for a dispute"""

    id: str
    dispute_id: str
    chair: Arbitrator
    members: List[Arbitrator]
    formed_at: datetime
    quorum_required: int = 3
    decision_method: str = "majority"  # "majority", "consensus", "supermajority"
    decision_threshold: float = 0.5  # For majority: >0.5, supermajority: 0.67


class DisputeError(Exception):
    """Base exception for dispute resolution errors"""
    pass


class PanelFormationError(DisputeError):
    """Raised when panel cannot be formed"""
    pass


class EvidenceError(DisputeError):
    """Raised when evidence submission fails"""
    pass


class DisputeSystem:
    """
    Dispute resolution system implementing Ostrom's conflict resolution principle.

    Key features:
    - Low-cost, local resolution before escalation
    - Impartial arbitration panels
    - Transparent procedures with due process
    - Binding or advisory rulings as configured
    - Appeal rights for serious matters
    """

    def __init__(
        self,
        default_panel_size: int = 3,
        max_panel_size: int = 5,
        default_hearing_days: int = 21,
        ruling_decision_days: int = 14,
        enable_appeals: bool = True,
        appeal_days: int = 7,
    ) -> None:
        """
        Initialize dispute system.

        Args:
            default_panel_size: Default number of arbitrators (odd for tie-breaking)
            max_panel_size: Maximum panel size
            default_hearing_days: Days from acceptance to hearing
            ruling_decision_days: Days from hearing to ruling
            enable_appeals: Whether appeals are allowed
            appeal_days: Days to file appeal after ruling
        """
        self.default_panel_size = default_panel_size
        self.max_panel_size = max_panel_size
        self.default_hearing_days = default_hearing_days
        self.ruling_decision_days = ruling_decision_days
        self.enable_appeals = enable_appeals
        self.appeal_days = appeal_days

        self._disputes: Dict[str, Dispute] = {}
        self._arbitrators: Dict[str, Arbitrator] = {}
        self._panels: Dict[str, ArbitrationPanel] = {}
        self._evidence: Dict[str, Evidence] = {}

        self._dispute_counter = 0
        self._evidence_counter = 0

        logger.info(
            "DisputeSystem initialized: panel_size=%d, hearing_days=%d, appeals=%s",
            default_panel_size,
            default_hearing_days,
            enable_appeals,
        )

    def register_arbitrator(self, arbitrator: Arbitrator) -> None:
        """Register an arbitrator in the system."""
        if arbitrator.id in self._arbitrators:
            raise ValueError(f"Arbitrator {arbitrator.id} already registered")

        self._arbitrators[arbitrator.id] = arbitrator
        logger.info("Registered arbitrator: %s", arbitrator.name)

    def get_available_arbitrators(
        self,
        required_expertise: Optional[List[str]] = None,
        exclude_ids: Optional[Set[str]] = None,
    ) -> List[Arbitrator]:
        """
        Get available arbitrators matching criteria.

        Args:
            required_expertise: Required expertise areas
            exclude_ids: Arbitrator IDs to exclude

        Returns:
            List of eligible arbitrators
        """
        exclude_ids = exclude_ids or set()
        candidates = []

        for arb in self._arbitrators.values():
            if not arb.is_active or arb.id in exclude_ids:
                continue

            if required_expertise:
                if not any(exp in arb.expertise for exp in required_expertise):
                    continue

            candidates.append(arb)

        return candidates

    def _generate_id(self) -> str:
        """Generate unique dispute ID."""
        self._dispute_counter += 1
        return f"DSP-{self._dispute_counter:08d}"

    def file_dispute(
        self,
        dispute_type: DisputeType,
        title: str,
        description: str,
        filing_party: str,
        respondent: str,
        related_proposals: Optional[List[str]] = None,
        urgency_level: int = 1,
        is_confidential: bool = False,
    ) -> Dispute:
        """
        File a new dispute.

        Args:
            dispute_type: Type of dispute
            title: Brief title
            description: Full description
            filing_party: Member ID filing the dispute
            respondent: Member or body being challenged
            related_proposals: Related amendment proposals
            urgency_level: 1=normal, 2=expedited
            is_confidential: Whether proceedings are confidential

        Returns:
            The created Dispute object

        Raises:
            ValueError: If parameters invalid
        """
        if urgency_level not in (1, 2):
            raise ValueError("Urgency level must be 1 or 2")

        if filing_party == respondent:
            raise ValueError("Filing party and respondent cannot be the same")

        dispute_id = self._generate_id()

        dispute = Dispute(
            id=dispute_id,
            dispute_type=dispute_type,
            title=title,
            description=description,
            filing_party=filing_party,
            respondent=respondent,
            filed_at=datetime.utcnow(),
            status=DisputeStatus.FILED,
            related_proposals=related_proposals or [],
            urgency_level=urgency_level,
            is_confidential=is_confidential,
        )

        self._disputes[dispute_id] = dispute
        logger.info("Dispute filed: %s: %s", dispute_id, title)
        return dispute

    def accept_dispute(
        self,
        dispute_id: str,
        acceptor_id: str,
        panel_size: Optional[int] = None,
    ) -> ArbitrationPanel:
        """
        Accept a dispute for arbitration and form panel.

        Args:
            dispute_id: Dispute to accept
            acceptor_id: Authority accepting (e.g., arbitration committee chair)
            panel_size: Custom panel size (default from init)

        Returns:
            Formed arbitration panel

        Raises:
            DisputeError: If dispute cannot be accepted
        """
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status not in (DisputeStatus.FILED,):
            raise DisputeError(f"Dispute {dispute_id} cannot be accepted in status {dispute.status}")

        # Determine required expertise based on dispute type
        expertise_map = {
            DisputeType.GOVERNANCE_PROCEDURE: ["governance", "procedural"],
            DisputeType.MEMBER_CONDUCT: ["conflict_resolution", "law"],
            DisputeType.RESOURCE_ALLOCATION: ["resource_management", "economics"],
            DisputeType.AMENDMENT_INTERPRETATION: ["governance", "law", "constitutional"],
            DisputeType.SANCTIONS_APPEAL: ["law", "conflict_resolution"],
            DisputeType.ELECTION_DISPUTE: ["election_law", "governance"],
        }
        required_expertise = expertise_map.get(dispute.dispute_type, ["governance"])

        # Get available arbitrators excluding conflicted parties
        exclude_ids = {dispute.filing_party, dispute.respondent}
        available = self.get_available_arbitrators(required_expertise, exclude_ids)

        panel_size = panel_size or self.default_panel_size
        if len(available) < panel_size:
            raise PanelFormationError(
                f"Insufficient arbitrators: need {panel_size}, have {len(available)}"
            )

        # Select arbitrators (could use rotation, random, or selection criteria)
        # For now: simple selection with conflict check
        selected = available[:panel_size]

        # Chair is first selected
        chair = selected[0]
        panel = ArbitrationPanel(
            id=f"PAN-{dispute_id}",
            dispute_id=dispute_id,
            chair=chair,
            members=selected,
            formed_at=datetime.utcnow(),
            quorum_required=panel_size // 2 + 1,
            decision_method="majority",
        )

        self._panels[panel.id] = panel
        dispute.arbitrators = selected
        dispute.status = DisputeStatus.ARBITRATOR_ASSIGNED

        logger.info(
            "Arbitration panel formed for %s: %d members, chair=%s",
            dispute_id,
            len(selected),
            chair.name,
        )
        return panel

    def submit_evidence(
        self,
        dispute_id: str,
        submitter_id: str,
        evidence_type: str,
        description: str,
        content_reference: str,
        is_confidential: bool = False,
        metadata: Optional[Dict] = None,
    ) -> Evidence:
        """
        Submit evidence to a dispute.

        Args:
            dispute_id: Dispute to submit to
            submitter_id: Member submitting
            evidence_type: Type of evidence
            description: Description
            content_reference: Reference to content
            is_confidential: Whether confidential
            metadata: Additional data

        Returns:
            Created Evidence object

        Raises:
            EvidenceError: If submission invalid
        """
        if dispute_id not in self._disputes:
            raise EvidenceError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status not in (
            DisputeStatus.ARBITRATOR_ASSIGNED,
            DisputeStatus.EVIDENCE_COLLECTION,
            DisputeStatus.HEARING_SCHEDULED,
        ):
            raise EvidenceError(f"Cannot submit evidence in status {dispute.status}")

        self._evidence_counter += 1
        evidence = Evidence(
            id=f"EVI-{self._evidence_counter:010d}",
            dispute_id=dispute_id,
            submitter_id=submitter_id,
            evidence_type=evidence_type,
            description=description,
            content_reference=content_reference,
            submitted_at=datetime.utcnow(),
            is_confidential=is_confidential,
            metadata=metadata or {},
        )

        self._evidence[evidence.id] = evidence
        dispute.evidence.append(evidence)

        if dispute.status == DisputeStatus.ARBITRATOR_ASSIGNED:
            dispute.status = DisputeStatus.EVIDENCE_COLLECTION

        logger.debug("Evidence submitted to %s: %s by %s", dispute_id, evidence.id, submitter_id)
        return evidence

    def schedule_hearing(
        self,
        dispute_id: str,
        scheduled_by: str,
        hearing_date: Optional[datetime] = None,
    ) -> datetime:
        """
        Schedule a hearing for a dispute.

        Args:
            dispute_id: Dispute to schedule
            scheduled_by: Who scheduled
            hearing_date: Specific date (defaults to calculated default)

        Returns:
            Scheduled hearing date
        """
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status not in (DisputeStatus.EVIDENCE_COLLECTION, DisputeStatus.HEARING_SCHEDULED):
            raise DisputeError(f"Cannot schedule hearing in status {dispute.status}")

        if hearing_date is None:
            hearing_date = datetime.utcnow() + timedelta(days=self.default_hearing_days)

        if hearing_date < datetime.utcnow():
            raise ValueError("Hearing date cannot be in the past")

        dispute.hearing_date = hearing_date
        dispute.status = DisputeStatus.HEARING_SCHEDULED

        logger.info("Hearing scheduled for %s: %s by %s", dispute_id, hearing_date.isoformat(), scheduled_by)
        return hearing_date

    def hold_hearing(self, dispute_id: str, notes: str = "") -> None:
        """
        Mark hearing as held.

        Args:
            dispute_id: Dispute
            notes: Hearing notes

        Raises:
            DisputeError: If hearing cannot be marked held
        """
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status != DisputeStatus.HEARING_SCHEDULED:
            raise DisputeError(f"Cannot hold hearing in status {dispute.status}")

        if not dispute.hearing_date:
            raise DisputeError("No hearing date scheduled")

        # Store hearing transcript/notes as evidence (before status change)
        self.submit_evidence(
            dispute_id=dispute_id,
            submitter_id="arbitration_panel",
            evidence_type="hearing_transcript",
            description="Hearing transcript/notes",
            content_reference=notes,
            is_confidential=dispute.is_confidential,
        )

        dispute.status = DisputeStatus.HEARING_HELD
        logger.info("Hearing held for %s", dispute_id)

    def issue_ruling(
        self,
        dispute_id: str,
        ruling_type: RulingType,
        decision: str,
        findings: List[str],
        reasoning: str,
        remedies: Optional[List[Dict[str, any]]] = None,
        dissent: Optional[Dict[str, str]] = None,
    ) -> Ruling:
        """
        Issue a ruling on a dispute.

        Args:
            dispute_id: Dispute to rule on
            ruling_type: Type of ruling
            decision: Summary decision
            findings: List of findings of fact
            reasoning: Reasoning behind ruling
            remedies: Required actions
            dissent: Dissenting opinion (author, text)

        Returns:
            The issued Ruling

        Raises:
            DisputeError: If ruling cannot be issued
        """
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status not in (DisputeStatus.HEARING_HELD, DisputeStatus.DELIBERATION):
            raise DisputeError(f"Cannot issue ruling in status {dispute.status}")

        now = datetime.utcnow()
        effective_date = now + timedelta(days=3)  # 3-day delay unless urgent
        if dispute.urgency_level == 2:
            effective_date = now  # Immediate for urgent

        ruling = Ruling(
            id=f"RUL-{dispute_id}",
            dispute_id=dispute_id,
            ruling_type=ruling_type,
            decision=decision,
            findings=findings,
            reasoning=reasoning,
            remedies=remedies or [],
            dissent=dissent,
            issued_at=now,
            effective_date=effective_date,
            appealable=self.enable_appeals and ruling_type != RulingType.DISMISSED,
            appeal_deadline=now + timedelta(days=self.appeal_days) if self.enable_appeals else None,
        )

        dispute.ruling = ruling
        dispute.status = DisputeStatus.RULING_ISSUED

        # Update arbitrator stats
        for arb in dispute.arbitrators:
            arb.cases_heard += 1

        logger.info("Ruling issued for %s: %s", dispute_id, decision)
        return ruling

    def resolve_dispute(self, dispute_id: str, resolved_by: str, resolution_notes: str = "") -> None:
        """
        Mark a dispute as fully resolved.

        Args:
            dispute_id: Dispute to resolve
            resolved_by: Who marked resolved
            resolution_notes: Resolution notes
        """
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status != DisputeStatus.RULING_ISSUED:
            raise DisputeError(f"Cannot resolve without ruling: {dispute.status}")

        now = datetime.utcnow()
        effective = dispute.ruling.effective_date if dispute.ruling else now

        if now < effective:
            logger.warning("Resolving %s before effective date %s", dispute_id, effective.isoformat())

        dispute.status = DisputeStatus.RESOLVED

        logger.info("Dispute resolved: %s by %s", dispute_id, resolved_by)

    def withdraw_dispute(self, dispute_id: str, withdrawn_by: str, reason: str) -> None:
        """
        Withdraw a dispute before resolution.

        Args:
            dispute_id: Dispute to withdraw
            withdrawn_by: Who withdraws
            reason: Reason for withdrawal
        """
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]

        if dispute.status in (DisputeStatus.RESOLVED, DisputeStatus.CLOSED):
            raise DisputeError(f"Cannot withdraw resolved dispute: {dispute.status}")

        dispute.status = DisputeStatus.WITHDRAWN
        dispute.ruling = Ruling(
            id=f"RUL-WD-{dispute_id}",
            dispute_id=dispute_id,
            ruling_type=RulingType.DISMISSED,
            decision="Withdrawn",
            findings=[f"Dispute withdrawn by {withdrawn_by}: {reason}"],
            reasoning="Withdrawn before resolution",
            issued_at=datetime.utcnow(),
            effective_date=datetime.utcnow(),
            appealable=False,
        )

        logger.info("Dispute withdrawn: %s by %s", dispute_id, withdrawn_by)

    def get_dispute(self, dispute_id: str) -> Optional[Dispute]:
        """Get dispute by ID."""
        return self._disputes.get(dispute_id)

    def list_disputes(
        self,
        status: Optional[DisputeStatus] = None,
        dispute_type: Optional[DisputeType] = None,
    ) -> List[Dispute]:
        """
        List disputes with optional filters.

        Args:
            status: Filter by status
            dispute_type: Filter by type

        Returns:
            List of matching disputes
        """
        disputes = list(self._disputes.values())

        if status:
            disputes = [d for d in disputes if d.status == status]
        if dispute_type:
            disputes = [d for d in disputes if d.dispute_type == dispute_type]

        return sorted(disputes, key=lambda d: d.filed_at, reverse=True)

    def get_evidence(self, dispute_id: str, include_confidential: bool = False) -> List[Evidence]:
        """Get evidence for a dispute."""
        if dispute_id not in self._disputes:
            return []

        if include_confidential:
            return self._disputes[dispute_id].evidence

        return [e for e in self._disputes[dispute_id].evidence if not e.is_confidential]

    def can_appeal(self, dispute_id: str, appellant_id: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a ruling can be appealed.

        Args:
            dispute_id: Dispute to appeal
            appellant_id: Who wants to appeal

        Returns:
            Tuple of (can_appeal, reason_if_not)
        """
        if dispute_id not in self._disputes:
            return False, "Dispute not found"

        dispute = self._disputes[dispute_id]

        if dispute.status != DisputeStatus.RULING_ISSUED:
            return False, f"Ruling not yet issued: {dispute.status}"

        if not dispute.ruling:
            return False, "No ruling exists"

        if not dispute.ruling.appealable:
            return False, "Ruling is not appealable"

        now = datetime.utcnow()
        if dispute.ruling.appeal_deadline and now > dispute.ruling.appeal_deadline:
            return False, f"Appeal deadline passed: {dispute.ruling.appeal_deadline}"

        # Only parties to dispute can appeal
        if appellant_id not in (dispute.filing_party, dispute.respondent):
            return False, "Only parties to the dispute may appeal"

        return True, None


def create_panel_with_expertise_rotation(
    dispute_id: str,
    arbitrators: List[Arbitrator],
    required_expertise: List[str],
    panel_size: int = 3,
) -> ArbitrationPanel:
    """
    Create panel using expertise-based rotation.

    Prioritizes arbitrators with relevant expertise while ensuring
    diversity and avoiding conflict.

    Args:
        dispute_id: Associated dispute
        arbitrators: Available arbitrators
        required_expertise: Required expertise areas
        panel_size: Panel size

    Returns:
        Formed panel
    """
    # Score arbitrators by expertise match
    scored = []
    for arb in arbitrators:
        score = sum(1 for exp in required_expertise if exp in arb.expertise)
        scored.append((score, arb))

    # Sort by score descending, then by cases_heard (for rotation)
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
