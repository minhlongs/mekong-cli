# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Coverage tests for dag_scheduler, cost_tracker, command_loader,
memory_store_adapter, config, and usage_metering modules.

Iteration 20 of the progressive coverage loop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── dag_scheduler ───────────────────────────────────────────────────────
from src.core.dag_scheduler import (
    DAGScheduler,
    DAGStepResult,
    validate_dag,
)

# ── cost_tracker ────────────────────────────────────────────────────────
from src.core.cost_tracker import (
    MODEL_PRICES,
    CostEntry,
    CostTracker,
    SpendSummary,
    get_cost_tracker,
)

# ── command_loader ──────────────────────────────────────────────────────
from src.core.command_loader import (
    Command,
    _parse_frontmatter,
    build_system_prompt,
    find_best_command,
    get_commands,
    load_all_commands,
)

# ── memory_store_adapter ────────────────────────────────────────────────
from src.core.memory_store_adapter import (
    MemoryStoreAdapter,
)

# ── usage_metering ──────────────────────────────────────────────────────
from src.core.usage_metering import (
    AnomalyCategory,
    UsageAnomalyDetector,
    UsageEvent,
    UsageEventType,
    UsageMetering,
    get_detector,
    get_metering,
    get_tracker,
    reset_metering,
)


# =========================================================================
# Helpers
# =========================================================================
@dataclass
class DummyStep:
    order: int
    name: str = ""
    dependencies: list[int] | None = None


@dataclass
class DummyVerification:
    passed: bool


@dataclass
class DummyResult:
    verification: DummyVerification


# =========================================================================
# dag_scheduler.py — 220 lines
# =========================================================================
class TestDAGStepResult:
    def test_fields(self) -> None:
        r = DAGStepResult(order=1, success=True, result="res", error=None)
        assert r.order == 1
        assert r.success is True
        assert r.result == "res"
        assert r.error is None


class TestDAGScheduler:
    def test_empty_steps(self) -> None:
        sched = DAGScheduler([])
        assert sched.get_ready_steps() == []
        assert sched.is_done() is True
        assert sched.has_dependencies() is False
        assert sched.cancelled_steps == set()

    def test_has_dependencies(self) -> None:
        steps = [
            DummyStep(order=1, dependencies=[]),
            DummyStep(order=2, dependencies=[1]),
        ]
        sched = DAGScheduler(steps)
        assert sched.has_dependencies() is True

    def test_has_no_dependencies(self) -> None:
        steps = [
            DummyStep(order=1, dependencies=[]),
            DummyStep(order=2, dependencies=None),
        ]
        sched = DAGScheduler(steps)
        assert sched.has_dependencies() is False

    def test_get_ready_steps_dependency_order(self) -> None:
        s1 = DummyStep(order=1, dependencies=[])
        s2 = DummyStep(order=2, dependencies=[1])
        sched = DAGScheduler([s1, s2])

        # Initially, only s1 is ready
        ready = sched.get_ready_steps()
        assert len(ready) == 1
        assert ready[0].order == 1

        # Mark 1 completed -> s2 becomes ready
        sched.mark_completed(1)
        ready2 = sched.get_ready_steps()
        assert len(ready2) == 1
        assert ready2[0].order == 2

    def test_mark_failed_cancels_transitive_downstream(self) -> None:
        s1 = DummyStep(order=1, dependencies=[])
        s2 = DummyStep(order=2, dependencies=[1])
        s3 = DummyStep(order=3, dependencies=[2])
        sched = DAGScheduler([s1, s2, s3])

        sched.mark_failed(1)
        assert 2 in sched.cancelled_steps
        assert 3 in sched.cancelled_steps
        assert sched.is_done() is True
        assert sched.get_ready_steps() == []

    def test_execute_all_success(self) -> None:
        s1 = DummyStep(order=1, dependencies=[])
        s2 = DummyStep(order=2, dependencies=[1])
        sched = DAGScheduler([s1, s2])

        completed_log = []

        def executor(step):
            return DummyResult(verification=DummyVerification(passed=True))

        def on_complete(order, res):
            completed_log.append((order, res.success))

        results = sched.execute_all(executor, on_complete=on_complete)
        assert len(results) == 2
        assert results[1].success is True
        assert results[2].success is True
        assert completed_log == [(1, True), (2, True)]

    def test_execute_all_step_failure(self) -> None:
        s1 = DummyStep(order=1, dependencies=[])
        s2 = DummyStep(order=2, dependencies=[1])
        sched = DAGScheduler([s1, s2])

        def executor(step):
            if step.order == 1:
                return DummyResult(verification=DummyVerification(passed=False))
            return DummyResult(verification=DummyVerification(passed=True))

        results = sched.execute_all(executor)
        assert results[1].success is False
        assert 2 in sched.cancelled_steps

    def test_execute_all_step_exception(self) -> None:
        s1 = DummyStep(order=1, dependencies=[])
        sched = DAGScheduler([s1])

        def executor(step):
            raise RuntimeError("exec exploded")

        results = sched.execute_all(executor)
        assert results[1].success is False
        assert "exec exploded" in results[1].error

    def test_execute_all_empty(self) -> None:
        sched = DAGScheduler([])
        results = sched.execute_all(lambda s: s)
        assert results == {}

    def test_execute_all_unresolvable_dependency_breaks(self) -> None:
        # Step with missing dependency cannot be scheduled, hitting break on line 139
        s1 = DummyStep(order=1, dependencies=[999])
        sched = DAGScheduler([s1])
        results = sched.execute_all(lambda s: s)
        assert results == {}


