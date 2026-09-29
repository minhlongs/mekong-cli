# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""ZenOS Autonomous Particle Lifecycle, AI Cell Runtime & Behavior Graph Engine.

Standard-library-only implementation with zero third-party or vendor dependencies,
adhering to ``tests/test_core_boundary.py``.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sqlite3
import typing
import uuid

CANONICAL_PARTICLES = [
    {
        "particle_id": "PARTICLE-SOV-001",
        "name": "sov-agent-alpha",
        "mission": "Autonomous strategic execution and resource orchestration",
        "constitution": "Operate transparently under ZenOS Article 1 & Binh Phap doctrine.",
        "template": "skel",
        "trust_score": 85.0,
    },
    {
        "particle_id": "PARTICLE-ZEN-002",
        "name": "zen-commons-nexus",
        "mission": "Constitutional governance, collective coordination, and dispute settlement",
        "constitution": "Protect common resources, arbitrate disputes, and uphold quorum rules.",
        "template": "skel",
        "trust_score": 95.0,
    },
    {
        "particle_id": "PARTICLE-AUD-003",
        "name": "audit-guardian-node",
        "mission": "Continuous constitutional auditing, telemetry inspection, and boundary validation",
        "constitution": "Verify cryptographic ballots, enforce boundary invariants, and detect collusion.",
        "template": "skel",
        "trust_score": 90.0,
    },
]


