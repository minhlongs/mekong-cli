# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
src/core/founder_engine.py — Autonomous Founder Genome & Psychometric Profiling Engine.
Pure Python standard library implementation with zero external HTTP or vendor dependencies.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class FounderEngine:
    """Autonomous Founder Genome & Psychometric Profiling Engine.

    Manages founder assessment profiles, TIPI-10 Big Five personality trait normalization,
    Schwartz core values, risk appetite scoring, cognitive bias extraction, and team archetype
    matching with SQLite WAL persistence.
    """

    # TIPI-10 item mapping: (normal_item, reverse_item)
    TIPI_DIMENSIONS: Dict[str, Tuple[str, str]] = {
        "extraversion": ("tipi_01", "tipi_06"),
        "agreeableness": ("tipi_07", "tipi_02"),
        "conscientiousness": ("tipi_03", "tipi_08"),
        "emotional_stability": ("tipi_09", "tipi_04"),
        "openness": ("tipi_05", "tipi_10"),
    }

    TIPI_REVERSE_ITEMS: set[str] = {"tipi_02", "tipi_04", "tipi_06", "tipi_08", "tipi_10"}

    RISK_DIMENSIONS: List[str] = [
        "financial",
        "operational",
        "reputational",
        "compliance",
        "technical",
    ]

    BIAS_MAP: Dict[str, str] = {
        "bias_confirmation": "confirmation_bias",
        "bias_overconfidence": "overconfidence",
        "bias_sunk_cost": "sunk_cost_fallacy",
        "bias_planning": "planning_fallacy",
        "bias_self_serving": "self_serving_bias",
        "bias_anchoring": "anchoring",
        "bias_availability": "availability_heuristic",
        "bias_framing": "framing_effect",
        "bias_status_quo": "status_quo_bias",
        "bias_optimism": "optimism_bias",
    }

    # Pre-seeded canonical founder archetypes
    DEFAULT_FOUNDERS: List[Dict[str, Any]] = [
        {
            "name": "sovereign-architect",
            "mission": "Build resilient, decentralized, self-governing software engines for sovereign operators.",
            "particle_id": "ptc_zenos_001",
            "values": ["self_direction", "achievement", "security"],
            "big_five": {
                "openness": 92,
                "conscientiousness": 88,
                "extraversion": 54,
                "agreeableness": 65,
                "emotional_stability": 84,
                "neuroticism": 17,
            },
            "fears": [
                {
                    "trigger": "Vendor lock-in or platform deplatforming",
                    "predicted_behavior": "Over-engineering redundant local fallback systems",
                    "mitigation": "Establish strict standard-library boundaries and right-to-fork charters",
                }
            ],
            "risk_profile": {
                "financial": 60,
                "operational": 70,
                "reputational": 50,
                "compliance": 80,
                "technical": 90,
            },
            "cognitive_biases": ["overconfidence", "planning_fallacy"],
            "risk_level": "moderate",
            "archetype": "Sovereign Architect",
            "notes": ["Demonstrates high technical conviction with systematic failover planning."],
        },
        {
            "name": "growth-evangelist",
            "mission": "Rapidly scale agentic workflows to thousands of global enterprises with viral distribution.",
            "particle_id": "ptc_growth_002",
            "values": ["stimulation", "achievement", "power"],
            "big_five": {
                "openness": 88,
                "conscientiousness": 62,
                "extraversion": 94,
                "agreeableness": 72,
                "emotional_stability": 75,
                "neuroticism": 26,
            },
            "fears": [
                {
                    "trigger": "Missing market momentum or slowing user adoption",
                    "predicted_behavior": "Deploying features before full architectural stabilization",
                    "mitigation": "Enforce automated CI/CD gating and pre-push validation test suites",
                }
            ],
            "risk_profile": {
                "financial": 85,
                "operational": 80,
                "reputational": 75,
                "compliance": 60,
                "technical": 80,
            },
            "cognitive_biases": ["optimism_bias", "availability_heuristic"],
            "risk_level": "aggressive",
            "archetype": "Growth Evangelist",
            "notes": ["Thrives on momentum and high-velocity shipping; benefits from operational counterbalances."],
        },
        {
            "name": "pragmatic-operator",
            "mission": "Ensure flawless operational execution, deterministic financial close, and 99.99% system reliability.",
            "particle_id": "ptc_ops_003",
            "values": ["security", "conformity", "benevolence"],
            "big_five": {
                "openness": 58,
                "conscientiousness": 96,
                "extraversion": 45,
                "agreeableness": 85,
                "emotional_stability": 90,
                "neuroticism": 11,
            },
            "fears": [
                {
                    "trigger": "Unreconciled ledger variances or unmonitored production failures",
                    "predicted_behavior": "Excessive manual verification gating leading to shipping bottlenecks",
                    "mitigation": "Deploy automated reconciliation cron jobs and telemetry dashboards",
                }
            ],
            "risk_profile": {
                "financial": 30,
                "operational": 40,
                "reputational": 35,
                "compliance": 25,
                "technical": 50,
            },
            "cognitive_biases": ["status_quo_bias", "sunk_cost_fallacy"],
            "risk_level": "conservative",
            "archetype": "Pragmatic Operator",
            "notes": ["Exemplary governance and fiscal rigor; safeguards runway and organizational trust."],
        },
    ]

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize SQLite database for founder genome ledger."""
        if db_path is None:
            db_dir = Path(".mekong")
            db_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = db_dir / "founder.db"
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
                CREATE TABLE IF NOT EXISTS founders (
                    id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    mission TEXT NOT NULL,
                    version TEXT NOT NULL,
                    particle_id TEXT,
                    core_values TEXT NOT NULL,
                    big_five TEXT NOT NULL,
                    fears TEXT NOT NULL,
                    risk_profile TEXT NOT NULL,
                    cognitive_biases TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    archetype TEXT NOT NULL,
                    notes TEXT NOT NULL,
                    assessed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS founder_assessments (
                    id TEXT PRIMARY KEY,
                    founder_id TEXT NOT NULL,
                    assessment_type TEXT NOT NULL,
                    raw_payload TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Pre-seed default archetypal founders if database is empty
            cur = conn.execute("SELECT COUNT(*) as count FROM founders")
            if cur.fetchone()["count"] == 0:
                now = datetime.now(timezone.utc).isoformat()
                for f in self.DEFAULT_FOUNDERS:
                    fid = f"fnd_{uuid.uuid4().hex[:12]}"
                    conn.execute(
                        """
                        INSERT INTO founders (
                            id, name, mission, version, particle_id, core_values,
                            big_five, fears, risk_profile, cognitive_biases,
                            risk_level, archetype, notes, assessed_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            fid,
                            f["name"],
                            f["mission"],
                            "1.0.0",
                            f["particle_id"],
                            json.dumps(f["values"]),
                            json.dumps(f["big_five"]),
                            json.dumps(f["fears"]),
                            json.dumps(f["risk_profile"]),
                            json.dumps(f["cognitive_biases"]),
                            f["risk_level"],
                            f["archetype"],
                            json.dumps(f["notes"]),
                            now,
                            now,
                        ),
                    )
            conn.commit()

    # ---------------------------------------------------------------------------
    # Psychometric Scoring Algorithms
    # ---------------------------------------------------------------------------

    def score_big_five(self, responses: Optional[Dict[str, int]]) -> Dict[str, int]:
        """Score Big Five traits (1-100 scale) from TIPI-10 responses (1-7 Likert)."""
        res = responses or {}
        result: Dict[str, int] = {}

        for dim_key, (normal_id, reverse_id) in self.TIPI_DIMENSIONS.items():
            normal_val = res.get(normal_id, 4)
            reverse_val = res.get(reverse_id, 4)

            # Invert reverse-scored items
            if normal_id in self.TIPI_REVERSE_ITEMS:
                normal_val = 8 - normal_val
            if reverse_id in self.TIPI_REVERSE_ITEMS:
                reverse_val = 8 - reverse_val

            raw_sum = normal_val + reverse_val  # range: 2-14
            normalized = int(round(((raw_sum - 2) / 12) * 99 + 1))
            normalized = max(1, min(100, normalized))
            result[dim_key] = normalized

        # Derived Neuroticism
        result["neuroticism"] = max(1, 101 - result["emotional_stability"])
        return result

    def score_risk_profile(self, ratings: Optional[Dict[str, int]]) -> Dict[str, int]:
        """Normalize risk ratings across dimensions (1-10 input to 10-100 score)."""
        r = ratings or {}
        return {
            dim: max(10, min(100, int(r.get(dim, 5)) * 10))
            for dim in self.RISK_DIMENSIONS
        }

    def extract_biases(self, bias_responses: Optional[Dict[str, bool]]) -> List[str]:
        """Extract identified cognitive biases from boolean responses."""
        if not bias_responses:
            return []
        biases: List[str] = []
        for qid, present in bias_responses.items():
            if present:
                mapped = self.BIAS_MAP.get(qid, qid.replace("bias_", ""))
                biases.append(mapped)
        return biases

    def classify_risk_level(self, bias_count: int, risk_scores: Dict[str, int]) -> str:
        """Classify overall risk appetite (conservative, moderate, aggressive)."""
        avg_risk = sum(risk_scores.values()) / max(1, len(risk_scores)) / 10.0
        if bias_count <= 3 or avg_risk < 4.0:
            return "conservative"
        if bias_count <= 6 or avg_risk < 7.0:
            return "moderate"
        return "aggressive"

    def determine_archetype(self, big_five: Dict[str, int], values: List[str]) -> str:
        """Synthesize primary founder archetype based on personality and core values."""
        openness = big_five.get("openness", 50)
        conscientiousness = big_five.get("conscientiousness", 50)
        extraversion = big_five.get("extraversion", 50)

        if openness >= 80 and "self_direction" in values:
            return "Sovereign Architect"
        if extraversion >= 80 and ("stimulation" in values or "achievement" in values):
            return "Growth Evangelist"
        if conscientiousness >= 80 and ("security" in values or "conformity" in values):
            return "Pragmatic Operator"
        if openness >= 75 and conscientiousness >= 75:
            return "Technical Visionary"
        return "Autonomous Generalist"

    # ---------------------------------------------------------------------------
    # Core Assessment Engine API
    # ---------------------------------------------------------------------------

    def assess_founder(
        self,
        name: str,
        mission: str = "",
        tipi_responses: Optional[Dict[str, int]] = None,
        values: Optional[List[str]] = None,
        fears: Optional[List[Dict[str, Any]]] = None,
        risk_ratings: Optional[Dict[str, int]] = None,
        bias_responses: Optional[Dict[str, bool]] = None,
        particle_id: Optional[str] = None,
        notes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Run or record a full founder assessment with psychometric synthesis."""
        fname = name.strip().lower()
        if not fname:
            raise ValueError("Founder name or identifier cannot be empty")

        fmission = mission.strip() or f"Mission of {fname}"
        vals = values or ["self_direction", "achievement"]
        frs = fears or []
        fnotes = notes or ["Self-reported psychometric screening profile."]

        big_five = self.score_big_five(tipi_responses)
        risk_profile = self.score_risk_profile(risk_ratings)
        biases = self.extract_biases(bias_responses)
        risk_level = self.classify_risk_level(len(biases), risk_profile)
        archetype = self.determine_archetype(big_five, vals)

        now = datetime.now(timezone.utc).isoformat()
        fid = f"fnd_{uuid.uuid4().hex[:12]}"
        asmt_id = f"asmt_{uuid.uuid4().hex[:12]}"

        raw_payload = {
            "tipi_responses": tipi_responses or {},
            "values": vals,
            "fears": frs,
            "risk_ratings": risk_ratings or {},
            "bias_responses": bias_responses or {},
        }

        with self._get_connection() as conn:
            cur = conn.execute("SELECT id FROM founders WHERE name = ?", (fname,))
            existing = cur.fetchone()
            if existing:
                fid = existing["id"]
                conn.execute(
                    """
                    UPDATE founders SET
                        mission = ?, particle_id = ?, core_values = ?, big_five = ?,
                        fears = ?, risk_profile = ?, cognitive_biases = ?,
                        risk_level = ?, archetype = ?, notes = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        fmission,
                        particle_id,
                        json.dumps(vals),
                        json.dumps(big_five),
                        json.dumps(frs),
                        json.dumps(risk_profile),
                        json.dumps(biases),
                        risk_level,
                        archetype,
                        json.dumps(fnotes),
                        now,
                        fid,
                    ),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO founders (
                        id, name, mission, version, particle_id, core_values,
                        big_five, fears, risk_profile, cognitive_biases,
                        risk_level, archetype, notes, assessed_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        fid,
                        fname,
                        fmission,
                        "1.0.0",
                        particle_id,
                        json.dumps(vals),
                        json.dumps(big_five),
                        json.dumps(frs),
                        json.dumps(risk_profile),
                        json.dumps(biases),
                        risk_level,
                        archetype,
                        json.dumps(fnotes),
                        now,
                        now,
                    ),
                )

            # Record audit assessment event
            conn.execute(
                """
                INSERT INTO founder_assessments (
                    id, founder_id, assessment_type, raw_payload, created_at
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    asmt_id,
                    fid,
                    "tipi_big_five_v1",
                    json.dumps(raw_payload),
                    now,
                ),
            )
            conn.commit()

        return self.get_founder(fname) or {}

    def get_founder(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve founder genome profile by name or ID."""
        key = name_or_id.strip().lower()
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT * FROM founders WHERE LOWER(name) = ? OR id = ?",
                (key, key),
            )
            row = cur.fetchone()
            if not row:
                return None

            return {
                "id": row["id"],
                "name": row["name"],
                "mission": row["mission"],
                "version": row["version"],
                "particle_id": row["particle_id"],
                "values": json.loads(row["core_values"]),
                "big_five": json.loads(row["big_five"]),
                "fears": json.loads(row["fears"]),
                "risk_profile": json.loads(row["risk_profile"]),
                "cognitive_biases": json.loads(row["cognitive_biases"]),
                "risk_level": row["risk_level"],
                "archetype": row["archetype"],
                "notes": json.loads(row["notes"]),
                "assessed_at": row["assessed_at"],
                "updated_at": row["updated_at"],
            }

    def list_founders(
        self,
        risk_level: str = "all",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """List assessed founder profiles with optional risk level filter."""
        filters = []
        params: List[Any] = []

        if risk_level and risk_level != "all":
            filters.append("risk_level = ?")
            params.append(risk_level.strip().lower())

        where = f"WHERE {' AND '.join(filters)}" if filters else ""
        sql = f"SELECT * FROM founders {where} ORDER BY updated_at DESC LIMIT ?"
        params.append(int(limit))

        with self._get_connection() as conn:
            cur = conn.execute(sql, params)
            rows = cur.fetchall()

        results = []
        for r in rows:
            results.append({
                "id": r["id"],
                "name": r["name"],
                "mission": r["mission"],
                "archetype": r["archetype"],
                "risk_level": r["risk_level"],
                "biases_count": len(json.loads(r["cognitive_biases"])),
                "particle_id": r["particle_id"],
                "assessed_at": r["assessed_at"],
            })
        return results

    def analyze_founder(self, name_or_id: str) -> Dict[str, Any]:
        """Generate actionable psychometric synthesis, team blindspots, and pairing recommendations."""
        f = self.get_founder(name_or_id)
        if not f:
            return {"success": False, "error": f"Founder '{name_or_id}' not found"}

        b5 = f["big_five"]
        strengths: List[str] = []
        blindspots: List[str] = []
        recommendations: List[str] = []

        # Trait evaluation
        if b5.get("openness", 0) >= 80:
            strengths.append("Exceptional vision and pattern recognition in unfamiliar markets")
        elif b5.get("openness", 0) <= 40:
            blindspots.append("May resist novel architectures or untested market wedges")

        if b5.get("conscientiousness", 0) >= 80:
            strengths.append("High execution discipline and systematic milestone delivery")
        elif b5.get("conscientiousness", 0) <= 45:
            blindspots.append("Risk of dropping administrative, tax, or legal follow-through")
            recommendations.append("Pair with a Pragmatic Operator or Chief of Staff for ops execution")

        if b5.get("emotional_stability", 0) >= 80:
            strengths.append("Calm under pressure and resilient during market volatility")
        elif b5.get("emotional_stability", 0) <= 40:
            blindspots.append("Elevated anxiety triggers during runway compression or critical bugs")

        # Bias evaluation
        biases = f["cognitive_biases"]
        if "overconfidence" in biases:
            blindspots.append("Potential overconfidence in timeline estimation and product-market fit")
            recommendations.append("Implement pre-mortems and pessimistic scenario modeling")
        if "planning_fallacy" in biases:
            recommendations.append("Apply a 1.5x buffer on critical engineering sprint timelines")

        return {
            "success": True,
            "id": f["id"],
            "name": f["name"],
            "archetype": f["archetype"],
            "risk_level": f["risk_level"],
            "personality_summary": {
                "openness": b5.get("openness"),
                "conscientiousness": b5.get("conscientiousness"),
                "extraversion": b5.get("extraversion"),
                "agreeableness": b5.get("agreeableness"),
                "emotional_stability": b5.get("emotional_stability"),
            },
            "strengths": strengths,
            "blindspots": blindspots,
            "strategic_recommendations": recommendations,
        }

    def get_status(self) -> Dict[str, Any]:
        """Return operational health, distribution, and total founder count."""
        with self._get_connection() as conn:
            cur_tot = conn.execute("SELECT COUNT(*) as c FROM founders")
            total = int(cur_tot.fetchone()["c"] or 0)

            cur_asmts = conn.execute("SELECT COUNT(*) as c FROM founder_assessments")
            asmts = int(cur_asmts.fetchone()["c"] or 0)

            cur_cons = conn.execute("SELECT COUNT(*) as c FROM founders WHERE risk_level = 'conservative'")
            cons = int(cur_cons.fetchone()["c"] or 0)

            cur_mod = conn.execute("SELECT COUNT(*) as c FROM founders WHERE risk_level = 'moderate'")
            mod = int(cur_mod.fetchone()["c"] or 0)

            cur_agg = conn.execute("SELECT COUNT(*) as c FROM founders WHERE risk_level = 'aggressive'")
            agg = int(cur_agg.fetchone()["c"] or 0)

        return {
            "status": "HEALTHY",
            "db_path": str(self.db_path),
            "total_founders": total,
            "total_assessments_logged": asmts,
            "risk_distribution": {
                "conservative": cons,
                "moderate": mod,
                "aggressive": agg,
            },
            "supported_frameworks": ["TIPI-10", "Schwartz-Values", "Cognitive-Biases-10", "Risk-5D"],
        }


# Global singleton instance
_founder_engine: Optional[FounderEngine] = None


def get_founder_engine() -> FounderEngine:
    """Get or instantiate the global FounderEngine singleton."""
    global _founder_engine
    if _founder_engine is None:
        _founder_engine = FounderEngine()
    return _founder_engine
