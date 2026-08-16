# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""member_registry.py — Commons member registry with anti-concentration cap.

Stores the ground-truth set of active Commons members and exposes operations
to register, update, and query members.  The concentration gate lives here
to make the cap impossible to accidentally bypass.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class MemberTier(str, Enum):
    FOUNDER = "FOUNDER"
    CONTRIBUTOR = "CONTRIBUTOR"
    HOLDER = "HOLDER"


class MemberStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXITED = "EXITED"


@dataclass(frozen=True)
class CommonsMember:
    member_id: str
    key_id: str  # links to the Economic Particle key_id
    tier: MemberTier
    voting_power: float
    joined_at: datetime
    term_start: datetime
    term_end: Optional[datetime]
    status: MemberStatus

    def is_active(self) -> bool:
        return self.status is MemberStatus.ACTIVE

    def in_term(self, when: Optional[datetime] = None) -> bool:
        w = when or datetime.now(timezone.utc)
        if self.term_end is None:
            return w >= self.term_start
        return self.term_start <= w <= self.term_end


class ConcentrationError(Exception):
    """Raised when registering a member would breach the anti-concentration cap."""


class RegistryError(Exception):
    """General registry failure."""


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class MemberRegistry:
    """In-memory registry with an energy-aware concentration cap.

    Lifetime: created once at process start; mutated through ``register`` /
    ``set_status`` / ``set_term``.  Persistence (D1/R2) is caller's job in
    production — this is the domain layer.
    """

    cap_fraction: float = 0.25  # no single member > 25% of weighted votes
    _members: dict[str, CommonsMember] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        *,
        key_id: str,
        tier: MemberTier | str,
        voting_power: float,
        term_end: Optional[datetime] = None,
        at: Optional[datetime] = None,
        existing_id: Optional[str] = None,
    ) -> CommonsMember:
        """Add a new member or re-register an existing one.

        Raises `ConcentrationError` if the prospective member's share of
        total voting power exceeds the cap.
        """
        if isinstance(tier, str):
            tier = MemberTier(tier.upper())

        now = at or datetime.now(timezone.utc)
        member_id = existing_id or _new_id()

        # Pre-flight: compute resultant total power if this member is new or
        # being re-registered (status flip EXITED -> ACTIVE).
        total = self._total_active_power()
        prev = self._members.get(member_id)
        if prev and prev.status is MemberStatus.ACTIVE:
            raise RegistryError(
                f"Member {member_id} is already active — use set_status to change"
            )
        added = voting_power
        if prev and prev.status is not MemberStatus.ACTIVE:
            # re-activation removes their old inactive contribution from "not
            # counted" but they were not in total above, so total simply grows
            # by voting_power.
            pass
        new_total = total + added
        share = added / new_total if new_total > 0 else 1.0
        if share > self.cap_fraction:
            raise ConcentrationError(
                f"Adding {member_id} ({tier.value}) gives "
                f"{share:.1%} voting power — exceeds {self.cap_fraction:.0%} cap "
                f"(total would be {new_total:.2f} power across "
                f"{self.active_count() + 1} members)"
            )

        rec = CommonsMember(
            member_id=member_id,
            key_id=key_id,
            tier=tier,
            voting_power=voting_power,
            joined_at=now,
            term_start=now,
            term_end=term_end,
            status=MemberStatus.ACTIVE,
        )
        self._members[member_id] = rec
        return rec

    def set_status(self, member_id: str, status: MemberStatus) -> None:
        member = self._require(member_id)
        member.status = status  # type: ignore[assignment]

    def set_term(self, member_id: str, *, start: datetime, end: Optional[datetime]) -> None:
        member = self._require(member_id)
        member.term_start = start
        member.term_end = end

    def get(self, member_id: str) -> CommonsMember:
        return self._require(member_id)

    def active_members(self) -> list[CommonsMember]:
        return [m for m in self._members.values() if m.is_active()]

    def active_count(self) -> int:
        return len(self.active_members())

    def total_active_power(self) -> float:
        return self._total_active_power()

    def power_share(self, member_id: str) -> float:
        member = self._require(member_id)
        if not member.is_active():
            return 0.0
        total = self._total_active_power()
        if total <= 0:
            return 0.0
        return member.voting_power / total

    def contribution_power(self, commit_count: int) -> float:
        """ZENOS-COMMONS v1 formula:

        ``power = 1.0 + min(commit_count ** 0.5, 10.0)``, capped at 5×.
        """
        import math

        base = 1.0
        bonus = min(math.sqrt(max(commit_count, 0)), 10.0)
        raw = base + bonus
        return min(raw, 5.0)

    # ------------------------------------------------------------------
    # Persistence helpers (caller owns disk format)
    # ------------------------------------------------------------------

    def to_dicts(self) -> list[dict]:
        out: list[dict] = []
        for m in self.active_members():
            d = {
                "member_id": m.member_id,
                "key_id": m.key_id,
                "tier": m.tier.value,
                "voting_power": m.voting_power,
                "joined_at": _iso(m.joined_at),
                "term_start": _iso(m.term_start),
                "term_end": _iso(m.term_end) if m.term_end else None,
                "status": m.status.value,
            }
            out.append(d)
        return out

    def from_dicts(self, rows: list[dict]) -> None:
        for r in rows:
            member = CommonsMember(
                member_id=r["member_id"],
                key_id=r["key_id"],
                tier=MemberTier(r["tier"].upper()),
                voting_power=float(r["voting_power"]),
                joined_at=_parse_dt(r["joined_at"]),
                term_start=_parse_dt(r["term_start"]),
                term_end=_parse_dt(r["term_end"]) if r.get("term_end") else None,
                status=MemberStatus(r["status"].upper()),
            )
            self._members[member.member_id] = member

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _total_active_power(self) -> float:
        return sum(
            m.voting_power for m in self._members.values() if m.is_active()
        )

    def _require(self, member_id: str) -> CommonsMember:
        try:
            return self._members[member_id]
        except KeyError:
            raise RegistryError(
                f"Unknown member: {member_id}"
            ) from None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_id(prefix: str = "cm") -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    rand = secrets.token_hex(4)
    return f"{prefix}_{ts}_{rand}"


def _iso(dt: datetime) -> str:
    return dt.isoformat() if dt.tzinfo else dt.replace(tzinfo=timezone.utc).isoformat()


def _parse_dt(raw: str) -> datetime:
    # accepts either ISO8601 or integer-unix-seconds for interoperability
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.fromtimestamp(int(raw), tz=timezone.utc)
        except Exception:
            raise RegistryError(f"Unparseable datetime: {raw!r}")
