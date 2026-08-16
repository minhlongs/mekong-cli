# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for the ZenOS behavior graph module."""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

from src.mekong.graph.api import detect_collusion, get_status, get_trust, record_behavior
from src.mekong.graph.collusion import detect_deal_rotation, detect_market_allocation, detect_price_parallelism
from src.mekong.graph.store import find_collusion, get_behavior_count, open_db
from src.mekong.graph.trust import compute_trust


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def db_path() -> str:
    """Create a temporary database file."""
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "test_graph.db")
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)
    os.rmdir(tmp)


def _uid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Test: record behavior
# ---------------------------------------------------------------------------


class TestRecordBehavior:
    def test_record_simple(self, db_path: str) -> None:
        src_id = _uid()
        tgt_id = _uid()
        result = record_behavior(
            source_id=src_id,
            source_name="alice",
            target_id=tgt_id,
            target_name="bob",
            action="trade",
            value=42.0,
            db_path=db_path,
        )
        assert result["status"] == "recorded"
        assert isinstance(result["behavior_id"], int)
        assert result["behavior_id"] > 0

    def test_record_with_payload(self, db_path: str) -> None:
        src_id = _uid()
        tgt_id = _uid()
        result = record_behavior(
            source_id=src_id,
            source_name="carol",
            target_id=tgt_id,
            target_name="dave",
            action="refer",
            payload={"channel": "email", "code": "FRIEND10"},
            value=0.0,
            db_path=db_path,
        )
        assert result["status"] == "recorded"

    def test_multiple_behaviors(self, db_path: str) -> None:
        src_id = _uid()
        tgt_id = _uid()
        for i in range(3):
            record_behavior(
                source_id=src_id,
                source_name="eve",
                target_id=tgt_id,
                target_name="frank",
                action="trade",
                value=float(i),
                db_path=db_path,
            )
        conn = open_db(db_path)
        try:
            count = get_behavior_count(conn, src_id, tgt_id)
            assert count == 3
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Test: trust computation
# ---------------------------------------------------------------------------


class TestTrustComputation:
    def test_cold_start(self, db_path: str) -> None:
        src_id = _uid()
        tgt_id = _uid()
        # Record fewer than 10 behaviors
        for _ in range(3):
            record_behavior(
                source_id=src_id,
                source_name="alice",
                target_id=tgt_id,
                target_name="bob",
                action="trade",
                value=1.0,
                db_path=db_path,
            )

        result = get_trust(source_id=src_id, target_id=tgt_id, db_path=db_path)
        assert result["score"] == 50  # cold start neutral
        assert result["confidence"] == 30  # 3 * 10
        assert result["cold_start"] is True
        assert result["behavior_count"] == 3

    def test_full_computation(self, db_path: str) -> None:
        """After 10+ behaviors, the full trust formula runs."""
        src_id = _uid()
        tgt_id = _uid()
        for i in range(12):
            record_behavior(
                source_id=src_id,
                source_name="alice",
                target_id=tgt_id,
                target_name="bob",
                action="trade",
                value=float(i % 5),
                db_path=db_path,
            )

        result = get_trust(source_id=src_id, target_id=tgt_id, db_path=db_path)
        assert 0 <= result["score"] <= 100
        assert 0 <= result["confidence"] <= 100
        assert result["cold_start"] is False
        assert result["behavior_count"] == 12

    def test_trust_score_is_int(self, db_path: str) -> None:
        """Trust score must always be an integer, never a float."""
        src_id = _uid()
        tgt_id = _uid()
        for _ in range(15):
            record_behavior(
                source_id=src_id,
                source_name="alice",
                target_id=tgt_id,
                target_name="bob",
                action="trade",
                value=1.0,
                db_path=db_path,
            )

        result = get_trust(source_id=src_id, target_id=tgt_id, db_path=db_path)
        assert isinstance(result["score"], int)
        assert isinstance(result["confidence"], int)

    def test_trust_score_clamped(self, db_path: str) -> None:
        """Score must never exceed 100 or go below 0."""
        src_id = _uid()
        tgt_id = _uid()

        # Directly upsert out-of-range via trust formula (negative penalty)
        # Use compute_trust which should clamp
        conn = open_db(db_path)
        try:
            from src.mekong.graph.store import ensure_entity

            ensure_entity(conn, src_id, "clamp_test_a")
            ensure_entity(conn, tgt_id, "clamp_test_b")

            # Insert a collusion flag to drive penalty up
            conn.execute(
                """INSERT INTO collusion_flags (pattern, entity_a_id, entity_b_id, evidence, severity)
                   VALUES ('test', ?, ?, '{}', 'critical')""",
                (src_id, tgt_id),
            )
            conn.commit()

            # Record enough behaviors to pass cold start
            for _ in range(12):
                from src.mekong.graph.store import record_behavior as rb

                rb(conn, src_id, tgt_id, "trade", value=100.0)

            score, confidence = compute_trust(conn, src_id, tgt_id)
            assert 0 <= score <= 100
            assert 0 <= confidence <= 100
        finally:
            conn.close()

    def test_anti_concentration(self, db_path: str) -> None:
        """Anti-concentration: two entities with zero interaction should have cold-start trust."""
        src_id = _uid()
        tgt_id = _uid()
        # No behaviors recorded between them
        result = get_trust(source_id=src_id, target_id=tgt_id, db_path=db_path)
        assert result["score"] == 50
        assert result["behavior_count"] == 0


