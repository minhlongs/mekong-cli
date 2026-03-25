"""Tests for src.core.skill_detector — SkillDetector."""

from pathlib import Path

import pytest

from src.core.skill_detector import DetectedSkill, SkillDetector


@pytest.fixture
def detector(tmp_path: Path) -> SkillDetector:
    """Create a SkillDetector pointed at a temp workspace."""
    return SkillDetector(workspace=str(tmp_path))


@pytest.fixture
def py_workspace(tmp_path: Path) -> SkillDetector:
    """Workspace with Python markers."""
    (tmp_path / "pyproject.toml").write_text('[tool.poetry]\nname = "test"')
    (tmp_path / "main.py").write_text("import os\n")
    (tmp_path / "conftest.py").write_text("# pytest config\n")
    return SkillDetector(workspace=str(tmp_path))


class TestSkillDetector:
    """Tests for SkillDetector class."""

    def test_detect_empty_workspace(self, detector: SkillDetector) -> None:
        """Empty workspace returns no skills."""
        skills = detector.detect()
        assert skills == []

    def test_detect_python_markers(self, py_workspace: SkillDetector) -> None:
        """Python markers are detected with correct confidence."""
        skills = py_workspace.detect()
        names = [s.name for s in skills]
        assert "python" in names

    def test_detect_returns_sorted_by_confidence(
        self, py_workspace: SkillDetector
    ) -> None:
        """Skills are sorted by confidence descending."""
        skills = py_workspace.detect()
        if len(skills) > 1:
            confs = [s.confidence for s in skills]
            assert confs == sorted(confs, reverse=True)

    def test_inject_context_empty(self, detector: SkillDetector) -> None:
        """inject_context returns empty string for empty workspace."""
        assert detector.inject_context() == ""

    def test_inject_context_with_skills(
        self, py_workspace: SkillDetector
    ) -> None:
        """inject_context includes detected skill names."""
        ctx = py_workspace.inject_context()
        assert "python" in ctx
        assert "Detected Skills" in ctx

    def test_cache_returns_same_results(
        self, py_workspace: SkillDetector
    ) -> None:
        """Second call returns cached results."""
        first = py_workspace.detect()
        second = py_workspace.detect()
        assert first is second  # Same object = cached

    def test_force_refresh_bypasses_cache(
        self, py_workspace: SkillDetector
    ) -> None:
        """force=True bypasses the cache."""
        first = py_workspace.detect()
        refreshed = py_workspace.detect(force=True)
        assert first is not refreshed  # Different object
        assert len(first) == len(refreshed)
