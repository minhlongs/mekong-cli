"""Tests for CLI memory sub-commands (mekong memory list|search|clear)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from typer.testing import CliRunner

from src.cli.commands.memory import memory_app

runner = CliRunner()


def _seed(path: Path, entries: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")


class TestMemoryList(unittest.TestCase):
    def test_shows_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "memory.jsonl"
            _seed(
                path,
                [
                    {"timestamp": "2026-01-01T00:00:00+00:00", "agent": "cto", "action": "deploy", "outcome": "success", "tags": ["deploy"]},
                    {"timestamp": "2026-01-02T00:00:00+00:00", "agent": "cmo", "action": "email", "outcome": "failed", "tags": ["email"]},
                ],
            )
            with patch.dict(os.environ, {"MEKONG_MEMORY_PATH": str(path)}):
                result = runner.invoke(memory_app, ["list", "--limit", "10"])
            assert result.exit_code == 0, result.output
            assert "deploy" in result.output
            assert "email" in result.output

    def test_empty_store(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "memory.jsonl"
            with patch.dict(os.environ, {"MEKONG_MEMORY_PATH": str(path)}):
                result = runner.invoke(memory_app, ["list"])
            assert result.exit_code == 0
            assert "No memory entries" in result.output


class TestMemorySearch(unittest.TestCase):
    def test_returns_matches(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "memory.jsonl"
            _seed(
                path,
                [
                    {"timestamp": "2026-01-01T00:00:00+00:00", "agent": "cfo", "action": "billing bug", "outcome": "failed", "tags": ["billing"]},
                ],
            )
            with patch.dict(os.environ, {"MEKONG_MEMORY_PATH": str(path)}):
                result = runner.invoke(memory_app, ["search", "billing bug"])
            assert result.exit_code == 0, result.output
            assert "cfo" in result.output
            assert "billing bug" in result.output

    def test_no_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "memory.jsonl"
            _seed(path, [{"timestamp": "2026-01-01T00:00:00+00:00", "agent": "a", "action": "x", "outcome": "ok"}])
            with patch.dict(os.environ, {"MEKONG_MEMORY_PATH": str(path)}):
                result = runner.invoke(memory_app, ["search", "zzz"])
            assert result.exit_code == 0
            assert "No results" in result.output


class TestMemoryClear(unittest.TestCase):
    def test_force_clears(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "memory.jsonl"
            _seed(path, [{"timestamp": "2026-01-01T00:00:00+00:00", "agent": "a", "action": "x", "outcome": "ok"}])
            with patch.dict(os.environ, {"MEKONG_MEMORY_PATH": str(path)}):
                result = runner.invoke(memory_app, ["clear", "--force"])
            assert result.exit_code == 0, result.output
            assert "cleared" in result.output.lower()
            assert path.read_text(encoding="utf-8") == ""


if __name__ == "__main__":
    unittest.main()
