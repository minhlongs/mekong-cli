"""Vertical chain integration test — swot -> plan -> cook -> test -> deploy -> audit."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.core.binh_phap.topology import (
    TopologyEngine,
    EscalationLevel,
    COMMERCIAL_CHAPTERS,
    CommandResult,
)
from src.core.binh_phap_escalation import resolve_llm_provider


@pytest.fixture
def engine(tmp_path: Path) -> TopologyEngine:
    state_file = tmp_path / "company.json"
    state_file.write_text(json.dumps({"binh_phap_state": {}}))
    return TopologyEngine(company_json_path=str(state_file))


class TestVerticalChain:
    def test_chain_sequence(self, engine: TopologyEngine) -> None:
        chain = engine.get_vertical_chain()
        assert chain == ["swot", "plan", "cook", "test", "deploy", "audit"]

    def test_commercial_chapter_set(self) -> None:
        assert COMMERCIAL_CHAPTERS == frozenset({1, 2, 5, 11, 12})

    def test_known_escalation_levels(self, engine: TopologyEngine) -> None:
        assert engine.get_escalation("standup") == EscalationLevel.AUTONOMOUS
        assert engine.get_escalation("launch") == EscalationLevel.APPROVE
        assert engine.get_escalation("pivot") == EscalationLevel.STRATEGIC

    def test_finance_is_in_commercial_chapters(self, engine: TopologyEngine) -> None:
        chapter = engine._command_to_chapter("finance")
        assert chapter in COMMERCIAL_CHAPTERS

    def test_strategic_uses_fable_model_by_default(self) -> None:
        cfg = resolve_llm_provider("strategic")
        assert cfg["model"] == "claude-opus-4-8"
        assert "base_url" in cfg

    def test_default_uses_opus_model(self) -> None:
        cfg = resolve_llm_provider("cloud_opus")
        assert cfg["model"] == "claude-opus-4-8"

    def test_advance_vertical_moves_pointer(self, engine: TopologyEngine) -> None:
        assert engine.next_vertical_command() == "swot"
        engine.advance_vertical(
            CommandResult(command="swot", chapter=1, success=True, output_key="swot_out")
        )
        assert engine.state["next_command"] == "plan"

    def test_dispatch_first_command(self, engine: TopologyEngine) -> None:
        action = engine.dispatch_next()
        assert action["action"] == "execute"
        assert action["command"] == "swot"
