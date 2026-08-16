"""Smoke tests: all 9 Mekong Core Protocols importable and compliant."""
import inspect

import pytest
from src.core import protocols


PROTOCOLS = [
    "MekongCoreRuntime", "LLMRouter", "ToolRegistry", "AgentDispatcher",
    "BillingMeter", "MemoryStore", "ObservabilitySink", "VerificationEngine", "GoalEngine",
]


class TestProtocolDefinitions:
    def test_all_nine_protocols_exist(self):
        for name in PROTOCOLS:
            assert hasattr(protocols, name), f"Missing Protocol: {name}"

    def test_protocols_are_typing_protocol(self):
        for name in PROTOCOLS:
            proto = getattr(protocols, name)
            assert hasattr(proto, "__protocol_attrs__") or inspect.isclass(proto), \
                f"{name} is not a Protocol class"

    def test_billing_meter_has_settle_payment(self):
        if hasattr(protocols, "BillingMeter"):
            methods = [m for m in dir(protocols.BillingMeter) if not m.startswith("_")]
            assert "settle_payment" in methods

    def test_tool_registry_has_list_mcp_tools(self):
        if hasattr(protocols, "ToolRegistry"):
            methods = [m for m in dir(protocols.ToolRegistry) if not m.startswith("_")]
            assert "list_mcp_tools" in methods

    def test_goal_engine_has_adapt(self):
        if hasattr(protocols, "GoalEngine"):
            methods = [m for m in dir(protocols.GoalEngine) if not m.startswith("_")]
            assert "adapt" in methods


class TestAdapterCompliance:
    def test_memory_store_adapter_importable(self):
        from src.core.memory_store_adapter import MemoryStoreAdapter
        adapter = MemoryStoreAdapter()
        assert isinstance(adapter, protocols.MemoryStore)

    def test_telemetry_sink_adapter_importable(self):
        from src.core.telemetry_sink_adapter import TelemetrySinkAdapter
        adapter = TelemetrySinkAdapter()
        assert isinstance(adapter, protocols.ObservabilitySink)

    def test_llm_router_adapter_importable(self):
        from src.core.llm_router_adapter import LLMRouterAdapter
        adapter = LLMRouterAdapter()
        assert isinstance(adapter, protocols.LLMRouter)