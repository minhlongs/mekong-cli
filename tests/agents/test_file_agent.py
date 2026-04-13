"""Tests for FileAgent — covers find, read, write, tree, stats, grep, custom, errors."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.file_agent import FileAgent
from src.core.agent_base import Task


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_task(task_id: str, **input_kwargs) -> Task:
    return Task(id=task_id, description="test", input=dict(**input_kwargs))


def make_completed_process(stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    cp = MagicMock(spec=subprocess.CompletedProcess)
    cp.stdout = stdout
    cp.returncode = returncode
    return cp


# ---------------------------------------------------------------------------
# plan()
# ---------------------------------------------------------------------------

class TestPlan:
    def setup_method(self):
        self.agent = FileAgent()

    def test_plan_find(self):
        tasks = self.agent.plan("find *.py")
        assert len(tasks) == 1
        assert tasks[0].id == "file_find"
        assert tasks[0].input["pattern"] == "*.py"

    def test_plan_read(self):
        tasks = self.agent.plan("read src/main.py")
        assert tasks[0].id == "file_read"
        assert tasks[0].input["path"] == "src/main.py"

    def test_plan_write(self):
        tasks = self.agent.plan("write output.txt hello world")
        assert tasks[0].id == "file_write"
        assert tasks[0].input["path"] == "output.txt"
        assert tasks[0].input["content"] == "hello world"

    def test_plan_write_no_content(self):
        tasks = self.agent.plan("write output.txt")
        assert tasks[0].id == "file_write"
        assert tasks[0].input["content"] == ""

    def test_plan_tree_default_depth(self):
        tasks = self.agent.plan("tree")
        assert tasks[0].id == "file_tree"
        assert tasks[0].input["depth"] == 3

    def test_plan_tree_custom_depth(self):
        tasks = self.agent.plan("tree 5")
        assert tasks[0].input["depth"] == 5

    def test_plan_stats(self):
        tasks = self.agent.plan("stats")
        assert tasks[0].id == "file_stats"

    def test_plan_grep(self):
        tasks = self.agent.plan("grep def main")
        assert tasks[0].id == "file_grep"
        assert tasks[0].input["pattern"] == "def main"

    def test_plan_unknown_command_falls_back_to_custom(self):
        tasks = self.agent.plan("frobnicate stuff")
        assert tasks[0].id == "file_custom"
        assert tasks[0].input["raw"] == "frobnicate stuff"

    def test_plan_find_no_pattern_uses_remainder(self):
        tasks = self.agent.plan("find")
        assert tasks[0].id == "file_find"
        assert tasks[0].input["pattern"] == ""


# ---------------------------------------------------------------------------
# execute() — file_find
# ---------------------------------------------------------------------------

class TestExecuteFind:
    def test_find_returns_files(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        (tmp_path / "b.py").write_text("y")
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_find", pattern="*.py")
        result = agent.execute(task)
        assert result.success is True
        assert result.output["count"] >= 2

    def test_find_subprocess_timeout(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_find", pattern="*.py")
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="find", timeout=15)):
            result = agent.execute(task)
        assert result.success is False
        assert "timed out" in result.error

    def test_find_subprocess_error_still_returns(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_find", pattern="*.py")
        with patch("subprocess.run", return_value=make_completed_process(stdout="")):
            result = agent.execute(task)
        assert result.success is True
        assert result.output["count"] == 0


# ---------------------------------------------------------------------------
# execute() — file_read
# ---------------------------------------------------------------------------

class TestExecuteRead:
    def test_read_existing_file(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("line1\nline2\n")
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_read", path="hello.txt")
        result = agent.execute(task)
        assert result.success is True
        assert result.output["content"] == "line1\nline2\n"
        assert result.output["lines"] == 3
        assert result.output["size"] == 12

    def test_read_missing_file(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_read", path="ghost.txt")
        result = agent.execute(task)
        assert result.success is False
        assert "not found" in result.error

    def test_read_path_traversal_denied(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_read", path="../../etc/passwd")
        result = agent.execute(task)
        assert result.success is False
        assert "Path traversal denied" in result.error

    def test_read_large_file_truncated(self, tmp_path):
        f = tmp_path / "big.txt"
        f.write_text("x" * 10000)
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_read", path="big.txt")
        result = agent.execute(task)
        assert result.success is True
        assert len(result.output["content"]) == 5000  # truncated


# ---------------------------------------------------------------------------
# execute() — file_write
# ---------------------------------------------------------------------------

class TestExecuteWrite:
    def test_write_creates_file(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_write", path="out.txt", content="hello")
        result = agent.execute(task)
        assert result.success is True
        assert (tmp_path / "out.txt").read_text() == "hello"
        assert result.output["size"] == 5

    def test_write_creates_parent_dirs(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_write", path="a/b/c.txt", content="data")
        result = agent.execute(task)
        assert result.success is True
        assert (tmp_path / "a" / "b" / "c.txt").exists()

    def test_write_path_traversal_denied(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_write", path="../../evil.txt", content="bad")
        result = agent.execute(task)
        assert result.success is False
        assert "Path traversal denied" in result.error

    def test_write_empty_content(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_write", path="empty.txt", content="")
        result = agent.execute(task)
        assert result.success is True
        assert result.output["size"] == 0


# ---------------------------------------------------------------------------
# execute() — file_tree
# ---------------------------------------------------------------------------

class TestExecuteTree:
    def test_tree_returns_entries(self, tmp_path):
        (tmp_path / "a.py").write_text("x")
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_tree", depth=2)
        result = agent.execute(task)
        assert result.success is True
        assert result.output["count"] > 0

    def test_tree_timeout(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_tree", depth=3)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="find", timeout=15)):
            result = agent.execute(task)
        assert result.success is False
        assert "timed out" in result.error


# ---------------------------------------------------------------------------
# execute() — file_stats
# ---------------------------------------------------------------------------

class TestExecuteStats:
    def test_stats_returns_dict(self, tmp_path):
        (tmp_path / "main.py").write_text("print('hi')\n")
        (tmp_path / "readme.md").write_text("# Title\n")
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_stats")
        result = agent.execute(task)
        assert result.success is True
        assert isinstance(result.output, dict)
        assert ".py" in result.output
        assert result.output[".py"]["files"] == 1
        assert ".md" in result.output

    def test_stats_empty_dir(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_stats")
        result = agent.execute(task)
        assert result.success is True
        assert result.output == {}


# ---------------------------------------------------------------------------
# execute() — file_grep
# ---------------------------------------------------------------------------

class TestExecuteGrep:
    def test_grep_finds_matches(self, tmp_path):
        f = tmp_path / "code.py"
        f.write_text("def hello():\n    pass\n")
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_grep", pattern="def hello")
        result = agent.execute(task)
        assert result.success is True
        assert result.output["count"] >= 1

    def test_grep_no_matches(self, tmp_path):
        (tmp_path / "code.py").write_text("nothing here\n")
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_grep", pattern="xyz_totally_absent_9999")
        result = agent.execute(task)
        assert result.success is True
        assert result.output["count"] == 0

    def test_grep_timeout(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_grep", pattern="foo")
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="grep", timeout=15)):
            result = agent.execute(task)
        assert result.success is False
        assert "timed out" in result.error


# ---------------------------------------------------------------------------
# execute() — file_custom (unknown task)
# ---------------------------------------------------------------------------

class TestExecuteCustomUnknown:
    def test_unknown_task_returns_error(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_custom", raw="something")
        result = agent.execute(task)
        assert result.success is False
        assert "Unknown task" in result.error

    def test_generic_exception_caught(self, tmp_path):
        agent = FileAgent(cwd=str(tmp_path))
        task = make_task("file_find", pattern="*.py")
        with patch("subprocess.run", side_effect=OSError("disk error")):
            result = agent.execute(task)
        assert result.success is False
        assert "disk error" in result.error