class TestValidateDAG:
    def test_valid_dag(self) -> None:
        steps = [
            DummyStep(order=1, dependencies=[]),
            DummyStep(order=2, dependencies=[1]),
            DummyStep(order=3, dependencies=[1, 2]),
        ]
        assert validate_dag(steps) is None

    def test_circular_dependency(self) -> None:
        steps = [
            DummyStep(order=1, dependencies=[2]),
            DummyStep(order=2, dependencies=[1]),
        ]
        err = validate_dag(steps)
        assert err is not None
        assert "Circular" in err

    def test_empty_steps(self) -> None:
        assert validate_dag([]) is None


# =========================================================================
# cost_tracker.py — 253 lines
# =========================================================================
class TestCostTracker:
    def test_cost_entry_dataclass(self) -> None:
        entry = CostEntry(model="gemini-2.0-flash", provider="google")
        assert entry.total_tokens == 0
        assert entry.cost_usd == 0.0

    def test_spend_summary_dataclass(self) -> None:
        summary = SpendSummary()
        assert summary.total_calls == 0
        assert summary.total_cost_usd == 0.0

    def test_completion_cost_no_usage(self, tmp_path: Path) -> None:
        tracker = CostTracker(persist_path=str(tmp_path / "spend.jsonl"))
        assert tracker.completion_cost("gemini-2.0-flash", usage=None) == 0.0
        assert tracker.completion_cost("gemini-2.0-flash", usage={}) == 0.0

    def test_completion_cost_with_pricing(self, tmp_path: Path) -> None:
        spend_file = tmp_path / "spend.jsonl"
        tracker = CostTracker(persist_path=str(spend_file))

        usage = {"prompt_tokens": 1000, "completion_tokens": 500}
        cost = tracker.completion_cost("gemini-2.0-flash", usage=usage, provider="google")

        # 1000 * 0.1e-6 = 0.0001; 500 * 0.4e-6 = 0.0002; total = 0.0003
        assert cost == pytest.approx(0.0003, rel=1e-4)
        assert spend_file.exists()

        # Check persisted line
        lines = spend_file.read_text().strip().splitlines()
        assert len(lines) == 1
        data = json.loads(lines[0])
        assert data["model"] == "gemini-2.0-flash"
        assert data["provider"] == "google"

    def test_completion_cost_with_slash_prefix(self, tmp_path: Path) -> None:
        tracker = CostTracker(persist_path=str(tmp_path / "spend.jsonl"))
        usage = {"input_tokens": 1000, "output_tokens": 1000}
        cost = tracker.completion_cost("openai/gpt-4o", usage=usage, provider="openai")
        assert cost > 0.0

    def test_get_summary(self, tmp_path: Path) -> None:
        tracker = CostTracker(persist_path=str(tmp_path / "spend.jsonl"))
        tracker.completion_cost(
            "gemini-2.0-flash",
            usage={"prompt_tokens": 1000, "completion_tokens": 500},
            provider="google",
        )
        tracker.completion_cost(
            "gpt-4o-mini",
            usage={"prompt_tokens": 2000, "completion_tokens": 1000},
            provider="openai",
        )

        summary = tracker.get_summary()
        assert summary.total_calls == 2
        assert summary.total_input_tokens == 3000
        assert summary.total_output_tokens == 1500
        assert "gemini-2.0-flash" in summary.by_model
        assert "gpt-4o-mini" in summary.by_model
        assert summary.by_provider["google"] > 0
        assert summary.by_provider["openai"] > 0

    def test_get_model_info(self) -> None:
        tracker = CostTracker()
        info = tracker.get_model_info("gemini-2.5-pro")
        assert info == MODEL_PRICES["gemini-2.5-pro"]

        info_slash = tracker.get_model_info("google/gemini-2.5-pro")
        assert info_slash == MODEL_PRICES["gemini-2.5-pro"]

        info_unknown = tracker.get_model_info("unknown-model-xyz")
        assert info_unknown == {}

    def test_clear(self, tmp_path: Path) -> None:
        tracker = CostTracker(persist_path=str(tmp_path / "spend.jsonl"))
        tracker.completion_cost("gemini-2.0-flash", usage={"prompt_tokens": 100})
        assert len(tracker._entries) == 1
        tracker.clear()
        assert len(tracker._entries) == 0

    def test_get_cost_tracker_singleton(self) -> None:
        t1 = get_cost_tracker()
        t2 = get_cost_tracker()
        assert t1 is t2