# ---------------------------------------------------------------------------
# Test: collusion detection
# ---------------------------------------------------------------------------


class TestCollusionDetection:
    def test_price_parallelism(self, db_path: str) -> None:
        src_id = _uid()
        tgt_id = _uid()
        src2_id = _uid()  # Two entities setting same price = collusion pattern
        # Record 4 behaviors from 2 different source entities at same price
        for src in [src_id, src2_id, src_id, src2_id]:
            record_behavior(
                source_id=src,
                source_name="alice",
                target_id=tgt_id,
                target_name="bob",
                action="set_price",
                value=99.99,
                db_path=db_path,
            )

        conn = open_db(db_path)
        try:
            flags = detect_price_parallelism(conn, min_occurrences=3)
            assert len(flags) >= 1
            assert flags[0].pattern == "price_parallelism"
        finally:
            conn.close()

    def test_deal_rotation(self, db_path: str) -> None:
        a_id = _uid()
        b_id = _uid()

        conn = open_db(db_path)
        try:
            from src.mekong.graph.store import ensure_entity, record_behavior as rb

            ensure_entity(conn, a_id, "alice")
            ensure_entity(conn, b_id, "bob")

            # Alternating bid_wins: A, B, A, B, A
            rb(conn, a_id, b_id, "bid_win", value=1.0)
            rb(conn, b_id, a_id, "bid_win", value=2.0)
            rb(conn, a_id, b_id, "bid_win", value=3.0)
            rb(conn, b_id, a_id, "bid_win", value=4.0)
            rb(conn, a_id, b_id, "bid_win", value=5.0)

            flags = detect_deal_rotation(conn, min_transactions=3)
            assert len(flags) >= 1
            assert flags[0].pattern == "deal_rotation"
        finally:
            conn.close()

    def test_market_allocation(self, db_path: str) -> None:
        a_id = _uid()
        b_id = _uid()
        x_id = _uid()
        y_id = _uid()

        conn = open_db(db_path)
        try:
            from src.mekong.graph.store import ensure_entity, record_behavior as rb

            ensure_entity(conn, a_id, "alice")
            ensure_entity(conn, b_id, "bob")
            ensure_entity(conn, x_id, "xavier")
            ensure_entity(conn, y_id, "yvonne")

            # Alice only trades with X, Bob only trades with Y — zero overlap
            rb(conn, a_id, x_id, "trade", value=1.0)
            rb(conn, a_id, x_id, "trade", value=2.0)
            rb(conn, b_id, y_id, "trade", value=10.0)
            rb(conn, b_id, y_id, "trade", value=20.0)

            flags = detect_market_allocation(conn)
            assert len(flags) >= 1
            assert flags[0].pattern == "market_allocation"
        finally:
            conn.close()

    def test_detect_all(self, db_path: str) -> None:
        """Running all detectors via API should not raise."""
        # Insert a few behaviors first
        a_id = _uid()
        b_id = _uid()
        record_behavior(
            source_id=a_id,
            source_name="alice",
            target_id=b_id,
            target_name="bob",
            action="trade",
            db_path=db_path,
        )

        results = detect_collusion(db_path=db_path)
        assert isinstance(results, list)

    def test_query_existing_flags(self, db_path: str) -> None:
        """Flags from previous runs are queryable."""
        src_id = _uid()
        tgt_id = _uid()

        conn = open_db(db_path)
        try:
            from src.mekong.graph.store import ensure_entity, insert_collusion_flag

            ensure_entity(conn, src_id, "alice")
            ensure_entity(conn, tgt_id, "bob")
            insert_collusion_flag(
                conn,
                pattern="price_parallelism",
                entity_a_id=src_id,
                entity_b_id=tgt_id,
                evidence={"test": True},
                severity="low",
            )

            flags = find_collusion(conn, pattern="price_parallelism")
            assert len(flags) >= 1
            assert flags[0].pattern == "price_parallelism"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Test: empty graph cold start
