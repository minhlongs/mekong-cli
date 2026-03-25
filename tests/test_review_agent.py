"""Tests for src.agents.review_agent — ReviewAgent."""

import pytest

from src.agents.review_agent import Perspective, ReviewAgent


@pytest.fixture
def agent() -> ReviewAgent:
    """Create a ReviewAgent without LLM."""
    return ReviewAgent(llm_client=None)


class TestReviewAgent:
    """Tests for ReviewAgent class."""

    def test_perspectives_count(self, agent: ReviewAgent) -> None:
        """ReviewAgent has exactly 6 perspectives."""
        assert len(agent.perspectives) == 6

    def test_plan_returns_6_tasks(self, agent: ReviewAgent) -> None:
        """plan() creates one task per perspective."""
        tasks = agent.plan("src/main.py")
        assert len(tasks) == 6
        task_ids = {t.id for t in tasks}
        assert "review_security" in task_ids
        assert "review_correctness" in task_ids

    def test_execute_without_llm(self, agent: ReviewAgent) -> None:
        """execute() works without LLM client (static fallback)."""
        tasks = agent.plan("src/main.py")
        for task in tasks:
            result = agent.execute(task)
            assert result.success
            assert result.output is not None

        summary = agent.get_summary()
        assert summary.info_count == 6
