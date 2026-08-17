"""Phase 2A (Step 3.5): MCP Capability Adapter."""
import pytest
from unittest.mock import MagicMock

from src.core.adapters.mcp_capability_adapter import MCPCapabilityAdapter
from src.core.capability import Capability, CapabilitySource
from src.core.protocols import CapabilityBus as CapabilityBusProtocol


class _FakeBus:
    """Minimal CapabilityBus for testing MCPCapabilityAdapter."""
    def __init__(self):
        self._caps: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._caps[capability.id] = capability

    def unregister(self, capability_id: str) -> bool:
        if capability_id in self._caps:
            del self._caps[capability_id]
            return True
        return False

    def get(self, capability_id: str) -> Capability | None:
        return self._caps.get(capability_id)

    def list_capabilities(self, risk_level=None, source=None):
        caps = list(self._caps.values())
        if risk_level:
            caps = [c for c in caps if c.risk_level == risk_level]
        if source:
            caps = [c for c in caps if c.source == source]
        return caps

    def discover(self, query: str):
        q = query.lower()
        return [c for c in self._caps.values()
                if q in c.name.lower() or q in c.description.lower()
                or any(q in t.lower() for t in c.tags)]

    def execute(self, capability_id: str, params: dict, context=None):
        cap = self._caps.get(capability_id)
        if cap is None:
            return {"error": f"Capability {capability_id} not found"}
        return cap.execute(params, context)

    def check_authorization(self, capability_id: str, principal: str) -> bool:
        cap = self._caps.get(capability_id)
        if cap is None or cap.authorization is None:
            return True
        return principal == cap.authorization


class TestMCPCapabilityAdapter:
    def test_adapter_creation(self):
        """MCPCapabilityAdapter must be instantiable."""
        adapter = MCPCapabilityAdapter()
        assert adapter is not None

    def test_bus_assignment(self):
        """bus property must accept and return CapabilityBus."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus
        assert adapter.bus is bus

    def test_sync_requires_bus(self):
        """sync_from_mcp must raise if bus is not set."""
        adapter = MCPCapabilityAdapter()
        with pytest.raises(RuntimeError, match="CapabilityBus not set"):
            adapter.sync_from_mcp()

    def test_sync_registers_capabilities(self):
        """sync_from_mcp must register discovered MCP tools as Capabilities."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        # Mock MCPServer with some tools
        mock_server = MagicMock()
        mock_server._tools = [
            {"name": "memory_search", "description": "Search memory"},
            {"name": "tasks_list", "description": "List tasks"},
            {"name": "brainstorm", "description": "Brainstorm topic"},
        ]
        adapter._mcp_server = mock_server

        caps = adapter.sync_from_mcp()
        assert len(caps) == 3
        assert all(isinstance(c, Capability) for c in caps)
        assert all(c.source == CapabilitySource.MCP for c in caps)

    def test_sync_sets_mcp_prefix(self):
        """Registered capabilities must have id prefixed with 'mcp:'."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        mock_server = MagicMock()
        mock_server._tools = [
            {"name": "memory_search", "description": "Search memory"},
        ]
        adapter._mcp_server = mock_server

        adapter.sync_from_mcp()
        cap = bus.get("mcp:memory_search")
        assert cap is not None
        assert cap.id == "mcp:memory_search"

    def test_sync_risk_level_medium(self):
        """MCP capabilities default to MEDIUM risk."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        mock_server = MagicMock()
        mock_server._tools = [
            {"name": "shell_run", "description": "Run shell"},
        ]
        adapter._mcp_server = mock_server

        adapter.sync_from_mcp()
        cap = bus.get("mcp:shell_run")
        assert cap.risk_level == "MEDIUM"

    def test_sync_tags_include_mcp(self):
        """MCP capabilities must have 'mcp' tag."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        mock_server = MagicMock()
        mock_server._tools = [
            {"name": "test_tool", "description": "Test"},
        ]
        adapter._mcp_server = mock_server

        adapter.sync_from_mcp()
        cap = bus.get("mcp:test_tool")
        assert "mcp" in cap.tags

    def test_sync_idempotent(self):
        """Calling sync_from_mcp twice must not duplicate."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        mock_server = MagicMock()
        mock_server._tools = [
            {"name": "tool_a", "description": "A"},
        ]
        adapter._mcp_server = mock_server

        adapter.sync_from_mcp()
        adapter.sync_from_mcp()  # second call
        assert len(bus.list_capabilities()) == 1

    def test_sync_handles_missing_server(self):
        """sync_from_mcp returns empty list when MCPServer unavailable."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus
        adapter._mcp_server = None

        caps = adapter.sync_from_mcp()
        assert caps == []

    def test_execute_calls_handler(self):
        """capability.execute() must call the MCP handler."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        mock_server = MagicMock()
        mock_handler = MagicMock(return_value="handler_result")
        mock_server._tools = [
            {"name": "test_tool", "description": "Test"},
        ]
        # Inject handler into the server instance
        mock_server._handle_test_tool = mock_handler
        adapter._mcp_server = mock_server

        adapter.sync_from_mcp()
        cap = bus.get("mcp:test_tool")
        result = cap.execute({"param": "value"})
        assert result["ok"] is True
        assert result["result"] == "handler_result"

    def test_get_capability(self):
        """get_capability returns single capability by tool name."""
        adapter = MCPCapabilityAdapter()
        bus = _FakeBus()
        adapter.bus = bus

        mock_server = MagicMock()
        mock_server._tools = [
            {"name": "search", "description": "Search"},
        ]
        adapter._mcp_server = mock_server

        adapter.sync_from_mcp()
        cap = adapter.get_capability("search")
        assert cap is not None
        assert cap.id == "mcp:search"

    def test_get_capability_without_bus(self):
        """get_capability returns None when bus not set."""
        adapter = MCPCapabilityAdapter()
        assert adapter.get_capability("anything") is None

    def test_fake_bus_satisfies_protocol(self):
        """_FakeBus must satisfy CapabilityBus Protocol."""
        assert isinstance(_FakeBus(), CapabilityBusProtocol)