# ---------------------------------------------------------------------------


class TestEmptyGraphColdStart:
    def test_empty_graph_trust_is_neutral(self, db_path: str) -> None:
        """Two entities with zero recorded interactions get neutral trust."""
        a_id = _uid()
        b_id = _uid()
        result = get_trust(source_id=a_id, target_id=b_id, db_path=db_path)
        assert result["score"] == 50
        assert result["cold_start"] is True
        assert result["behavior_count"] == 0

    def test_empty_graph_status(self, db_path: str) -> None:
        """Status on an empty graph should show zero counts."""
        status = get_status(db_path=db_path)
        assert status["entities"] == 0
        assert status["behaviors"] == 0
        assert status["trust_scores"] == 0
        assert status["active_collusion_flags"] == 0


# ---------------------------------------------------------------------------
# Test: anti-concentration
# ---------------------------------------------------------------------------


class TestAntiConcentration:
    def test_entities_with_zero_interaction(self, db_path: str) -> None:
        """Anti-concentration: entities with zero shared behaviors get neutral trust, not 0."""
        a_id = _uid()
        b_id = _uid()

        # Alice is very active with Carol
        c_id = _uid()
        for _ in range(15):
            record_behavior(
                source_id=a_id,
                source_name="alice",
                target_id=c_id,
                target_name="carol",
                action="trade",
                db_path=db_path,
            )

        # Bob is unknown — no interaction with Alice
        result = get_trust(source_id=a_id, target_id=b_id, db_path=db_path)
        assert result["score"] == 50  # neutral, not adversarial
        assert result["cold_start"] is True


# ---------------------------------------------------------------------------
# Test: trust_scores are INTEGER not REAL
# ---------------------------------------------------------------------------


class TestTrustSchema:
    def test_trust_score_column_type(self, db_path: str) -> None:
        """Verify the trust_scores.score column is INTEGER via schema introspection."""
        conn = open_db(db_path)
        try:
            col_info = conn.execute("PRAGMA table_info(trust_scores)").fetchall()
            score_col = [c for c in col_info if c["name"] == "score"]
            assert len(score_col) == 1
            # SQLite reports type as TEXT/INTEGER/REAL/BLOB
            assert score_col[0]["type"] == "INTEGER", (
                f"Expected INTEGER, got {score_col[0]['type']}"
            )

            confidence_col = [c for c in col_info if c["name"] == "confidence"]
            assert confidence_col[0]["type"] == "INTEGER"
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Multi-particle network tests
# ---------------------------------------------------------------------------


