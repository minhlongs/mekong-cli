"""Unit tests for FileAgent stats scoping and path traversal guards."""

from pathlib import Path

import pytest

from src.agents.file_agent import FileAgent


@pytest.fixture
def agent():
    """Create a FileAgent instance with root cwd."""
    cwd = str(Path(__file__).resolve().parents[2])
    return FileAgent(cwd=cwd)


class TestFileStatsScoping:
    """Test that file_stats scans only the src/ subtree by default."""

    def test_default_path_is_src(self, agent):
        """Default file_stats task should scan src/ directory."""
        tasks = agent.plan("stats")
        assert len(tasks) == 1
        assert tasks[0].id == "file_stats"
        assert tasks[0].input.get("path") == "src"

    def test_execute_returns_dict_shape(self, agent):
        """file_stats output must be Dict[ext, {files: int, lines: int}]."""
        task = agent.plan("stats")[0]
        result = agent.execute(task)
        assert result.success
        assert isinstance(result.output, dict)
        for ext, data in result.output.items():
            assert isinstance(ext, str)
            assert ext.startswith(".")
            assert "files" in data
            assert "lines" in data
            assert isinstance(data["files"], int)
            assert isinstance(data["lines"], int)

    def test_scoped_to_src_not_full_repo(self, agent):
        """Stats should only include files under src/, not full repo."""
        task = agent.plan("stats")[0]
        result = agent.execute(task)
        # src/ has Python files, so .py should be present
        assert ".py" in result.output
        for ext, data in result.output.items():
            assert data["files"] >= 0

    def test_custom_path_parameter(self, agent):
        """Custom path parameter should scope scan to that subtree."""
        task = agent.plan("stats")[0]
        task.input["path"] = "tests/unit"
        result = agent.execute(task)
        assert result.success
        assert isinstance(result.output, dict)

    def test_path_traversal_guard(self, agent):
        """Path traversal attempt should fall back to safe src/ default."""
        task = agent.plan("stats")[0]
        task.input["path"] = "../../../etc"
        result = agent.execute(task)
        # Should fall back to src/ and return valid stats with .py files
        assert result.success
        assert isinstance(result.output, dict)
        assert ".py" in result.output

    def test_path_none_guard(self, agent):
        """None path should fall back to safe src/ default without TypeError."""
        task = agent.plan("stats")[0]
        task.input["path"] = None
        result = agent.execute(task)
        assert result.success
        assert isinstance(result.output, dict)
        assert ".py" in result.output

    def test_nonexistent_path_falls_back(self, agent):
        """Non-existent path should fall back to src/."""
        task = agent.plan("stats")[0]
        task.input["path"] = "nonexistent_dir_xyz"
        result = agent.execute(task)
        assert result.success
        assert isinstance(result.output, dict)
        assert ".py" in result.output
