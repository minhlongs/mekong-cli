"""Tests for src.agents.docs_agent — DocsAgent."""

from pathlib import Path

import pytest

from src.agents.docs_agent import DocsAgent


@pytest.fixture
def agent(tmp_path: Path) -> DocsAgent:
    """Create a DocsAgent with a temp workspace."""
    src = tmp_path / "src" / "core"
    src.mkdir(parents=True)
    (src / "__init__.py").write_text('"""Core module."""\n')
    (src / "main.py").write_text("print('hello')\n")
    api = tmp_path / "src" / "api"
    api.mkdir(parents=True)
    (api / "routes.py").write_text("# routes\n")
    return DocsAgent(workspace=str(tmp_path), output_dir="docs")


class TestDocsAgent:
    """Tests for DocsAgent class."""

    def test_plan_init_returns_4_tasks(self, agent: DocsAgent) -> None:
        """plan('init') generates 4 doc specs."""
        tasks = agent.plan("init")
        assert len(tasks) == 4
        names = [t.input["name"] for t in tasks]
        assert "codebase-summary" in names
        assert "api-reference" in names

    def test_execute_creates_files(self, agent: DocsAgent) -> None:
        """execute() creates markdown files in docs/."""
        tasks = agent.plan("init")
        for task in tasks:
            result = agent.execute(task)
            assert result.success
            assert Path(str(result.output)).is_file()

    def test_verify_checks_file_exists(self, agent: DocsAgent) -> None:
        """verify() returns True when output file exists."""
        tasks = agent.plan("init")
        task = tasks[0]
        result = agent.execute(task)
        assert agent.verify(result) is True
