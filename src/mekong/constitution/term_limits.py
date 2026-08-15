"""term_limits.py — Guardian term-limits enforcer for ZenOS Commons.

ZENOS Art 7: Guardian term = 1 year max, 2 terms maximum.

This module is protocol-level enforcement (code enforces; it doesn't trust).
When the Guardian is out of term, L1 and L2 amendment execution is blocked.
L3 (soft) proposals remain executable by default so routine evolution is not
strangled by an expired election.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.mekong.constitution.amendment import AmendmentProposal, AmendmentTier, ProposalState


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GuardianTerm:
    guardian_id: str
    term_number: int  # 1-indexed
    started_at: datetime
    ends_at: datetime

    def is_active(self, when: Optional[datetime] = None) -> bool:
        w = when or datetime.now(timezone.utc)
        return self.started_at <= w <= self.ends_at


class TermLimitError(Exception):
    """Raised when an action is blocked because the Guardian is out of term."""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class GuardianRegistry:
    """Track Guardian terms.  Max 2 terms; each term is at most 1 year."""

    max_terms: int = 2
    max_term_days: int = 365
    _terms: list[GuardianTerm] = field(default_factory=list)
    _current: Optional[GuardianTerm] = None

    # ------------------------------------------------------------------
    # Elections
    # ------------------------------------------------------------------

    def elect(
        self,
        guardian_id: str,
        *,
        at: Optional[datetime] = None,
        term_days: Optional[int] = None,
    ) -> GuardianTerm:
        if self._current and self._current.guardian_id == guardian_id and self._current.is_active(at):
            raise TermLimitError(
                f"Guardian {guardian_id} is already in an active term"
            )
        prior_terms = [t for t in self._terms if t.guardian_id == guardian_id]
        if len(prior_terms) >= self.max_terms:
            raise TermLimitError(
                f"Guardian {guardian_id} has already served {self.max_terms} terms"
            )
        now = at or datetime.now(timezone.utc)
        days = term_days or self.max_term_days
        term = GuardianTerm(
            guardian_id=guardian_id,
            term_number=len(prior_terms) + 1,
            started_at=now,
            ends_at=now + timedelta(days=days),
        )
        self._terms.append(term)
        self._current = term
        return term

    def current_term(self, when: Optional[datetime] = None) -> Optional[GuardianTerm]:
        if self._current is None:
            return None
        w = when or datetime.now(timezone.utc)
        if self._current.ends_at < w:
            self._current = None
            return None
        return self._current

    # ------------------------------------------------------------------
    # Enforcement
    # ------------------------------------------------------------------

    def guard_proposal(self, proposal: AmendmentProposal, *, when: Optional[datetime] = None) -> None:
        """Raise `TermLimitError` when the active Guardian cannot execute the
        proposal's tier.

        L1/L2 require an active Guardian term.  L3 is always allowed to
        prevent a deadlock caused by an expired election.
        """
        term = self.current_term(when)
        if term is None:
            # No Guardian at all — founder is the default Guardian under the
            # transition defaults in Art 10 of the charter.
            return
        if proposal.tier in {AmendmentTier.L1, AmendmentTier.L2}:
            if not term.is_active(when):
                raise TermLimitError(
                    f"Guardian {term.guardian_id} term #{term.term_number} expired "
                    f"on {term.ends_at.date()} — cannot execute {proposal.tier.value} proposal "
                    f"{proposal.proposal_id}"
                )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def guardian_of(registry: GuardianRegistry) -> Optional[str]:
    term = registry.current_term()
    return term.guardian_id if term else None


def term_days_remaining(registry: GuardianRegistry, *, when: Optional[datetime] = None) -> int:
    term = registry.current_term(when)
    if term is None:
        return 0
    w = when or datetime.now(timezone.utc)
    remaining = term.ends_at - w
    return max(0, int(remaining.total_seconds() // 86400))
