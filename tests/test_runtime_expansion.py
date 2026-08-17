"""Phase 2B: Runtime Adapter Expansion — health, destroy, capability_bus."""
from unittest.mock import MagicMock

from src.core.runtime_adapter import MekongCoreRuntimeImpl


class _FakeDispatcher:
    def dispatch(self, task):
        return None


class _FakeToolRegistry:
    def register(self, tool, **kwargs):
        pass
    def execute(self, tool_id, params):
        return {"ok": True}
    def list_tools(self):
        return []


class TestRuntimeExpansion:
    def test_health_returns_status_dict(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        health = runtime.health()
        assert isinstance(health, dict)
        assert "status" in health
        assert health["status"] == "ok"

    def test_health_includes_agent_id(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            agent_id="test-agent",
        )
        health = runtime.health()
        assert health["agent_id"] == "test-agent"

    def test_health_not_destroyed_initially(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        assert runtime.health()["destroyed"] is False

    def test_destroy_sets_destroyed_flag(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        result = runtime.destroy()
        assert result["status"] == "destroyed"
        assert runtime.health()["destroyed"] is True

    def test_destroy_returns_agent_id(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            agent_id="my-agent",
        )
        result = runtime.destroy()
        assert result["agent_id"] == "my-agent"

    def test_destroy_after_destroy_is_idempotent(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        runtime.destroy()
        result = runtime.destroy()
        assert result["status"] == "destroyed"

    def test_health_includes_llm_router_status(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        health = runtime.health()
        assert "llm_router" in health
        assert health["llm_router"]["status"] == "ok"

    def test_health_includes_has_billing(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        health = runtime.health()
        assert "has_billing" in health

    def test_health_with_capability_bus(self):
        fake_bus = MagicMock()
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
            capability_bus=fake_bus,
        )
        health = runtime.health()
        assert health["has_capability_bus"] is True

    def test_health_without_capability_bus(self):
        runtime = MekongCoreRuntimeImpl(
            dispatcher=_FakeDispatcher(),
            tool_registry=_FakeToolRegistry(),
        )
        health = runtime.health()
        assert health["has_capability_bus"] is False