# =========================================================================
# command_loader.py — 176 lines
# =========================================================================
class TestCommandLoader:
    def test_parse_frontmatter_valid(self) -> None:
        text = '---\ndescription: "My cmd"\nargument-hint: "<arg>"\n---\nBody text'
        fm, body = _parse_frontmatter(text)
        assert fm["description"] == "My cmd"
        assert fm["argument-hint"] == "<arg>"
        assert body == "Body text"

    def test_parse_frontmatter_no_start(self) -> None:
        fm, body = _parse_frontmatter("No frontmatter")
        assert fm == {}
        assert body == "No frontmatter"

    def test_parse_frontmatter_unclosed(self) -> None:
        fm, body = _parse_frontmatter("---\ndescription: unclosed")
        assert fm == {}
        assert "unclosed" in body

    def test_load_all_commands(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cmd_dir = tmp_path / "commands"
        cmd_dir.mkdir()
        (cmd_dir / "accounting-daily.md").write_text(
            '---\ndescription: "Run accounting"\nargument-hint: "[date]"\nallowed-tools: bash, read\n---\nDo accounting.',
            encoding="utf-8",
        )
        (cmd_dir / "corrupt.md").write_text(
            "not a real yaml frontmatter",
            encoding="utf-8",
        )

        monkeypatch.setattr("src.core.command_loader.COMMANDS_DIR", cmd_dir)
        cmds = load_all_commands()
        assert len(cmds) == 2
        cmd = next(c for c in cmds if c.id == "accounting-daily")
        assert cmd.description == "Run accounting"
        assert cmd.allowed_tools == ["bash", "read"]

    def test_load_all_commands_missing_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.core.command_loader.COMMANDS_DIR", tmp_path / "nonexistent")
        cmds = load_all_commands()
        assert cmds == []

    def test_load_all_commands_file_read_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cmd_dir = tmp_path / "commands"
        cmd_dir.mkdir()
        unreadable = cmd_dir / "bad.md"
        unreadable.write_text("content", encoding="utf-8")

        orig_read = Path.read_text

        def mock_read(self, *args, **kwargs):
            if self.name == "bad.md":
                raise OSError("Simulated read error")
            return orig_read(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", mock_read)
        monkeypatch.setattr("src.core.command_loader.COMMANDS_DIR", cmd_dir)
        cmds = load_all_commands()
        assert cmds == []

    def test_find_best_command_slash_syntax(self, monkeypatch: pytest.MonkeyPatch) -> None:
        dummy_cmd = Command(
            id="accounting-daily",
            path=Path("test.md"),
            description="Daily accounting run",
            argument_hint="",
            allowed_tools=[],
            content="Run daily accounting.",
        )
        monkeypatch.setattr("src.core.command_loader.get_commands", lambda: [dummy_cmd])

        found = find_best_command("/accounting-daily Q3 report")
        assert found is not None
        assert found.id == "accounting-daily"

    def test_find_best_command_keyword_and_role_match(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c1 = Command(
            id="accounting-tax",
            path=Path("tax.md"),
            description="Calculate tax invoices and expense reports",
            argument_hint="",
            allowed_tools=[],
            content="Do tax.",
        )
        c2 = Command(
            id="marketing-campaign",
            path=Path("mkt.md"),
            description="Launch email campaign",
            argument_hint="",
            allowed_tools=[],
            content="Do marketing.",
        )
        monkeypatch.setattr("src.core.command_loader.get_commands", lambda: [c1, c2])

        # CFO role matches accounting prefix (+10) + keyword overlap (+2*N)
        found = find_best_command("review invoices and tax expense", agent_role="cfo", domain="finance")
        assert found is not None
        assert found.id == "accounting-tax"

    def test_find_best_command_domain_match_in_description(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        c1 = Command(
            id="general-task",
            path=Path("gen.md"),
            description="Specialized accounting and tax workflow",
            argument_hint="",
            allowed_tools=[],
            content="Task.",
        )
        monkeypatch.setattr("src.core.command_loader.get_commands", lambda: [c1])

        found = find_best_command("process workflow", domain="accounting")
        assert found is not None
        assert found.id == "general-task"

    def test_find_best_command_no_commands_or_low_score(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("src.core.command_loader.get_commands", lambda: [])
        assert find_best_command("random goal") is None

        # Low score threshold (< 4)
        c = Command(
            id="xyz",
            path=Path("x.md"),
            description="completely unrelated",
            argument_hint="",
            allowed_tools=[],
            content="",
        )
        monkeypatch.setattr("src.core.command_loader.get_commands", lambda: [c])
        assert find_best_command("alpha beta gamma") is None

    def test_build_system_prompt(self) -> None:
        cmd = Command(
            id="test-cmd",
            path=Path("t.md"),
            description="Test",
            argument_hint="",
            allowed_tools=[],
            content="Command Instructions Here",
        )
        prompt = build_system_prompt(cmd, "build new report")
        assert "You are a Mekong AI OS operational agent." in prompt
        assert "Command Instructions Here" in prompt
        assert "build new report" in prompt

    def test_get_commands_caching(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import src.core.command_loader as cl
        cl._COMMANDS = None
        monkeypatch.setattr(cl, "load_all_commands", lambda: ["mocked"])
        assert get_commands() == ["mocked"]
        # Cached second call
        assert get_commands() == ["mocked"]


# =========================================================================
# memory_store_adapter.py — 92 lines
# =========================================================================
class TestMemoryStoreAdapter:
    def test_store_json_decoding(self) -> None:
        mock_store = MagicMock()
        adapter = MemoryStoreAdapter(store=mock_store)

        val = json.dumps({"token": "123", "score": 99}).encode("utf-8")
        adapter.store("key1", val)

        mock_store.record.assert_called_once()
        entry = mock_store.record.call_args[0][0]
        assert entry.goal == "key1"
        assert entry.status == "success"
        assert entry.context == {"token": "123", "score": 99}

    def test_store_raw_bytes_fallback(self) -> None:
        mock_store = MagicMock()
        adapter = MemoryStoreAdapter(store=mock_store)

        val = b"\x80abc non-json"
        adapter.store("raw_key", val)

        mock_store.record.assert_called_once()
        entry = mock_store.record.call_args[0][0]
        assert entry.goal == "raw_key"
        assert "raw" in entry.context

    def test_retrieve_success(self) -> None:
        mock_store = MagicMock()
        mock_entry = MagicMock()
        mock_entry.context = {"user": "alice"}
        mock_store.query.return_value = [mock_entry]

        adapter = MemoryStoreAdapter(store=mock_store)
        res = adapter.retrieve("alice_key")
        assert res is not None
        assert json.loads(res.decode("utf-8")) == {"user": "alice"}

    def test_retrieve_empty_or_no_context(self) -> None:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        adapter = MemoryStoreAdapter(store=mock_store)
        assert adapter.retrieve("missing") is None

        # Entry with empty context
        mock_entry = MagicMock()
        mock_entry.context = None
        mock_store.query.return_value = [mock_entry]
        assert adapter.retrieve("no_ctx") is None

    def test_retrieve_non_json_serializable_context(self) -> None:
        mock_store = MagicMock()
        mock_entry = MagicMock()
        mock_entry.context = object()
        mock_store.query.return_value = [mock_entry]

        adapter = MemoryStoreAdapter(store=mock_store)
        res = adapter.retrieve("obj_key")
        assert res is not None
        assert b"object at" in res

    def test_delete_success(self) -> None:
        mock_store = MagicMock()
        e1 = MagicMock(goal="keep")
        e2 = MagicMock(goal="delete_me")
        mock_store.query.return_value = [e2]
        mock_store._entries = [e1, e2]

        adapter = MemoryStoreAdapter(store=mock_store)
        assert adapter.delete("delete_me") is True
        assert mock_store._entries == [e1]
        mock_store._save.assert_called_once()

    def test_delete_missing(self) -> None:
        mock_store = MagicMock()
        mock_store.query.return_value = []
        adapter = MemoryStoreAdapter(store=mock_store)
        assert adapter.delete("not_found") is False

        # Query returns non-matching entry
        mock_store.query.return_value = [MagicMock(goal="other")]
        assert adapter.delete("target") is False

    def test_search(self) -> None:
        mock_store = MagicMock()
        e = MagicMock(
            goal="find_me",
            context={"meta": 1},
            status="done",
            timestamp=123.45,
            error_summary="none",
        )
        mock_store.semantic_search.return_value = [e]

        adapter = MemoryStoreAdapter(store=mock_store)
        hits = adapter.search("query", limit=5)
        assert len(hits) == 1
        assert hits[0].key == "find_me"
        assert hits[0].score == 1.0
        assert hits[0].metadata["status"] == "done"


# =========================================================================
# config.py — 15 lines
# =========================================================================
class TestConfig:
    def test_config_instance(self) -> None:
        import importlib
        import src.core.config as config_mod
        importlib.reload(config_mod)

        cfg = config_mod.get_config()
        assert isinstance(cfg, config_mod.Config)


# =========================================================================
# usage_metering.py — 37 lines (re-export shim)
# =========================================================================
class TestUsageMeteringReexports:
    def test_symbols_accessible(self) -> None:
        assert UsageEvent is not None
        assert UsageEventType is not None
        assert UsageMetering is not None
        assert get_metering is not None
        assert reset_metering is not None
        assert UsageAnomalyDetector is not None
        assert AnomalyCategory is not None
        assert get_detector is not None
        assert get_tracker is not None
