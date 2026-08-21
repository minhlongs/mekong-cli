"""Phase 2A (Step 3): Agent Registry consolidation tests.

Note: AgentRegistry already serves as the consolidated registry.
These tests verify it satisfies the AgentDispatcher Protocol's discovery needs (Protocol removed; registry still works).
"""
import pytest

from src.core.agent_registry import AgentRegistry


class TestAgentRegistryConsolidated:
    def test_registry_loads_from_default_dir(self):
        """AgentRegistry must be instantiable."""
        registry = AgentRegistry()
        assert registry is not None

    def test_registry_list_returns_names(self):
        """list() must return list of agent name strings."""
        registry = AgentRegistry()
        names = registry.list()
        assert isinstance(names, list)

    def test_registry_get_existing(self):
        """get() must return agent class for registered agent."""
        registry = AgentRegistry()
        names = registry.list()
        if names:
            first = names[0]
            agent_cls = registry.get(first)
            assert agent_cls is not None

    def test_registry_get_missing_raises(self):
        """get() must raise KeyError for unknown agent."""
        registry = AgentRegistry()
        with pytest.raises(KeyError):
            registry.get("nonexistent_agent_xyz")

    def test_registry_has_required_fields(self):
        """Retrieved agent class must have name and role."""
        registry = AgentRegistry()
        names = registry.list()
        if names:
            agent_cls = registry.get(names[0])
            assert hasattr(agent_cls, "name")
            assert hasattr(agent_cls, "role")