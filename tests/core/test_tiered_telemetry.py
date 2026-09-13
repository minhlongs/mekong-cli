"""Tests for Tiered Telemetry Storage (Netdata DBENGINE-inspired)."""

import json
from dataclasses import dataclass, field
from typing import Any

from src.core.telemetry import (
    ExecutionTrace,
    StepTrace,
    TelemetryCollector,
    TieredTelemetryStore,
)


class TestTieredTelemetryStore:
    """Test tiered storage: Tier 0 (full), Tier 1 (summary), Tier 2 (archive)."""

    def _make_trace(self, goal: str = "test goal") -> ExecutionTrace:
        return ExecutionTrace(
            goal=goal,
            steps=[
                StepTrace(step_order=1, title="step1", duration_seconds=1.5, exit_code=0),
                StepTrace(step_order=2, title="step2", duration_seconds=2.0, exit_code=0,
                          self_healed=True),
                StepTrace(step_order=3, title="step3", duration_seconds=0.5, exit_code=1),
            ],
            total_duration=4.0,
            llm_calls=2,
            errors=["step3 failed"],
        )

    def test_store_trace_tier0(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        trace = self._make_trace()
        path = store.store_trace(trace)
        assert path.exists()
        data = json.loads(path.read_text())
        assert data["goal"] == "test goal"
        assert len(data["steps"]) == 3

    def test_summarize_to_tier1(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        trace = self._make_trace()
        summary = store.summarize_to_tier1(trace)
        assert summary["goal"] == "test goal"
        assert summary["step_count"] == 3
        assert summary["success_count"] == 2
        assert summary["self_healed"] == 1
        assert summary["error_count"] == 1
        assert summary["llm_calls"] == 2
        # Check file exists
        tier1_dir = tmp_path / "tier1"
        assert tier1_dir.exists()
        jsonl_files = list(tier1_dir.glob("summary-*.jsonl"))
        assert len(jsonl_files) == 1

    def test_summarize_appends_to_same_day(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        store.summarize_to_tier1(self._make_trace("goal1"))
        store.summarize_to_tier1(self._make_trace("goal2"))
        tier1_dir = tmp_path / "tier1"
        jsonl_files = list(tier1_dir.glob("summary-*.jsonl"))
        assert len(jsonl_files) == 1  # Same day = same file
        lines = jsonl_files[0].read_text().strip().splitlines()
        assert len(lines) == 2

    def test_get_recent_summaries(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        for i in range(5):
            store.summarize_to_tier1(self._make_trace(f"goal-{i}"))
        summaries = store.get_recent_summaries(limit=3)
        assert len(summaries) == 3

    def test_get_recent_summaries_empty(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        assert store.get_recent_summaries() == []

    def test_cleanup_expired_removes_old_files(self, tmp_path):
        import time
        store = TieredTelemetryStore(str(tmp_path))
        # Create a tier0 file
        tier0 = tmp_path / "tier0"
        tier0.mkdir(parents=True)
        old_file = tier0 / "trace-old.json"
        old_file.write_text("{}")
        # Set modification time to 30 days ago (beyond 14-day retention)
        old_mtime = time.time() - (30 * 86400)
        import os
        os.utime(old_file, (old_mtime, old_mtime))
        removed = store.cleanup_expired()
        assert removed == 1
        assert not old_file.exists()

    def test_cleanup_keeps_recent_files(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        tier0 = tmp_path / "tier0"
        tier0.mkdir(parents=True)
        recent_file = tier0 / "trace-recent.json"
        recent_file.write_text("{}")
        removed = store.cleanup_expired()
        assert removed == 0
        assert recent_file.exists()

    def test_compact_to_tier2_empty(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        assert store.compact_to_tier2() == 0

    def test_tier_directories(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        assert store._tier_dir(0) == tmp_path / "tier0"
        assert store._tier_dir(1) == tmp_path / "tier1"
        assert store._tier_dir(2) == tmp_path / "tier2"

    def test_store_trace_serializes_dataclass_fields(self, tmp_path):
        """``_serialize_obj`` walks ``__dataclass_fields__`` when it encounters
        a raw dataclass value (asdict leaves nested dataclasses intact only
        when they are declared as fields)."""
        from dataclasses import dataclass

        @dataclass
        class Nested:
            value: int = 7

        @dataclass
        class TraceWithExtra(ExecutionTrace):  # type: ignore[misc]
            extra: Any = field(default_factory=Nested)

        store = TieredTelemetryStore(str(tmp_path))
        trace = TraceWithExtra(goal="dc", extra=Nested())

        path = store.store_trace(trace)
        data = json.loads(path.read_text())
        assert data["extra"]["value"] == 7

    def test_store_trace_handles_circular_self_reference(self, tmp_path):
        """A field whose value IS the trace itself is rendered as a sentinel
        rather than recursing forever."""
        @dataclass
        class TraceWithSelf(ExecutionTrace):  # type: ignore[misc]
            self_ref: Any = None

        store = TieredTelemetryStore(str(tmp_path))
        trace = TraceWithSelf(goal="circular")
        trace.self_ref = trace

        path = store.store_trace(trace)
        data = json.loads(path.read_text())
        assert data["self_ref"] == {"__ref__": "circular_reference"}

    def test_store_trace_falls_back_to_str_for_unknown_types(self, tmp_path):
        """Objects with no dataclass fields, no json-native type, and no
        iteration protocol are stringified verbatim."""
        class Custom:
            def __str__(self) -> str:
                return "custom-render"

        @dataclass
        class TraceWithCustom(ExecutionTrace):  # type: ignore[misc]
            custom: Any = None

        store = TieredTelemetryStore(str(tmp_path))
        trace = TraceWithCustom(goal="str")
        trace.custom = Custom()

        path = store.store_trace(trace)
        data = json.loads(path.read_text())
        assert data["custom"] == "custom-render"

    def test_compact_to_tier2_archives_old_summaries(self, tmp_path):
        import os
        import time
        store = TieredTelemetryStore(str(tmp_path))
        tier1 = tmp_path / "tier1"
        tier1.mkdir(parents=True)
        tier2 = tmp_path / "tier2"
        tier2.mkdir(parents=True)

        old = tier1 / "summary-20200101.jsonl"
        old.write_text('{"goal": "old goal"}\n')
        old_mtime = time.time() - (200 * 86400)
        os.utime(old, (old_mtime, old_mtime))

        compacted = store.compact_to_tier2()
        assert compacted == 1
        assert not old.exists()
        archives = list(tier2.glob("archive-*.jsonl"))
        assert len(archives) == 1
        assert "old goal" in archives[0].read_text()

    def test_compact_to_tier2_skips_unparseable_filenames(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        tier1 = tmp_path / "tier1"
        tier1.mkdir(parents=True)
        # Stem that does not parse as a date -> skipped, not archived.
        (tier1 / "summary-notadate.jsonl").write_text("{}")

        assert store.compact_to_tier2() == 0
        assert (tier1 / "summary-notadate.jsonl").exists()

    def test_compact_to_tier2_keeps_recent_summaries(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        tier1 = tmp_path / "tier1"
        tier1.mkdir(parents=True)
        (tier1 / "summary-20990101.jsonl").write_text('{"goal": "future"}')

        assert store.compact_to_tier2() == 0
        assert (tier1 / "summary-20990101.jsonl").exists()

    def test_cleanup_expired_across_all_tiers(self, tmp_path):
        import os
        import time
        store = TieredTelemetryStore(str(tmp_path))
        old_mtime = time.time() - (400 * 86400)

        for tier in (0, 1, 2):
            tier_dir = tmp_path / f"tier{tier}"
            tier_dir.mkdir(parents=True)
            f = tier_dir / f"stale-{tier}.json"
            f.write_text("{}")
            os.utime(f, (old_mtime, old_mtime))

        removed = store.cleanup_expired()
        assert removed == 3

    def test_get_recent_summaries_skips_malformed_lines(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        tier1 = tmp_path / "tier1"
        tier1.mkdir(parents=True)
        (tier1 / "summary-20200101.jsonl").write_text(
            '{"goal": "good"}\nnot-json\n{"goal": "also good"}\n'
        )

        summaries = store.get_recent_summaries(limit=10)
        assert len(summaries) == 2
        assert all(s["goal"] in ("good", "also good") for s in summaries)

    def test_get_recent_summaries_respects_limit(self, tmp_path):
        store = TieredTelemetryStore(str(tmp_path))
        tier1 = tmp_path / "tier1"
        tier1.mkdir(parents=True)
        (tier1 / "summary-20200101.jsonl").write_text(
            "\n".join('{"goal": "g%d"}' % i for i in range(5)) + "\n"
        )

        summaries = store.get_recent_summaries(limit=2)
        assert len(summaries) == 2

    def test_store_trace_circular_field_nested_not_trace(self, tmp_path):
        """A circular reference to the trace must render as the sentinel even
        when reached through a list, not only as a direct field value."""
        @dataclass
        class TraceWithList(ExecutionTrace):  # type: ignore[misc]
            refs: Any = None

        store = TieredTelemetryStore(str(tmp_path))
        trace = TraceWithList(goal="nested")
        trace.refs = [trace]

        path = store.store_trace(trace)
        data = json.loads(path.read_text())
        assert data["refs"] == [{"__ref__": "circular_reference"}]

    def test_store_trace_non_dataclass_object_uses_asdict(self, tmp_path):
        """``store_trace`` falls back to ``asdict()`` for non-dataclass traces
        (duck-typed objects with a goal attribute)."""
        class DuckTrace:
            def __init__(self) -> None:
                self.goal = "duck"
                self.steps: list[Any] = []
                self.total_duration = 1.0
                self.llm_calls = 0
                self.errors: list[str] = []

        store = TieredTelemetryStore(str(tmp_path))
        path = store.store_trace(DuckTrace())  # type: ignore[arg-type]
        data = json.loads(path.read_text())
        assert data["goal"] == "duck"


class TestTelemetryCollectorIntegration:
    """Test TelemetryCollector with tiered store integration."""

    def test_full_trace_lifecycle(self, tmp_path):
        collector = TelemetryCollector(output_dir=str(tmp_path))
        collector.start_trace("deploy app")
        collector.record_step(1, "Install deps", 2.5, 0)
        collector.record_step(2, "Build", 5.0, 0, self_healed=True)
        collector.record_llm_call()
        collector.record_error("minor warning")
        trace = collector.finish_trace()
        assert trace is not None
        assert trace.goal == "deploy app"
        assert len(trace.steps) == 2
        assert trace.llm_calls == 1
        assert len(trace.errors) == 1
