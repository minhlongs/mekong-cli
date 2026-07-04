"""Tests for the ZenOS behavior graph module."""

from __future__ import annotations

import json
import os
import tempfile
import uuid

import pytest

from src.mekong.graph.api import detect_collusion, get_status, get_trust, record_behavior
from src.mekong.graph.collusion import detect_deal_rotation, detect_market_allocation, detect_price_parallelism
from src.mekong.graph.store import find_collusion, get_behavior_count, get_trust_score, open_db
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
