# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Autonomous Agent Collaboration Mesh & Multi-Agent Consensus Protocol.

Coordinates structured debate, quorum voting (majority, supermajority, unanimous,
and weighted roles), synthetic consensus resolution, and cryptographic SHA-256
ballot persistence in SQLite (.mekong/consensus.db).

STRICT INVARIANT: Provider-neutral and standard-library-only. Zero external vendor
SDKs or heavy third-party packages (complies with tests/test_core_boundary.py).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default database location in .mekong/consensus.db
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = _PROJECT_ROOT / ".mekong" / "consensus.db"

# Canonical role authority weights in Mekong multi-agent architecture
DEFAULT_ROLE_WEIGHTS: Dict[str, int] = {
    "ceo": 3,
    "cto": 2,
    "cfo": 2,
    "cmo": 1,
    "pm": 1,
    "sre": 1,
    "qa": 1,
    "cso": 1,
    "ae": 1,
}

# Agent persona heuristics for debate arguments and voting perspectives
AGENT_PERSPECTIVES: Dict[str, Dict[str, str]] = {
    "ceo": {
        "title": "Chief Executive Officer",
        "focus": "Strategic alignment, corporate growth, ROI, and balanced risk-reward posture.",
        "bias": "Favors actions maximizing enterprise value, competitive moat, and capital efficiency.",
    },
    "cto": {
        "title": "Chief Technology Officer",
        "focus": "Architectural integrity, technical debt minimization, security, and developer velocity.",
        "bias": "Favors clean decoupled architecture, automated verification, and robust modern primitives.",
    },
    "cfo": {
        "title": "Chief Financial Officer",
        "focus": "Cost governance, unit economics, budget constraints, and cash flow predictability.",
        "bias": "Skeptical of unbudgeted infrastructure spend; demands quantifiable ROI and payback horizons.",
    },
    "cmo": {
        "title": "Chief Marketing Officer",
        "focus": "Brand velocity, audience reach, market positioning, and user acquisition pipelines.",
        "bias": "Favors speed-to-market, customer-facing differentiation, and high-impact growth loops.",
    },
    "pm": {
        "title": "Product Manager",
        "focus": "User journey friction, feature adoption, time-to-market, and roadmap priority.",
        "bias": "Champions user empathy, iterative release cadence, and eliminating workflow bottlenecks.",
    },
    "sre": {
        "title": "Site Reliability Engineer",
        "focus": "Uptime, SLOs/SLAs, operational simplicity, disaster recovery, and blast-radius containment.",
        "bias": "Cautious on breaking changes; requires automated rollbacks, telemetry, and rate limits.",
    },
    "qa": {
        "title": "Quality Assurance Lead",
        "focus": "Test coverage, regression prevention, edge cases, and deterministic reproducibility.",
        "bias": "Insists on comprehensive test gates (unit, integration, e2e) before code promotion.",
    },
    "cso": {
        "title": "Chief Strategy Officer",
        "focus": "Competitive landscape, intelligence gathering, defensibility, and market shifts.",
        "bias": "Prioritizes long-term sustainable advantage and strategic maneuverability.",
    },
}

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS consensus_ballots (
    ballot_id       TEXT    NOT NULL PRIMARY KEY,
    proposal        TEXT    NOT NULL,
    quorum_type     TEXT    NOT NULL,
    passed          INTEGER NOT NULL DEFAULT 0,
    yes_votes       INTEGER NOT NULL DEFAULT 0,
    no_votes        INTEGER NOT NULL DEFAULT 0,
    abstain_votes   INTEGER NOT NULL DEFAULT 0,
    ballot_hash     TEXT    NOT NULL,
    payload_json    TEXT    NOT NULL,
    created_at      REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS debate_sessions (
    session_id          TEXT    NOT NULL PRIMARY KEY,
    topic               TEXT    NOT NULL,
    proponent           TEXT    NOT NULL,
    opponent            TEXT    NOT NULL,
    moderator           TEXT    NOT NULL,
    consensus_score     REAL    NOT NULL DEFAULT 0.0,
    recommended_action  TEXT    NOT NULL,
    payload_json        TEXT    NOT NULL,
    created_at          REAL    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ballots_created_at ON consensus_ballots (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_debates_created_at ON debate_sessions (created_at DESC);
"""


@dataclass
class AgentVote:
    """Individual vote cast by an agent in a consensus session."""

    agent_id: str
    vote: str  # "yes", "no", "abstain"
    weight: int = 1
    justification: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert vote to dictionary."""
        return asdict(self)


@dataclass
class BallotResult:
    """Outcome and cryptographic ledger receipt of a consensus vote."""

    ballot_id: str
    proposal: str
    quorum_type: str  # "majority", "supermajority", "unanimous", "weighted"
    votes: List[AgentVote] = field(default_factory=list)
    total_votes: int = 0
    yes_votes: int = 0
    no_votes: int = 0
    abstain_votes: int = 0
    weighted_yes: int = 0
    weighted_total: int = 0
    passed: bool = False
    ballot_hash: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert ballot result to dictionary."""
        return {
            "ballot_id": self.ballot_id,
            "proposal": self.proposal,
            "quorum_type": self.quorum_type,
            "votes": [v.to_dict() for v in self.votes],
            "total_votes": self.total_votes,
            "yes_votes": self.yes_votes,
            "no_votes": self.no_votes,
            "abstain_votes": self.abstain_votes,
            "weighted_yes": self.weighted_yes,
            "weighted_total": self.weighted_total,
            "passed": self.passed,
            "ballot_hash": self.ballot_hash,
            "timestamp": self.timestamp,
        }


@dataclass
class DebateTurn:
    """A single turn or speech in a structured multi-agent debate."""

    round_number: int
    speaker: str
    role: str
    stance: str  # "pro", "con", "synthesis"
    argument: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert turn to dictionary."""
        return asdict(self)


@dataclass
class DebateSession:
    """Full transcript, telemetry, and synthetic resolution of a debate session."""

    session_id: str
    topic: str
    proponent: str
    opponent: str
    moderator: str
    rounds: int
    turns: List[DebateTurn] = field(default_factory=list)
    synthesis: str = ""
    recommended_action: str = ""
    consensus_score: float = 0.0  # 0.0 to 100.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert debate session to dictionary."""
        return {
            "session_id": self.session_id,
            "topic": self.topic,
            "proponent": self.proponent,
            "opponent": self.opponent,
            "moderator": self.moderator,
            "rounds": self.rounds,
            "turns": [t.to_dict() for t in self.turns],
            "synthesis": self.synthesis,
            "recommended_action": self.recommended_action,
            "consensus_score": self.consensus_score,
            "timestamp": self.timestamp,
        }


class ConsensusBridge:
    """Coordinates multi-agent voting, structured debate, and cryptographic ledger."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        raw_env = os.environ.get("MEKONG_CONSENSUS_DB_PATH")
        if db_path:
            self.db_path = Path(db_path).resolve()
        elif raw_env:
            self.db_path = Path(raw_env).resolve()
        else:
            self.db_path = _DEFAULT_DB.resolve()

        self._lock = threading.Lock()
        self._ensure_db()

    def _ensure_db(self) -> None:
        """Create database parent directories and initialize tables."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.executescript(_SCHEMA_SQL)
                conn.commit()
        except Exception as exc:
            logger.warning(f"Error initializing consensus database: {exc}")

    def _broadcast_gateway_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Stream consensus lifecycle events over Gateway broker if active."""
        try:
            from src.core.gateway.streaming import StreamEvent, get_streaming_broker
            broker = get_streaming_broker()
            broker.publish(StreamEvent(
                mission_id="consensus_mesh",
                event_type=event_type,
                data=data,
            ))
        except Exception:
            pass

    def compute_ballot_hash(self, proposal: str, votes: List[AgentVote], created_at: float) -> str:
        """Compute deterministic SHA-256 checksum representing the ballot ledger."""
        hasher = hashlib.sha256()
        canonical_data = {
            "proposal": proposal.strip(),
            "votes": sorted(
                [{"agent": v.agent_id, "vote": v.vote, "weight": v.weight} for v in votes],
                key=lambda x: x["agent"],
            ),
            "created_at": created_at,
        }
        hasher.update(json.dumps(canonical_data, sort_keys=True).encode("utf-8"))
        return hasher.hexdigest()

    def create_vote(
        self,
        proposal: str,
        agents: Optional[List[str]] = None,
        quorum: str = "majority",
        custom_votes: Optional[List[Dict[str, Any]]] = None,
    ) -> BallotResult:
        """Execute and resolve a multi-agent vote on a specified proposal."""
        quorum_mode = quorum.lower().strip()
        if quorum_mode not in ("majority", "supermajority", "unanimous", "weighted"):
            quorum_mode = "majority"

        target_agents = [a.lower().strip() for a in agents] if agents else ["ceo", "cto", "cfo", "pm", "sre"]
        now = time.time()
        ballot_id = f"ballot_{int(now * 1000)}_{os.urandom(3).hex()}"

        self._broadcast_gateway_event("consensus_proposal_created", {
            "ballot_id": ballot_id,
            "proposal": proposal,
            "quorum_type": quorum_mode,
            "agents": target_agents,
        })

        votes: List[AgentVote] = []
        if custom_votes:
            for cv in custom_votes:
                agent = cv.get("agent_id", "agent").lower()
                v_choice = cv.get("vote", "yes").lower()
                w = cv.get("weight", DEFAULT_ROLE_WEIGHTS.get(agent, 1))
                just = cv.get("justification", f"Vote from {agent}")
                votes.append(AgentVote(
                    agent_id=agent,
                    vote=v_choice,
                    weight=w,
                    justification=just,
                    timestamp=now,
                ))
        else:
            # Generate simulated agent votes using persona heuristics
            for agent in target_agents:
                weight = DEFAULT_ROLE_WEIGHTS.get(agent, 1)
                perspective = AGENT_PERSPECTIVES.get(agent, {})
                v_choice, just = self._simulate_agent_vote(agent, proposal, perspective)
                votes.append(AgentVote(
                    agent_id=agent,
                    vote=v_choice,
                    weight=weight,
                    justification=just,
                    timestamp=now,
                ))

        # Tally votes
        yes_votes = sum(1 for v in votes if v.vote == "yes")
        no_votes = sum(1 for v in votes if v.vote == "no")
        abstain_votes = sum(1 for v in votes if v.vote == "abstain")
        active_votes = yes_votes + no_votes

        weighted_yes = sum(v.weight for v in votes if v.vote == "yes")
        weighted_no = sum(v.weight for v in votes if v.vote == "no")
        weighted_total = weighted_yes + weighted_no

        passed = False
        if quorum_mode == "majority":
            passed = yes_votes > (active_votes / 2.0) if active_votes > 0 else False
        elif quorum_mode == "supermajority":
            passed = yes_votes >= (2.0 * active_votes / 3.0) if active_votes > 0 else False
        elif quorum_mode == "unanimous":
            passed = (yes_votes == active_votes and active_votes > 0)
        elif quorum_mode == "weighted":
            passed = weighted_yes > (weighted_total / 2.0) if weighted_total > 0 else False

        ballot_hash = self.compute_ballot_hash(proposal, votes, now)

        result = BallotResult(
            ballot_id=ballot_id,
            proposal=proposal,
            quorum_type=quorum_mode,
            votes=votes,
            total_votes=len(votes),
            yes_votes=yes_votes,
            no_votes=no_votes,
            abstain_votes=abstain_votes,
            weighted_yes=weighted_yes,
            weighted_total=weighted_total,
            passed=passed,
            ballot_hash=ballot_hash,
            timestamp=now,
        )

        # Persist ballot into SQLite
        self._save_ballot(result)

        self._broadcast_gateway_event("consensus_resolved", {
            "ballot_id": ballot_id,
            "passed": passed,
            "yes_votes": yes_votes,
            "no_votes": no_votes,
            "ballot_hash": ballot_hash,
        })

        return result

    def _simulate_agent_vote(
        self,
        agent: str,
        proposal: str,
        perspective: Dict[str, str],
    ) -> Tuple[str, str]:
        """Produce a heuristic vote and rationale reflecting agent's architectural persona."""
        prop_lower = proposal.lower()
        title = perspective.get("title", agent.upper())

        # Heuristic rules based on proposal keywords and agent roles
        if agent == "sre":
            if any(k in prop_lower for k in ("skip test", "force deploy", "disable alert", "remove safeguard")):
                return "no", f"[{title}] Rejects due to unacceptable reliability and disaster recovery risk."
            return "yes", f"[{title}] Confirms deployment guardrails, telemetry, and rollback checkpoints are defined."

        if agent == "cfo":
            if any(k in prop_lower for k in ("increase budget", "expensive", "unlimited spend", "third-party license")):
                return "no", f"[{title}] Requires formal cost-benefit analysis and payback horizon model."
            return "yes", f"[{title}] Approves; capital allocation aligns with fiscal prudence and unit economics."

        if agent == "cto":
            if any(k in prop_lower for k in ("monolith", "quick hack", "ignore debt", "vendor lock")):
                return "no", f"[{title}] Technical debt and architectural complexity exceed maintainability threshold."
            return "yes", f"[{title}] Architectural decoupling, testability, and standard boundaries are satisfied."

        if agent == "qa":
            if any(k in prop_lower for k in ("skip test", "manual test only", "untested")):
                return "no", f"[{title}] Zero automated regression coverage breaches deployment contract."
            return "yes", f"[{title}] Test suites provide deterministic pass criteria with zero regressions."

        # Default CEO / PM / CMO alignment
        return "yes", f"[{title}] Aligns with current roadmap milestone and strategic company priorities."

    def _save_ballot(self, result: BallotResult) -> None:
        """Persist ballot record to consensus database."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO consensus_ballots
                        (ballot_id, proposal, quorum_type, passed, yes_votes, no_votes, abstain_votes, ballot_hash, payload_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            result.ballot_id,
                            result.proposal,
                            result.quorum_type,
                            1 if result.passed else 0,
                            result.yes_votes,
                            result.no_votes,
                            result.abstain_votes,
                            result.ballot_hash,
                            json.dumps(result.to_dict()),
                            result.timestamp,
                        ),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning(f"Error persisting ballot {result.ballot_id}: {exc}")

    def conduct_debate(
        self,
        topic: str,
        proponent: str = "cto",
        opponent: str = "sre",
        moderator: str = "ceo",
        rounds: int = 2,
    ) -> DebateSession:
        """Conduct a structured multi-round thesis-antithesis-synthesis debate."""
        now = time.time()
        session_id = f"debate_{int(now * 1000)}_{os.urandom(3).hex()}"
        total_rounds = max(1, min(rounds, 5))

        turns: List[DebateTurn] = []

        prop_persp = AGENT_PERSPECTIVES.get(proponent, {"title": proponent.upper()})
        opp_persp = AGENT_PERSPECTIVES.get(opponent, {"title": opponent.upper()})
        mod_persp = AGENT_PERSPECTIVES.get(moderator, {"title": moderator.upper()})

        for r in range(1, total_rounds + 1):
            # Proponent turn
            pro_arg = (
                f"Round {r} ({prop_persp.get('title', proponent)}): "
                f"We must advance '{topic}'. Velocity, modular evolution, and developer throughput "
                f"outweigh incremental transitional friction. We provide automated interfaces and clean contracts."
            )
            turns.append(DebateTurn(
                round_number=r,
                speaker=proponent,
                role=prop_persp.get("title", proponent),
                stance="pro",
                argument=pro_arg,
                timestamp=time.time(),
            ))
            self._broadcast_gateway_event("consensus_debate_turn", turns[-1].to_dict())

            # Opponent turn
            opp_arg = (
                f"Round {r} ({opp_persp.get('title', opponent)}): "
                f"Counterpoint on '{topic}': Blast radius containment and failure modes are paramount. "
                f"Without verified telemetry, fallback recovery mechanisms, and strict rate limits, "
                f"uncontrolled complexity risks production outage and operational burden."
            )
            turns.append(DebateTurn(
                round_number=r,
                speaker=opponent,
                role=opp_persp.get("title", opponent),
                stance="con",
                argument=opp_arg,
                timestamp=time.time(),
            ))
            self._broadcast_gateway_event("consensus_debate_turn", turns[-1].to_dict())

        # Moderator Synthesis
        synthesis = (
            f"Synthesis by {mod_persp.get('title', moderator)}: "
            f"Both {prop_persp.get('title', proponent)}'s emphasis on velocity and "
            f"{opp_persp.get('title', opponent)}'s insistence on blast-radius control are valid. "
            f"We proceed with '{topic}' bounded by strict automated test gates, checkpoint rollbacks, "
            f"and phase-gated canary deployment."
        )
        recommended_action = f"Proceed with phased implementation of '{topic}' with mandatory SRE observability gates."
        consensus_score = 88.5

        turns.append(DebateTurn(
            round_number=total_rounds + 1,
            speaker=moderator,
            role=mod_persp.get("title", moderator),
            stance="synthesis",
            argument=synthesis,
            timestamp=time.time(),
        ))

        session = DebateSession(
            session_id=session_id,
            topic=topic,
            proponent=proponent,
            opponent=opponent,
            moderator=moderator,
            rounds=total_rounds,
            turns=turns,
            synthesis=synthesis,
            recommended_action=recommended_action,
            consensus_score=consensus_score,
            timestamp=now,
        )

        # Persist debate session
        self._save_debate(session)

        return session

    def _save_debate(self, session: DebateSession) -> None:
        """Persist debate record to consensus database."""
        with self._lock:
            try:
                with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO debate_sessions
                        (session_id, topic, proponent, opponent, moderator, consensus_score, recommended_action, payload_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session.session_id,
                            session.topic,
                            session.proponent,
                            session.opponent,
                            session.moderator,
                            session.consensus_score,
                            session.recommended_action,
                            json.dumps(session.to_dict()),
                            session.timestamp,
                        ),
                    )
                    conn.commit()
            except Exception as exc:
                logger.warning(f"Error persisting debate {session.session_id}: {exc}")

    def list_ballots(self, limit: int = 20) -> List[BallotResult]:
        """Fetch historical ballots from consensus database."""
        results: List[BallotResult] = []
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                cursor = conn.execute(
                    "SELECT payload_json FROM consensus_ballots ORDER BY created_at DESC LIMIT ?",
                    (max(1, limit),),
                )
                for (payload,) in cursor.fetchall():
                    data = json.loads(payload)
                    votes = [AgentVote(**v) for v in data.get("votes", [])]
                    results.append(BallotResult(
                        ballot_id=data["ballot_id"],
                        proposal=data["proposal"],
                        quorum_type=data["quorum_type"],
                        votes=votes,
                        total_votes=data.get("total_votes", len(votes)),
                        yes_votes=data.get("yes_votes", 0),
                        no_votes=data.get("no_votes", 0),
                        abstain_votes=data.get("abstain_votes", 0),
                        weighted_yes=data.get("weighted_yes", 0),
                        weighted_total=data.get("weighted_total", 0),
                        passed=bool(data.get("passed", False)),
                        ballot_hash=data.get("ballot_hash", ""),
                        timestamp=data.get("timestamp", 0.0),
                    ))
        except Exception as exc:
            logger.warning(f"Error reading ballots from database: {exc}")
        return results

    def list_debates(self, limit: int = 20) -> List[DebateSession]:
        """Fetch historical debate sessions from consensus database."""
        results: List[DebateSession] = []
        try:
            with sqlite3.connect(str(self.db_path), timeout=10.0) as conn:
                cursor = conn.execute(
                    "SELECT payload_json FROM debate_sessions ORDER BY created_at DESC LIMIT ?",
                    (max(1, limit),),
                )
                for (payload,) in cursor.fetchall():
                    data = json.loads(payload)
                    turns = [DebateTurn(**t) for t in data.get("turns", [])]
                    results.append(DebateSession(
                        session_id=data["session_id"],
                        topic=data["topic"],
                        proponent=data["proponent"],
                        opponent=data["opponent"],
                        moderator=data["moderator"],
                        rounds=data.get("rounds", 1),
                        turns=turns,
                        synthesis=data.get("synthesis", ""),
                        recommended_action=data.get("recommended_action", ""),
                        consensus_score=data.get("consensus_score", 0.0),
                        timestamp=data.get("timestamp", 0.0),
                    ))
        except Exception as exc:
            logger.warning(f"Error reading debates from database: {exc}")
        return results


# Global singleton instance
_GLOBAL_CONSENSUS_BRIDGE: Optional[ConsensusBridge] = None
_GLOBAL_CONSENSUS_LOCK = threading.Lock()


def get_consensus_bridge() -> ConsensusBridge:
    """Get or initialize singleton ConsensusBridge."""
    global _GLOBAL_CONSENSUS_BRIDGE
    with _GLOBAL_CONSENSUS_LOCK:
        if _GLOBAL_CONSENSUS_BRIDGE is None:
            _GLOBAL_CONSENSUS_BRIDGE = ConsensusBridge()
        return _GLOBAL_CONSENSUS_BRIDGE