class TestMultiParticleNetwork:
    """Tests for multi-particle network operations (connect, status, strategist)."""

    @pytest.fixture
    def particle_alpha(self, tmp_path: Path) -> Path:
        """Create a minimal alpha particle directory (no ZENOS.md needed for connect)."""
        p = tmp_path / "alpha"
        p.mkdir(parents=True)
        return p

    @pytest.fixture
    def particle_beta(self, tmp_path: Path) -> Path:
        """Create a minimal beta particle directory."""
        p = tmp_path / "beta"
        p.mkdir(parents=True)
        return p

    @pytest.fixture
    def strategist_particle(self, tmp_path: Path) -> Path:
        """Create a particle with ZENOS.md constitution and cells/strategist.yaml.

        Used by ``test_cross_strategist`` which requires the full particle
        layout including cell config and constitution files.
        """
        particle_dir = tmp_path / "test-particle"
        particle_dir.mkdir(parents=True)

        # Write constitution
        constitution = """# ZENOS.md — Test Particle

## Article 1: Mission Integrity

The particle exists to serve testing and learning.

## Article 2: Governance

Decisions are made by consensus.

## Article 3: AI Cell Boundaries

Cells operate within defined privilege limits.

## Article 4: Right to Exit

Any participant may exit at any time.

## Article 5: Behavioral Integrity

The particle shall resist anti-concentration patterns.
"""
        (particle_dir / "ZENOS.md").write_text(constitution, encoding="utf-8")

        # Write strategist cell config
        cells_dir = particle_dir / "cells"
        cells_dir.mkdir(parents=True)
        config_yaml = yaml.dump({
            "role": "strategist",
            "model": "anthropic/claude-sonnet-4",
            "capabilities": ["analysis", "recommendation"],
            "privileges": {"max_budget": 100.0, "requires_approval": False},
            "boundaries": {"read": ["particle/*"], "write": ["particle/reports/*"]},
        })
        (cells_dir / "strategist.yaml").write_text(config_yaml, encoding="utf-8")

        return particle_dir

    @pytest.fixture
    def connected_db(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> str:
        """Connect alpha and beta and return the DB path."""
        from src.mekong.graph.network import connect_particles

        os.chdir(str(particle_alpha.parent))
        connect_particles(
            str(particle_alpha),
            str(particle_beta),
            db_path=db_path,
        )
        return db_path

    # ------------------------------------------------------------------
    # test_connect_particles
    # ------------------------------------------------------------------

    def test_connect_particles_creates_entities(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """Connecting two particles registers both as entities in the graph."""
        from src.mekong.graph.network import connect_particles

        os.chdir(str(particle_alpha.parent))
        result = connect_particles(
            str(particle_alpha),
            str(particle_beta),
            db_path=db_path,
        )

        assert result["status"] == "connected"
        assert result["particle_a"]["name"] == "alpha"
        assert result["particle_b"]["name"] == "beta"

        # Both entities exist in the DB
        conn = open_db(db_path)
        try:
            alpha_ent = conn.execute(
                "SELECT * FROM entities WHERE id = ?", ("particle:alpha",)
            ).fetchone()
            beta_ent = conn.execute(
                "SELECT * FROM entities WHERE id = ?", ("particle:beta",)
            ).fetchone()
            assert alpha_ent is not None
            assert alpha_ent["name"] == "alpha"
            assert beta_ent is not None
            assert beta_ent["name"] == "beta"
        finally:
            conn.close()

    def test_connect_particles_trust_scores(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """Connecting particles creates trust scores in both directions."""
        from src.mekong.graph.network import connect_particles

        os.chdir(str(particle_alpha.parent))
        result = connect_particles(
            str(particle_alpha),
            str(particle_beta),
            db_path=db_path,
        )

        # Trust keys exist and are within valid range
        trust = result["trust"]
        assert "alpha_to_beta" in trust
        assert "beta_to_alpha" in trust
        a_to_b, b_to_a = trust["alpha_to_beta"], trust["beta_to_alpha"]
        assert isinstance(a_to_b, int)
        assert isinstance(b_to_a, int)
        assert 0 <= a_to_b <= 100
        assert 0 <= b_to_a <= 100

        # Cold start: 1 behavior per direction -> confidence = 10
        assert a_to_b == 50
        assert b_to_a == 50

    def test_connect_particles_records_behaviors(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """Connecting particles records bidirectional ``particle_connect`` behaviors."""
        from src.mekong.graph.network import connect_particles

        os.chdir(str(particle_alpha.parent))
        connect_particles(
            str(particle_alpha),
            str(particle_beta),
            db_path=db_path,
        )

        conn = open_db(db_path)
        try:
            # Alpha -> beta
            rows = conn.execute(
                "SELECT * FROM behaviors WHERE source_id = ? AND target_id = ? AND action = ?",
                ("particle:alpha", "particle:beta", "particle_connect"),
            ).fetchall()
            assert len(rows) == 1

            # Beta -> alpha
            rows = conn.execute(
                "SELECT * FROM behaviors WHERE source_id = ? AND target_id = ? AND action = ?",
                ("particle:beta", "particle:alpha", "particle_connect"),
            ).fetchall()
            assert len(rows) == 1
        finally:
            conn.close()

    def test_connect_particles_twice_is_idempotent(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """Connecting the same pair a second time adds more behaviors but does
        not error."""
        from src.mekong.graph.network import connect_particles

        os.chdir(str(particle_alpha.parent))
        connect_particles(str(particle_alpha), str(particle_beta), db_path=db_path)
        connect_particles(str(particle_alpha), str(particle_beta), db_path=db_path)

        conn = open_db(db_path)
        try:
            count = conn.execute(
                "SELECT COUNT(*) AS c FROM behaviors WHERE action = 'particle_connect'",
            ).fetchone()["c"]
            assert count == 4  # 2 connections * 2 directions
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # test_network_status
    # ------------------------------------------------------------------

    def test_network_status_shows_counterparties(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """After connecting, particle status shows the counterparty."""
        from src.mekong.graph.network import connect_particles, particle_network_status

        os.chdir(str(particle_alpha.parent))
        connect_particles(str(particle_alpha), str(particle_beta), db_path=db_path)

        status = particle_network_status(str(particle_alpha), db_path=db_path)

        assert status["particle"]["name"] == "alpha"
        assert status["behaviors_count"] >= 1
        assert "particle:beta" in status["counterparties"]

    def test_network_status_behaviors(
        self,
        connected_db: str,
        particle_alpha: Path,
    ) -> None:
        """Connected particle's status lists the connection behavior."""
        from src.mekong.graph.network import particle_network_status

        os.chdir(str(particle_alpha.parent))
        status = particle_network_status(str(particle_alpha), db_path=connected_db)

        assert status["behaviors_count"] >= 1
        actions = {b["action"] for b in status["behaviors"]}
        assert "particle_connect" in actions

    def test_network_status_trust(
        self,
        connected_db: str,
        particle_alpha: Path,
    ) -> None:
        """Connected particle's status shows outgoing and incoming trust."""
        from src.mekong.graph.network import particle_network_status

        os.chdir(str(particle_alpha.parent))
        status = particle_network_status(str(particle_alpha), db_path=connected_db)

        assert len(status["outgoing_trust"]) >= 1
        assert len(status["incoming_trust"]) >= 1

        outgoing_scores = {t["target_id"]: t["score"] for t in status["outgoing_trust"]}
        assert "particle:beta" in outgoing_scores
        assert 0 <= outgoing_scores["particle:beta"] <= 100

    # ------------------------------------------------------------------
    # test_cross_strategist
    # ------------------------------------------------------------------

    def test_cross_strategist_network_context(
        self,
        strategist_particle: Path,
    ) -> None:
        """Cross-particle strategist includes network context when particles
        are connected.  The LLM is mocked; we verify the system prompt would
        contain the trust network block."""
        from unittest.mock import patch as _patch

        from src.mekong.graph.network import connect_particles, cross_particle_strategist

        # Create a connected beta particle
        beta_dir = strategist_particle.parent / "beta"
        beta_dir.mkdir()
        (beta_dir / "ZENOS.md").write_text(
            "# Beta\n\n## Article 1: Mission\n\nAudio AI for SEA.\n",
            encoding="utf-8",
        )
        cells_dir = beta_dir / "cells"
        cells_dir.mkdir()
        config_yaml = yaml.dump({
            "role": "strategist",
            "model": "anthropic/claude-sonnet-4",
            "capabilities": ["analysis"],
            "privileges": {"max_budget": 100.0, "requires_approval": False},
            "boundaries": {"read": ["particle/*"], "write": []},
        })
        (cells_dir / "strategist.yaml").write_text(config_yaml, encoding="utf-8")

        db_path = str(strategist_particle.parent / "test.db")

        os.chdir(str(strategist_particle.parent))
        connect_particles(
            str(strategist_particle),
            str(beta_dir),
            db_path=db_path,
        )

        # Mock the LLM call to verify network context is included
        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendation": "Partner with beta for audio-video synergy",
                        "confidence": 0.85,
                        "rationale": "Strategic alignment between video and audio AI",
                        "risk_factors": ["Integration complexity"],
                        "estimated_impact": "high",
                    }),
                },
            }],
        }

        with _patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=False):
            with _patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response

                result = cross_particle_strategist(
                    particle_id=str(strategist_particle),
                    question="Should we partner with beta?",
                    db_path=db_path,
                )

        assert result["network_context"]["peer_count"] >= 1
        peers = result["network_context"]["peers"]
        assert any("beta" in p["target_name"] for p in peers)

        # Recommendation is present
        rec = result["recommendation"]
        assert "recommendation" in rec
        assert rec["recommendation"] == "Partner with beta for audio-video synergy"
        assert rec["confidence"] == 0.85
        assert "Integration complexity" in rec["risk_factors"]

    def test_cross_strategist_no_network_context(
        self,
        strategist_particle: Path,
    ) -> None:
        """Cross-particle strategist with no connected peers includes empty
        network context."""
        from unittest.mock import patch as _patch

        from src.mekong.graph.network import cross_particle_strategist

        db_path = str(strategist_particle.parent / "test.db")

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendation": "Go it alone for now",
                        "confidence": 0.7,
                        "rationale": "No trusted peers identified",
                        "risk_factors": ["Slower growth"],
                        "estimated_impact": "medium",
                    }),
                },
            }],
        }

        with _patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=False):
            with _patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response

                result = cross_particle_strategist(
                    particle_id=str(strategist_particle),
                    question="What should we do?",
                    db_path=db_path,
                )

        assert result["network_context"]["peer_count"] == 0
        assert result["network_context"]["peers"] == []

    def test_cross_strategist_records_behavior(
        self,
        strategist_particle: Path,
    ) -> None:
        """Cross-particle strategist records a behavior graph entry."""
        from unittest.mock import patch as _patch

        from src.mekong.graph.network import connect_particles, cross_particle_strategist

        # Create a connected beta particle
        beta_dir = strategist_particle.parent / "beta"
        beta_dir.mkdir()
        (beta_dir / "ZENOS.md").write_text(
            "# Beta\n\n## Article 1: Mission\n\nAudio AI for SEA.\n",
            encoding="utf-8",
        )
        cells_dir = beta_dir / "cells"
        cells_dir.mkdir()
        config_yaml = yaml.dump({
            "role": "strategist",
            "model": "anthropic/claude-sonnet-4",
            "capabilities": ["analysis"],
            "privileges": {"max_budget": 100.0, "requires_approval": False},
            "boundaries": {"read": ["particle/*"], "write": []},
        })
        (cells_dir / "strategist.yaml").write_text(config_yaml, encoding="utf-8")

        db_path = str(strategist_particle.parent / "test.db")

        os.chdir(str(strategist_particle.parent))
        connect_particles(
            str(strategist_particle),
            str(beta_dir),
            db_path=db_path,
        )

        mock_response = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "recommendation": "Collaborate on cross-modal AI",
                        "confidence": 0.8,
                        "rationale": "Combined video+audio creates moat",
                        "risk_factors": [],
                        "estimated_impact": "high",
                    }),
                },
            }],
        }

        with _patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}, clear=False):
            with _patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                mock_post.return_value.json.return_value = mock_response
                with _patch("src.mekong.graph.network.record_behavior") as mock_record:
                    cross_particle_strategist(
                        particle_id=str(strategist_particle),
                        question="Should we collaborate?",
                        db_path=db_path,
                    )

        mock_record.assert_called_once()
        call_kwargs = mock_record.call_args.kwargs
        assert call_kwargs["action"] == "network_strategist_recommendation"
        assert "cell:" in call_kwargs["source_id"]

    # ------------------------------------------------------------------
    # test_particle_isolation
    # ------------------------------------------------------------------

    def test_particle_isolation_no_trust(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """Unconnected particles have no trust scores in the graph."""
        # Register both entities but do NOT connect them
        conn = open_db(db_path)
        try:
            from src.mekong.graph.store import ensure_entity

            ensure_entity(conn, "particle:alpha", "alpha")
            ensure_entity(conn, "particle:beta", "beta")
        finally:
            conn.close()

        # Verify no trust scores exist
        conn = open_db(db_path)
        try:
            scores = conn.execute(
                "SELECT * FROM trust_scores WHERE source_id = 'particle:alpha' AND target_id = 'particle:beta'"
            ).fetchall()
            assert len(scores) == 0

            # And no behaviors between them
            behaviors = conn.execute(
                "SELECT * FROM behaviors WHERE source_id = 'particle:alpha' AND target_id = 'particle:beta'"
            ).fetchall()
            assert len(behaviors) == 0
        finally:
            conn.close()

    def test_particle_isolation_cold_start_trust(
        self,
        particle_alpha: Path,
        particle_beta: Path,
        db_path: str,
    ) -> None:
        """Unconnected particles get neutral cold-start trust (50) when queried
        via get_trust."""
        from src.mekong.graph.api import get_trust

        trust = get_trust(
            source_id="particle:alpha",
            target_id="particle:beta",
            db_path=db_path,
        )
        assert trust["score"] == 50  # cold start neutral
        assert trust["cold_start"] is True
        assert trust["behavior_count"] == 0

    def test_particle_isolation_status(
        self,
        particle_alpha: Path,
        db_path: str,
    ) -> None:
        """A particle that has not interacted with anyone shows zero behaviors
        and no counterparties."""
        # Register the entity
        conn = open_db(db_path)
        try:
            from src.mekong.graph.store import ensure_entity

            ensure_entity(conn, "particle:alpha", "alpha")
        finally:
            conn.close()

        from src.mekong.graph.api import get_status

        status = get_status(db_path=db_path)
        assert status["entities"] >= 1
        assert status["behaviors"] == 0
        assert status["trust_scores"] == 0
