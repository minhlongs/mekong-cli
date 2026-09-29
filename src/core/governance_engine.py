# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/core/governance_engine.py — Autonomous Constitutional Governance & Voting Engine.
Pure Python standard library implementation with zero external HTTP or vendor dependencies.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class GovernanceEngine:
    """Autonomous Constitutional Governance & Voting Engine.

    Manages constitutional amendment proposals, multi-tier quorum requirements,
    supermajority threshold validation, cryptographic ballot tracking, and vote tallying
    with SQLite WAL persistence.
    """

    # Quorum and passage threshold configurations per tier
    TIER_SPECS: Dict[str, Dict[str, Any]] = {
        "soft": {
            "name": "Soft Governance",
            "threshold_percent": 50.0,
            "quorum_min": 3,
            "description": "Simple majority (>50%) for operational tweaks, templates, and non-binding directives.",
        },
        "operational": {
            "name": "Operational Amendment",
            "threshold_percent": 66.7,
            "quorum_min": 5,
            "description": "Two-thirds supermajority (≥66.7%) for service contracts, pricing adjustments, and tool integrations.",
        },
        "foundational": {
            "name": "Foundational Constitutional",
            "threshold_percent": 75.0,
            "quorum_min": 7,
            "description": "Three-fourths supermajority (≥75.0%) for core boundary invariants, charters, and right-to-fork guarantees.",
        },
    }

    VALID_CHOICES: set[str] = {"yes", "no", "abstain", "recuse"}

    DEFAULT_PROPOSALS: List[Dict[str, Any]] = [
        {
            "id": "prop_zenos_001",
            "title": "Sovereign Air-Gap & Standard Library Invariant Charter",
            "description": "Establish irreversible boundary guarantees prohibiting external HTTP/SDK calls in core execution modules.",
            "amendment_text": "All modules under src/core/ must remain 100% pure standard library with zero third-party dependencies.",
            "proposer": "founder",
            "tier": "foundational",
            "co_sponsors": ["sovereign-architect", "ops-lead"],
            "status": "enacted",
            "threshold_percent": 75.0,
            "quorum_min": 7,
            "results": {
                "total_votes": 8,
                "yes_weight": 8.0,
                "no_weight": 0.0,
                "abstain_weight": 0.0,
                "recuse_weight": 0.0,
                "quorum_reached": True,
                "passed": True,
                "enacted": True,
            },
        },
        {
            "id": "prop_zenos_002",
            "title": "Autonomous Quorum Voting & Debate Protocol",
            "description": "Standardize multi-agent consensus protocols and structured debate procedures for high-risk executions.",
            "amendment_text": "High-risk decisions exceeding 20% budget or architectural restructuring require multi-agent quorum consensus.",
            "proposer": "sovereign-architect",
            "tier": "operational",
            "co_sponsors": ["pragmatic-operator"],
            "status": "passed",
            "threshold_percent": 66.7,
            "quorum_min": 5,
            "results": {
                "total_votes": 6,
                "yes_weight": 5.0,
                "no_weight": 1.0,
                "abstain_weight": 0.0,
                "recuse_weight": 0.0,
                "quorum_reached": True,
                "passed": True,
                "enacted": False,
            },
        },
        {
            "id": "prop_zenos_003",
            "title": "Dynamic Plugin Marketplace & Provider Governance",
            "description": "Authorize community-contributed vendor onboarding with automated security and compliance audit verification.",
            "amendment_text": "Community plugins and model providers must pass air-gap boundary audit scoring (≥80) before public listing.",
            "proposer": "community-steward",
            "tier": "soft",
            "co_sponsors": ["growth-evangelist"],
            "status": "voting",
            "threshold_percent": 50.0,
            "quorum_min": 3,
            "results": {
                "total_votes": 2,
                "yes_weight": 2.0,
                "no_weight": 0.0,
                "abstain_weight": 0.0,
                "recuse_weight": 0.0,
                "quorum_reached": False,
                "passed": False,
                "enacted": False,
            },
        },
    ]

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize SQLite database for constitutional governance ledger."""
        if db_path is None:
            db_dir = Path(".mekong")
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "governance.db"
        else:
            self.db_path = Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amendment_text TEXT NOT NULL,
                    proposer TEXT NOT NULL,
                    tier TEXT NOT NULL,
                    co_sponsors TEXT NOT NULL,
                    status TEXT NOT NULL,
                    threshold_percent REAL NOT NULL,
                    quorum_min INTEGER NOT NULL,
                    results TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    voter_id TEXT NOT NULL,
                    choice TEXT NOT NULL,
                    weight REAL NOT NULL,
                    ballot_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(proposal_id, voter_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_audits (
                    id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Pre-seed canonical proposals if empty
            cur = conn.execute("SELECT COUNT(*) as count FROM proposals")
            if cur.fetchone()["count"] == 0:
                now = datetime.now(timezone.utc).isoformat()
                for p in self.DEFAULT_PROPOSALS:
                    conn.execute(
                        """
                        INSERT INTO proposals (
                            id, title, description, amendment_text, proposer, tier,
                            co_sponsors, status, threshold_percent, quorum_min,
                            results, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            p["id"],
                            p["title"],
                            p["description"],
                            p["amendment_text"],
                            p["proposer"],
                            p["tier"],
                            json.dumps(p["co_sponsors"]),
                            p["status"],
                            p["threshold_percent"],
                            p["quorum_min"],
                            json.dumps(p["results"]),
                            now,
                            now,
                        ),
                    )
            conn.commit()

    # ---------------------------------------------------------------------------
    # Core Governance Engine API
    # ---------------------------------------------------------------------------

    def create_proposal(
        self,
        title: str,
        description: str,
        text: str,
        proposer: str = "founder",
        tier: str = "soft",
        co_sponsors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Draft and submit a new constitutional amendment proposal."""
        ptier = tier.strip().lower()
        if ptier not in self.TIER_SPECS:
            ptier = "soft"

        spec = self.TIER_SPECS[ptier]
        pid = f"prop_{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        sponsors = co_sponsors or []

        initial_results = {
            "total_votes": 0,
            "yes_weight": 0.0,
            "no_weight": 0.0,
            "abstain_weight": 0.0,
            "recuse_weight": 0.0,
            "quorum_reached": False,
            "passed": False,
            "enacted": False,
        }

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO proposals (
                    id, title, description, amendment_text, proposer, tier,
                    co_sponsors, status, threshold_percent, quorum_min,
                    results, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pid,
                    title.strip(),
                    description.strip(),
                    text.strip(),
                    proposer.strip() or "founder",
                    ptier,
                    json.dumps(sponsors),
                    "voting",
                    spec["threshold_percent"],
                    spec["quorum_min"],
                    json.dumps(initial_results),
                    now,
                    now,
                ),
            )
            # Log audit trail
            conn.execute(
                """
                INSERT INTO governance_audits (id, action, target_id, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    f"aud_{uuid.uuid4().hex[:10]}",
                    "create_proposal",
                    pid,
                    json.dumps({"title": title, "proposer": proposer, "tier": ptier}),
                    now,
                ),
            )
            conn.commit()

        return self.get_proposal(pid) or {}

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full proposal record, ballot metrics, and current voting status."""
        key = proposal_id.strip()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM proposals WHERE id = ? OR LOWER(title) = LOWER(?)",
                (key, key),
            )
            row = cur.fetchone()
            if not row:
                return None

            # Fetch votes cast on this proposal
            cur_votes = conn.execute(
                "SELECT voter_id, choice, weight, ballot_hash, created_at FROM votes WHERE proposal_id = ?",
                (row["id"],),
            )
            votes_list = [
                {
                    "voter": v["voter_id"],
                    "choice": v["choice"],
                    "weight": v["weight"],
                    "ballot_hash": v["ballot_hash"],
                    "cast_at": v["created_at"],
                }
                for v in cur_votes.fetchall()
            ]

            return {
                "id": row["id"],
                "title": row["title"],
                "description": row["description"],
                "amendment_text": row["amendment_text"],
                "proposer": row["proposer"],
                "tier": row["tier"],
                "co_sponsors": json.loads(row["co_sponsors"]),
                "status": row["status"],
                "threshold_percent": row["threshold_percent"],
                "quorum_min": row["quorum_min"],
                "results": json.loads(row["results"]),
                "votes_count": len(votes_list),
                "votes": votes_list,
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }

    def list_proposals(
        self,
        status: str = "all",
        tier: str = "all",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List proposals with optional status and tier filters."""
        filters = []
        params: List[Any] = []

        if status and status != "all":
            filters.append("status = ?")
            params.append(status.strip().lower())

        if tier and tier != "all":
            filters.append("tier = ?")
            params.append(tier.strip().lower())

        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        sql = f"SELECT * FROM proposals {where} ORDER BY created_at DESC LIMIT ?"
        params.append(int(limit))

        with self._get_connection() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for r in rows:
            res = json.loads(r["results"])
            results.append({
                "id": r["id"],
                "title": r["title"],
                "proposer": r["proposer"],
                "tier": r["tier"],
                "status": r["status"],
                "threshold_percent": r["threshold_percent"],
                "quorum_min": r["quorum_min"],
                "yes_weight": res.get("yes_weight", 0.0),
                "no_weight": res.get("no_weight", 0.0),
                "created_at": r["created_at"],
            })
        return results

    def cast_vote(
        self,
        proposal_id: str,
        voter: str,
        choice: str,
        weight: float = 1.0,
    ) -> Dict[str, Any]:
        """Record a weighted vote with deterministic SHA-256 cryptographic ballot hash."""
        prop = self.get_proposal(proposal_id)
        if not prop:
            return {"success": False, "error": f"Proposal '{proposal_id}' not found"}

        if prop["status"] not in ("draft", "voting"):
            return {
                "success": False,
                "error": f"Proposal is '{prop['status']}', voting is closed",
            }

        pchoice = choice.strip().lower()
        if pchoice not in self.VALID_CHOICES:
            return {
                "success": False,
                "error": f"Invalid choice '{choice}'. Must be one of {sorted(self.VALID_CHOICES)}",
            }

        pvoter = voter.strip().lower() or "voter-anonymous"
        pweight = max(0.1, float(weight))
        now = datetime.now(timezone.utc).isoformat()
        vid = f"vote_{uuid.uuid4().hex[:10]}"

        # Compute tamper-evident ballot hash
        hash_seed = f"{prop['id']}:{pvoter}:{pchoice}:{pweight:.4f}:{now}"
        ballot_hash = hashlib.sha256(hash_seed.encode("utf-8")).hexdigest()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO votes (id, proposal_id, voter_id, choice, weight, ballot_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(proposal_id, voter_id) DO UPDATE SET
                    choice = excluded.choice,
                    weight = excluded.weight,
                    ballot_hash = excluded.ballot_hash,
                    created_at = excluded.created_at
                """,
                (vid, prop["id"], pvoter, pchoice, pweight, ballot_hash, now),
            )
            conn.commit()

        # Update and return tallied status
        return self.tally_votes(prop["id"])

    def tally_votes(self, proposal_id: str) -> Dict[str, Any]:
        """Compute participation quorum, supermajority satisfaction, and finalize verdict."""
        prop = self.get_proposal(proposal_id)
        if not prop:
            return {"success": False, "error": f"Proposal '{proposal_id}' not found"}

        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT choice, weight FROM votes WHERE proposal_id = ?",
                (prop["id"],),
            )
            rows = cur.fetchall()

        total_voters = len(rows)
        yes_w = sum(r["weight"] for r in rows if r["choice"] == "yes")
        no_w = sum(r["weight"] for r in rows if r["choice"] == "no")
        abstain_w = sum(r["weight"] for r in rows if r["choice"] == "abstain")
        recuse_w = sum(r["weight"] for r in rows if r["choice"] == "recuse")

        quorum_reached = total_voters >= prop["quorum_min"]
        decisive_weight = yes_w + no_w

        if decisive_weight > 0:
            yes_percent = (yes_w / decisive_weight) * 100.0
        else:
            yes_percent = 0.0

        passed = quorum_reached and (yes_percent >= prop["threshold_percent"])

        # Determine new status if proposal was voting
        current_status = prop["status"]
        if current_status == "voting" and quorum_reached:
            new_status = "passed" if passed else "rejected"
        else:
            new_status = current_status

        results = {
            "total_votes": total_voters,
            "yes_weight": round(yes_w, 2),
            "no_weight": round(no_w, 2),
            "abstain_weight": round(abstain_w, 2),
            "recuse_weight": round(recuse_w, 2),
            "yes_percent": round(yes_percent, 2),
            "threshold_percent": prop["threshold_percent"],
            "quorum_min": prop["quorum_min"],
            "quorum_reached": quorum_reached,
            "passed": passed,
            "enacted": prop.get("results", {}).get("enacted", False),
        }

        now = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE proposals SET results = ?, status = ?, updated_at = ? WHERE id = ?",
                (json.dumps(results), new_status, now, prop["id"]),
            )
            conn.commit()

        return {
            "success": True,
            "proposal_id": prop["id"],
            "title": prop["title"],
            "tier": prop["tier"],
            "status": new_status,
            "results": results,
            "updated_at": now,
        }

    def get_status(self) -> Dict[str, Any]:
        """Return operational health, tier thresholds, and proposal count distribution."""
        with self._get_connection() as conn:
            cur_tot = conn.execute("SELECT COUNT(*) as c FROM proposals")
            total = int(cur_tot.fetchone()["c"] or 0)

            cur_votes = conn.execute("SELECT COUNT(*) as c FROM votes")
            total_votes = int(cur_votes.fetchone()["c"] or 0)

            cur_passed = conn.execute("SELECT COUNT(*) as c FROM proposals WHERE status IN ('passed', 'enacted')")
            passed = int(cur_passed.fetchone()["c"] or 0)

            cur_voting = conn.execute("SELECT COUNT(*) as c FROM proposals WHERE status = 'voting'")
            voting = int(cur_voting.fetchone()["c"] or 0)

        return {
            "status": "HEALTHY",
            "db_path": str(self.db_path),
            "total_proposals": total,
            "active_voting": voting,
            "passed_or_enacted": passed,
            "total_ballots_cast": total_votes,
            "tier_specifications": self.TIER_SPECS,
        }


# Global singleton instance
_governance_engine: Optional[GovernanceEngine] = None


def get_governance_engine() -> GovernanceEngine:
    """Get or instantiate the global GovernanceEngine singleton."""
    global _governance_engine
    if _governance_engine is None:
        _governance_engine = GovernanceEngine()
    return _governance_engine
