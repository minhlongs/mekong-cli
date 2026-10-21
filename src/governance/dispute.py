# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Dispute resolution module — Arbitration panel for governance conflicts."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from .dispute_models import (
    ArbitrationPanel, Arbitrator, Dispute, DisputeError, DisputeStatus, DisputeType,
    Evidence, EvidenceError, PanelFormationError, Ruling, RulingType,
    create_panel_with_expertise_rotation,
)
from .dispute_proceedings import DisputeProceedingsMixin

logger = logging.getLogger(__name__)


class DisputeSystem(DisputeProceedingsMixin):
    """Dispute resolution system implementing Ostrom's conflict resolution principle."""

    def __init__(
        self, default_panel_size: int = 3, max_panel_size: int = 5,
        default_hearing_days: int = 21, ruling_decision_days: int = 14,
        enable_appeals: bool = True, appeal_days: int = 7,
    ) -> None:
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

    def register_arbitrator(self, arbitrator: Arbitrator) -> None:
        if arbitrator.id in self._arbitrators:
            raise ValueError(f"Arbitrator {arbitrator.id} already registered")
        self._arbitrators[arbitrator.id] = arbitrator

    def get_available_arbitrators(
        self, required_expertise: Optional[List[str]] = None, exclude_ids: Optional[Set[str]] = None,
    ) -> List[Arbitrator]:
        exclude_ids = exclude_ids or set()
        return [
            arb for arb in self._arbitrators.values()
            if arb.is_active and arb.id not in exclude_ids
            and (not required_expertise or any(exp in arb.expertise for exp in required_expertise))
        ]

    def _generate_id(self) -> str:
        self._dispute_counter += 1
        return f"DSP-{self._dispute_counter:08d}"

    def file_dispute(
        self, dispute_type: DisputeType, title: str, description: str,
        filing_party: str, respondent: str, related_proposals: Optional[List[str]] = None,
        urgency_level: int = 1, is_confidential: bool = False,
    ) -> Dispute:
        if urgency_level not in (1, 2):
            raise ValueError("Urgency level must be 1 or 2")
        if filing_party == respondent:
            raise ValueError("Filing party and respondent cannot be the same")

        dispute_id = self._generate_id()
        dispute = Dispute(
            id=dispute_id, dispute_type=dispute_type, title=title,
            description=description, filing_party=filing_party,
            respondent=respondent, filed_at=datetime.utcnow(),
            status=DisputeStatus.FILED, related_proposals=related_proposals or [],
            urgency_level=urgency_level, is_confidential=is_confidential,
        )
        self._disputes[dispute_id] = dispute
        return dispute

    def accept_dispute(
        self, dispute_id: str, acceptor_id: str, panel_size: Optional[int] = None
    ) -> ArbitrationPanel:
        if dispute_id not in self._disputes:
            raise DisputeError(f"Dispute {dispute_id} not found")

        dispute = self._disputes[dispute_id]
        if dispute.status not in (DisputeStatus.FILED,):
            raise DisputeError(f"Dispute {dispute_id} cannot be accepted in status {dispute.status}")

        expertise_map = {
            DisputeType.GOVERNANCE_PROCEDURE: ["governance", "procedural"],
            DisputeType.MEMBER_CONDUCT: ["conflict_resolution", "law"],
            DisputeType.RESOURCE_ALLOCATION: ["resource_management", "economics"],
            DisputeType.AMENDMENT_INTERPRETATION: ["governance", "law", "constitutional"],
            DisputeType.SANCTIONS_APPEAL: ["law", "conflict_resolution"],
            DisputeType.ELECTION_DISPUTE: ["election_law", "governance"],
        }
        required_expertise = expertise_map.get(dispute.dispute_type, ["governance"])
        available = self.get_available_arbitrators(
            required_expertise, {dispute.filing_party, dispute.respondent}
        )

        panel_size = panel_size or self.default_panel_size
        if len(available) < panel_size:
            raise PanelFormationError(f"Insufficient arbitrators: need {panel_size}, have {len(available)}")

        selected = available[:panel_size]
        panel = ArbitrationPanel(
            id=f"PAN-{dispute_id}", dispute_id=dispute_id, chair=selected[0],
            members=selected, formed_at=datetime.utcnow(),
            quorum_required=panel_size // 2 + 1, decision_method="majority",
        )
        self._panels[panel.id] = panel
        dispute.arbitrators = selected
        dispute.status = DisputeStatus.ARBITRATOR_ASSIGNED
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
            id=f"EVI-{self._evidence_counter:010d}", dispute_id=dispute_id,
            submitter_id=submitter_id, evidence_type=evidence_type,
            description=description, content_reference=content_reference,
            submitted_at=datetime.utcnow(), is_confidential=is_confidential,
            metadata=metadata or {},
        )
        self._evidence[evidence.id] = evidence
        dispute.evidence.append(evidence)
        if dispute.status == DisputeStatus.ARBITRATOR_ASSIGNED:
            dispute.status = DisputeStatus.EVIDENCE_COLLECTION
        return evidence


__all__ = [
    "DisputeType", "DisputeStatus", "RulingType", "Arbitrator", "Evidence",
    "Dispute", "Ruling", "ArbitrationPanel", "DisputeError",
    "PanelFormationError", "EvidenceError", "DisputeSystem",
    "create_panel_with_expertise_rotation",
]
