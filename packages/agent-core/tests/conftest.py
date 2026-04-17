"""Shared pytest fixtures for agent-core."""

from __future__ import annotations

from pathlib import Path

import pytest

from agent_core.memory import SeedMemory


@pytest.fixture
def tmp_memory(tmp_path: Path) -> SeedMemory:
    return SeedMemory(root=tmp_path / "agent-core")


@pytest.fixture
def tmp_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    monkeypatch.setenv("AGENT_CORE_OUTPUTS", str(outputs))
    import importlib

    import agent_core.tools.file_system as fs

    importlib.reload(fs)
    return outputs
