"""Unit Tests for UsageTracker — unified SQLite + event-bus metering."""

import pytest
from unittest.mock import MagicMock

from src.usage.usage_tracker import (
    UsageTracker,
    UsageEvent,
    UsageEventType,
    AnomalyCategory,
    DailyUsage,
    get_tracker,
)


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_db(tmp_path):
    """Provide a temp SQLite DB path."""
    return tmp_path / "test.db"


def _make_tracker(tmp_db):
    """Create a UsageTracker backed by temp DB with event bus mocked."""
    t = UsageTracker(db_path=tmp_db)
    # Patch metering to avoid real event bus / anomaly detector
    t._api_call_count = 0
    t._agent_spawn_count = 0
    t._llm_call_count = 0
    t._total_input_tokens = 0
    t._total_output_tokens = 0
    t._detector = MagicMock()
    t._detector.detect_anomaly.return_value = None
    t._event_bus = MagicMock()
    return t


# ── UsageEvent dataclass ────────────────────────────────────────────────────

class TestUsageEvent:

    def test_creation(self):
        """UsageEvent requires event_type (enum), category (enum), metric, value."""
        event = UsageEvent(
            event_type=UsageEventType.API_CALL,
            category=AnomalyCategory.API_CALLS,
            metric="chat/completions",
            value=1.0,
        )
        assert event.event_type == UsageEventType.API_CALL
        assert event.category == AnomalyCategory.API_CALLS
        assert event.metric == "chat/completions"
        assert event.value == 1.0
        assert event.metadata == {}
        assert isinstance(event.timestamp, float)
        assert event.timestamp > 0

    def test_creation_with_metadata(self):
        """Metadata dict is stored as-is."""
        event = UsageEvent(
            event_type=UsageEventType.MODEL_USAGE,
            category=AnomalyCategory.MODEL_USAGE,
            metric="qwen3.5-plus",
            value=1500.0,
            metadata={"model": "qwen"},
        )
        assert event.metadata["model"] == "qwen"

    def test_to_dict(self):
        """to_dict serializes enum values to strings."""
        event = UsageEvent(
            event_type=UsageEventType.TOKEN_USAGE,
            category=AnomalyCategory.TOKEN_USAGE,
            metric="gpt-4o",
            value=500.0,
        )
        d = event.to_dict()
        assert d["event_type"] == "usage:token_usage"
        assert d["category"] == "token_usage"
        assert d["metric"] == "gpt-4o"
        assert d["value"] == 500.0


# ── UsageTracker — track_command ──────────────────────────────────────────

class TestTrackCommand:

    @pytest.mark.asyncio
    async def test_track_command_inserts_row(self, tmp_db):
        """track_command inserts a row into usage_events."""
        tracker = _make_tracker(tmp_db)
        before = tracker._conn.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
        await tracker.track_command(license_key="lic-1", command="cook")
        after = tracker._conn.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
        assert after == before + 1

    @pytest.mark.asyncio
    async def test_track_command_with_key_id(self, tmp_db):
        """key_id is used as license when license_key is None."""
        tracker = _make_tracker(tmp_db)
        await tracker.track_command(key_id="my-key", command="plan")

    @pytest.mark.asyncio
    async def test_track_command_with_metadata(self, tmp_db):
        """Metadata is passed through to _track_event."""
        tracker = _make_tracker(tmp_db)
        await tracker.track_command(
            license_key="lic-1",
            command="deploy",
            metadata={"exit_code": 0},
        )


# ── UsageTracker — track_feature ──────────────────────────────────────────

class TestTrackFeature:

    @pytest.mark.asyncio
    async def test_track_feature_inserts_row(self, tmp_db):
        """track_feature inserts a feature event row."""
        tracker = _make_tracker(tmp_db)
        await tracker.track_feature(feature_tag="bmc", license_key="lic-1")


# ── UsageTracker — event-bus metering ─────────────────────────────────────

class TestEventBusMetering:

    def test_record_api_call(self, tmp_db):
        """record_api_call increments api_call_count and emits event."""
        tracker = _make_tracker(tmp_db)
        tracker.record_api_call("chat/completions")
        assert tracker._api_call_count == 1

    def test_record_llm_call(self, tmp_db):
        """record_llm_call increments llm_call_count."""
        tracker = _make_tracker(tmp_db)
        tracker.record_llm_call(model="gpt-4o", input_tokens=100, output_tokens=200)
        assert tracker._llm_call_count == 1

    def test_record_token_usage(self, tmp_db):
        """record_token_usage accumulates input + output tokens."""
        tracker = _make_tracker(tmp_db)
        tracker.record_token_usage("qwen3.5-plus", input_tokens=300, output_tokens=200)
        assert tracker._total_input_tokens == 300
        assert tracker._total_output_tokens == 200

    def test_get_usage_summary(self, tmp_db):
        """get_usage_summary returns dict with expected keys."""
        tracker = _make_tracker(tmp_db)
        tracker.record_api_call("endpoint")
        tracker.record_llm_call(model="m", input_tokens=10, output_tokens=20)
        summary = tracker.get_usage_summary()
        assert summary["api_calls"] == 1
        assert summary["llm_calls"] == 1
        assert summary["total_tokens"] == 30

    def test_reset_counters(self, tmp_db):
        """reset_counters zeroes all counters."""
        tracker = _make_tracker(tmp_db)
        tracker.record_api_call("x")
        tracker.reset_counters()
        assert tracker.get_usage_summary()["api_calls"] == 0


# ── UsageTracker — get_daily_usage ─────────────────────────────────────────

class TestGetDailyUsage:

    def test_returns_dataclass(self, tmp_db):
        """get_daily_usage returns a DailyUsage dataclass instance."""
        tracker = _make_tracker(tmp_db)
        result = tracker.get_daily_usage(license_key="lic-1")
        assert isinstance(result, DailyUsage)

    def test_daily_usage_fields(self, tmp_db):
        """DailyUsage has expected fields."""
        tracker = _make_tracker(tmp_db)
        usage = tracker.get_daily_usage(license_key="lic-1")
        assert isinstance(usage.date, str)
        assert isinstance(usage.total_commands, int)
        assert isinstance(usage.command_breakdown, dict)


# ── UsageTracker — singleton ──────────────────────────────────────────────

class TestGlobalTracker:

    def test_get_tracker_singleton(self):
        """get_tracker returns same instance on repeated calls."""
        t1 = get_tracker()
        t2 = get_tracker()
        assert t1 is t2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
