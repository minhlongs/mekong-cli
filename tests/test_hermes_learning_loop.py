"""Tests for Hermes-style closed learning-loop contract."""

from __future__ import annotations

import json
from pathlib import Path

from src.harness.learning_loop import HermesLearningLoop, validate_learning_loop


def test_default_learning_loop_validates() -> None:
    loop = HermesLearningLoop.load()
    result = validate_learning_loop(loop)

    assert loop.schema == "mekong.hermes_learning_loop.v1"
    assert result.valid is True
    assert result.capability_count == 5
    assert "mcp-tool-gateway" in loop.capability_ids()


def test_learning_loop_reports_missing_capability(tmp_path: Path) -> None:
    loop = HermesLearningLoop.load()
    data = {
        "schema": loop.schema,
        "version": loop.version,
        "mission": loop.mission,
        "capabilities": loop.capabilities[:-1],
        "loop": loop.loop,
    }
    path = tmp_path / "bad-loop.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    result = validate_learning_loop(HermesLearningLoop.load(path))

    assert result.valid is False
    assert "Missing capabilities" in result.errors[0]