class ParticleEngine:
    """ZenOS Particle lifecycle, AI cell runtime, and behavior trust graph engine."""

    def __init__(self, db_path: str | pathlib.Path | None = None) -> None:
        if db_path is None:
            base_dir = pathlib.Path(".mekong")
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = base_dir / "particle.db"
        else:
            self.db_path = pathlib.Path(db_path)
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS particles (
                    particle_id TEXT PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    mission TEXT NOT NULL,
                    constitution TEXT NOT NULL,
                    template TEXT NOT NULL DEFAULT 'skel',
                    status TEXT NOT NULL DEFAULT 'active',
                    trust_score REAL NOT NULL DEFAULT 50.0,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS particle_connections (
                    connection_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    trust_score REAL NOT NULL DEFAULT 50.0,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    UNIQUE(source_id, target_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS particle_behaviors (
                    behavior_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    value REAL NOT NULL DEFAULT 0.0,
                    timestamp TEXT NOT NULL,
                    behavior_hash TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cell_executions (
                    execution_id TEXT PRIMARY KEY,
                    particle_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed',
                    output TEXT NOT NULL,
                    compliance_passed INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

            # Seed canonical particles if empty
            cursor = conn.execute("SELECT COUNT(*) AS cnt FROM particles")
            if cursor.fetchone()["cnt"] == 0:
                now = datetime.datetime.now(datetime.timezone.utc).isoformat()
                for p in CANONICAL_PARTICLES:
                    conn.execute(
                        """
                        INSERT INTO particles (particle_id, name, mission, constitution, template, status, trust_score, created_at, metadata)
                        VALUES (?, ?, ?, ?, ?, 'active', ?, ?, '{}')
                        """,
                        (p["particle_id"], p["name"], p["mission"], p["constitution"], p["template"], p["trust_score"], now),
                    )

                # Seed mutual connections
                conn.execute(
                    """
                    INSERT OR IGNORE INTO particle_connections (connection_id, source_id, target_id, trust_score, status, created_at)
                    VALUES
                    ('CONN-001', 'PARTICLE-SOV-001', 'PARTICLE-ZEN-002', 90.0, 'active', ?),
                    ('CONN-002', 'PARTICLE-ZEN-002', 'PARTICLE-SOV-001', 90.0, 'active', ?),
                    ('CONN-003', 'PARTICLE-ZEN-002', 'PARTICLE-AUD-003', 92.0, 'active', ?),
                    ('CONN-004', 'PARTICLE-AUD-003', 'PARTICLE-ZEN-002', 92.0, 'active', ?),
                    ('CONN-005', 'PARTICLE-AUD-003', 'PARTICLE-SOV-001', 88.0, 'active', ?),
                    ('CONN-006', 'PARTICLE-SOV-001', 'PARTICLE-AUD-003', 88.0, 'active', ?)
                    """,
                    (now, now, now, now, now, now),
                )
                conn.commit()

    def init_particle(
        self,
        name: str,
        mission: str = "",
        constitution: str = "",
        template: str = "skel",
    ) -> dict[str, typing.Any]:
        """Create and register a new ZenOS particle."""
        clean_name = name.strip().lower()
        if not clean_name:
            raise ValueError("Particle name cannot be empty.")

        particle_id = f"PARTICLE-{clean_name.upper().replace('-', '_')}-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        mission_text = mission.strip() or f"{name} autonomous particle"
        constitution_text = constitution.strip() or "Abide by ZenOS Core Constitution & transparency principles."

        with self._get_connection() as conn:
            # Check if name already exists
            cursor = conn.execute("SELECT particle_id FROM particles WHERE name = ?", (clean_name,))
            if cursor.fetchone():
                raise ValueError(f"Particle with name '{clean_name}' already exists.")

            conn.execute(
                """
                INSERT INTO particles (particle_id, name, mission, constitution, template, status, trust_score, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, 'active', 50.0, ?, '{}')
                """,
                (particle_id, clean_name, mission_text, constitution_text, template, now),
            )
            conn.commit()

        return {
            "particle_id": particle_id,
            "name": clean_name,
            "mission": mission_text,
            "constitution": constitution_text,
            "template": template,
            "status": "active",
            "trust_score": 50.0,
            "created_at": now,
        }

    def get_particle(self, particle_id_or_name: str) -> dict[str, typing.Any] | None:
        """Fetch a particle by ID or name."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM particles WHERE particle_id = ? OR name = ?",
                (particle_id_or_name, particle_id_or_name.lower()),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def list_particles(self, status: str = "all", limit: int = 50) -> list[dict[str, typing.Any]]:
        """List registered particles with optional status filter."""
        with self._get_connection() as conn:
            if status != "all":
                cursor = conn.execute(
                    "SELECT * FROM particles WHERE status = ? ORDER BY trust_score DESC, created_at DESC LIMIT ?",
                    (status, limit),
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM particles ORDER BY trust_score DESC, created_at DESC LIMIT ?",
                    (limit,),
                )
            return [dict(r) for r in cursor.fetchall()]

    def connect_particles(
        self,
        particle_a: str,
        particle_b: str,
        trust_score: float = 50.0,
    ) -> dict[str, typing.Any]:
        """Establish bidirectional trust connection between two particles."""
        p_a = self.get_particle(particle_a)
        if not p_a:
            raise ValueError(f"Particle '{particle_a}' not found.")
        p_b = self.get_particle(particle_b)
        if not p_b:
            raise ValueError(f"Particle '{particle_b}' not found.")

        id_a, id_b = p_a["particle_id"], p_b["particle_id"]
        if id_a == id_b:
            raise ValueError("A particle cannot connect to itself.")

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn_1 = f"CONN-{str(uuid.uuid4())[:8].upper()}"
        conn_2 = f"CONN-{str(uuid.uuid4())[:8].upper()}"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO particle_connections (connection_id, source_id, target_id, trust_score, status, created_at)
                VALUES (?, ?, ?, ?, 'active', ?)
                ON CONFLICT(source_id, target_id) DO UPDATE SET trust_score = ?, status = 'active'
                """,
                (conn_1, id_a, id_b, trust_score, now, trust_score),
            )
            conn.execute(
                """
                INSERT INTO particle_connections (connection_id, source_id, target_id, trust_score, status, created_at)
                VALUES (?, ?, ?, ?, 'active', ?)
                ON CONFLICT(source_id, target_id) DO UPDATE SET trust_score = ?, status = 'active'
                """,
                (conn_2, id_b, id_a, trust_score, now, trust_score),
            )
            conn.commit()

        # Record connection behavior
        self.record_behavior(id_a, id_b, "connect", value=trust_score)
        self.record_behavior(id_b, id_a, "connect", value=trust_score)

        return {
            "status": "connected",
            "particle_a": p_a["name"],
            "particle_b": p_b["name"],
            "trust_score": trust_score,
            "connected_at": now,
        }

    def record_behavior(
        self,
        source: str,
        target: str,
        action: str,
        value: float = 0.0,
    ) -> dict[str, typing.Any]:
        """Record an interactive behavior between two entities with cryptographic hash."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        behavior_id = f"BEH-{str(uuid.uuid4())[:8].upper()}"
        raw_hash = f"{behavior_id}:{source}:{target}:{action}:{value}:{now}"
        behavior_hash = hashlib.sha256(raw_hash.encode("utf-8")).hexdigest()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO particle_behaviors (behavior_id, source_id, target_id, action, value, timestamp, behavior_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (behavior_id, source, target, action, value, now, behavior_hash),
            )
            conn.commit()

        return {
            "behavior_id": behavior_id,
            "source_id": source,
            "target_id": target,
            "action": action,
            "value": value,
            "timestamp": now,
            "hash": behavior_hash,
        }

    def get_particle_status(self, particle_id_or_name: str) -> dict[str, typing.Any]:
        """Retrieve complete status for a particle including network connections and behaviors."""
        particle = self.get_particle(particle_id_or_name)
        if not particle:
            raise ValueError(f"Particle '{particle_id_or_name}' not found.")

        pid = particle["particle_id"]
        with self._get_connection() as conn:
            # Active connections
            c_cursor = conn.execute(
                """
                SELECT c.*, p.name AS target_name, p.status AS target_status
                FROM particle_connections c
                JOIN particles p ON c.target_id = p.particle_id
                WHERE c.source_id = ? AND c.status = 'active'
                """,
                (pid,),
            )
            connections = [dict(r) for r in c_cursor.fetchall()]

            # Recent behaviors
            b_cursor = conn.execute(
                """
                SELECT * FROM particle_behaviors
                WHERE source_id = ? OR target_id = ?
                ORDER BY timestamp DESC LIMIT 10
                """,
                (pid, pid),
            )
            recent_behaviors = [dict(r) for r in b_cursor.fetchall()]

            # Cell execution count
            exec_cursor = conn.execute(
                "SELECT COUNT(*) AS cnt, SUM(compliance_passed) AS passed FROM cell_executions WHERE particle_id = ?",
                (pid,),
            )
            exec_stats = exec_cursor.fetchone()
            total_execs = exec_stats["cnt"] or 0
            passed_execs = exec_stats["passed"] or 0

        collusion_data = self.detect_collusion(pid)

        return {
            "particle": particle,
            "connections_count": len(connections),
            "connections": connections,
            "recent_behaviors": recent_behaviors,
            "cell_executions": {
                "total": total_execs,
                "compliance_passed": passed_execs,
            },
            "collusion_detected": collusion_data["collusion_detected"],
            "risk_score": collusion_data["risk_score"],
        }

    def detect_collusion(self, particle_id_or_name: str = "") -> dict[str, typing.Any]:
        """Heuristic collusion and circular endorsement detection across particles."""
        target_pid = ""
        if particle_id_or_name:
            p = self.get_particle(particle_id_or_name)
            if p:
                target_pid = p["particle_id"]

        with self._get_connection() as conn:
            if target_pid:
                cursor = conn.execute(
                    """
                    SELECT source_id, target_id, action, COUNT(*) as cnt
                    FROM particle_behaviors
                    WHERE source_id = ? OR target_id = ?
                    GROUP BY source_id, target_id, action
                    """,
                    (target_pid, target_pid),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT source_id, target_id, action, COUNT(*) as cnt
                    FROM particle_behaviors
                    GROUP BY source_id, target_id, action
                    """
                )
            records = [dict(r) for r in cursor.fetchall()]

        # Heuristic: Check if endorsement velocity between any 2 particles is excessive (> 20)
        flags: list[dict[str, typing.Any]] = []
        for r in records:
            if r["cnt"] > 20:
                flags.append({
                    "source": r["source_id"],
                    "target": r["target_id"],
                    "action": r["action"],
                    "frequency": r["cnt"],
                    "reason": "Excessive mutual interaction velocity",
                })

        collusion_detected = len(flags) > 0
        risk_score = min(100.0, len(flags) * 25.0)

        return {
            "collusion_detected": collusion_detected,
            "risk_score": risk_score,
            "flagged_interactions": flags,
            "evaluated_records": len(records),
        }

    def run_cell(
        self,
        role: str,
        prompt: str,
        particle_id: str = "default",
        auto_compliance: bool = False,
    ) -> dict[str, typing.Any]:
        """Execute an autonomous AI cell role within particle constitutional context."""
        clean_role = role.strip().lower()
        valid_roles = {"strategist", "compliance", "executor", "evaluator"}
        if clean_role not in valid_roles:
            raise ValueError(f"Invalid cell role '{clean_role}'. Must be one of: {', '.join(sorted(valid_roles))}")

        # Resolve particle
        p = None
        if particle_id not in ("default", ""):
            p = self.get_particle(particle_id)
        if not p:
            # Default to first active particle
            particles = self.list_particles(limit=1)
            p = particles[0] if particles else CANONICAL_PARTICLES[0]

        exec_id = f"CELL-{clean_role.upper()[:4]}-{str(uuid.uuid4())[:8].upper()}"
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Deterministic simulation output
        summary = (
            f"AI Cell [{clean_role}] executed successfully on particle [{p['name']}]. "
            f"Prompt: '{prompt[:60]}...'. Constitutional directives applied."
        )
        compliance_passed = 1
        if auto_compliance and "violate" in prompt.lower():
            compliance_passed = 0
            summary += " [Constitutional Violation Warning Triggered]"

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO cell_executions (execution_id, particle_id, role, prompt, status, output, compliance_passed, created_at)
                VALUES (?, ?, ?, ?, 'completed', ?, ?, ?)
                """,
                (exec_id, p["particle_id"], clean_role, prompt, summary, compliance_passed, now),
            )
            conn.commit()

        return {
            "execution_id": exec_id,
            "particle_id": p["particle_id"],
            "particle_name": p["name"],
            "role": clean_role,
            "prompt": prompt,
            "output": summary,
            "compliance_passed": bool(compliance_passed),
            "executed_at": now,
        }

    def get_status(self) -> dict[str, typing.Any]:
        """Aggregate overview telemetry across ZenOS particles and runtime cells."""
        with self._get_connection() as conn:
            p_cursor = conn.execute("SELECT COUNT(*) AS total, AVG(trust_score) AS avg_trust FROM particles")
            p_stats = p_cursor.fetchone()
            total_particles = p_stats["total"] or 0
            avg_trust = round(p_stats["avg_trust"] or 50.0, 1)

            c_cursor = conn.execute("SELECT COUNT(*) AS total FROM particle_connections WHERE status = 'active'")
            total_connections = c_cursor.fetchone()["total"] or 0

            b_cursor = conn.execute("SELECT COUNT(*) AS total FROM particle_behaviors")
            total_behaviors = b_cursor.fetchone()["total"] or 0

            cell_cursor = conn.execute("SELECT COUNT(*) AS total, SUM(compliance_passed) AS passed FROM cell_executions")
            cell_stats = cell_cursor.fetchone()
            total_cells = cell_stats["total"] or 0
            passed_cells = cell_stats["passed"] or 0

        particles = self.list_particles(limit=10)

        return {
            "total_particles": total_particles,
            "active_connections": total_connections,
            "recorded_behaviors": total_behaviors,
            "average_trust_score": avg_trust,
            "cell_executions": {
                "total": total_cells,
                "compliance_passed": passed_cells,
            },
            "recent_particles": particles,
            "status": "operational",
        }
