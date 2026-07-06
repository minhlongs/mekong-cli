"""Tests for harness.agents.factory.AgentFactory (B6)."""

from __future__ import annotations

import pytest


class TestAgentFactory:
    """AgentFactory smoke tests — bypass LLM/memory deps."""

    @pytest.fixture()
    def factory(self):
        from harness.agents.factory import AgentFactory

        return AgentFactory()

    def test_list_available_returns_all_five(self, factory):
        agents = factory.list_available()
        for expected in ("ceo", "ae", "pm", "eng", "ops"):
            assert expected in agents, f"Missing agent: {expected}"

    def test_get_definition_returns_dict(self, factory):
        for agent_id in ("ceo", "eng", "ops"):
            defn = factory.get_definition(agent_id)
            assert isinstance(defn, dict)
            assert defn["id"] == agent_id
            assert "name" in defn
            assert "role" in defn

    def test_create_ceo_returns_metadata_stub(self, factory):
        agent = factory.create("ceo")
        from harness.agents.factory import AgentMetadata

        assert isinstance(agent, AgentMetadata)
        assert agent.id == "ceo"
        assert agent.role == "Chief Executive Officer"

    def test_create_eng_returns_agent_instance(self, factory):
        agent = factory.create("eng")
        # May be concrete FileAgent or AgentMetadata stub
        assert agent is not None
        assert hasattr(agent, "plan")

    def test_unknown_agent_raises(self, factory):
        with pytest.raises(ValueError, match="Unknown agent"):
            factory.create("nonexistent")

    def test_create_demo_returns_metadata(self, factory):
        demo = factory.create_demo("test_demo")
        from harness.agents.factory import AgentMetadata

        assert isinstance(demo, AgentMetadata)
        assert demo.id == "test_demo"

    def test_agent_metadata_plan_returns_list(self, factory):
        agent = factory.create("pm")
        plan = agent.plan("dummy input")
        assert isinstance(plan, list)

    def test_agent_metadata_execute_returns_result(self, factory):
        from harness.agents.factory import AgentMetadata

        agent = AgentMetadata("test", {"id": "test", "name": "Test", "role": "test"})
        from harness.agents.factory import Result

        result = agent.execute(type("Task", (), {"id": "t1"})())
        assert isinstance(result, Result)

    def test_agent_metadata_verify_success_true(self, factory):
        from harness.agents.factory import AgentMetadata, Result

        agent = AgentMetadata("test", {"id": "test"})
        assert agent.verify(Result(task_id="x", success=True)) is True

    def test_agent_metadata_verify_failure_false(self, factory):
        from harness.agents.factory import AgentMetadata, Result

        agent = AgentMetadata("test", {"id": "test"})
        assert agent.verify(Result(task_id="x", success=False)) is False

    def test_factory_caches_instances(self, factory):
        a1 = factory.create("ops")
        a2 = factory.create("ops")
        assert a1 is a2
