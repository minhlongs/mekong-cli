"""Phase 2A: CapabilityBus Protocol + Capability dataclass."""
import time

import pytest

from src.core.capability import Capability, CapabilityBus, CapabilitySource, InMemoryCapabilityBus


class MockBus:
    """Minimal in-memory CapabilityBus for testing."""
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

    def cleanup(self) -> int:
        expired = [cid for cid, cap in self._caps.items() if cap.is_expired()]
        for cid in expired:
            del self._caps[cid]
        return len(expired)


class TestCapabilityDataclass:
    def test_capability_creation(self):
        cap = Capability(
            id="test:cap",
            name="Test Capability",
            description="A test capability",
            risk_level="LOW",
            source=CapabilitySource.BUILTIN,
        )
        assert cap.id == "test:cap"
        assert cap.risk_level == "LOW"
        assert cap.source == CapabilitySource.BUILTIN

    def test_capability_defaults(self):
        cap = Capability(id="x", name="X", description="Y")
        assert cap.input_schema == {}
        assert cap.output_schema == {}
        assert cap.risk_level == "LOW"
        assert cap.tags == []
        assert cap.cost == 0.0
        assert cap.authorization is None

    def test_capability_with_metadata(self):
        cap = Capability(
            id="mcp:tool",
            name="MCP Tool",
            description="An MCP tool",
            risk_level="MEDIUM",
            source=CapabilitySource.MCP,
            cost=1.5,
            authorization="admin",
            tags=["mcp", "test"],
            metadata={"handler": "_handle_test"},
        )
        assert cap.source == CapabilitySource.MCP
        assert cap.cost == 1.5
        assert cap.authorization == "admin"
        assert "mcp" in cap.tags

    def test_capability_execute_raises_by_default(self):
        cap = Capability(id="x", name="X", description="Y")
        with pytest.raises(NotImplementedError):
            cap.execute({})


class TestCapabilityBusProtocol:
    def test_mock_bus_satisfies_protocol(self):
        assert isinstance(MockBus(), CapabilityBus)

    def test_register_and_get(self):
        bus = MockBus()
        cap = Capability(id="t1", name="T1", description="T")
        bus.register(cap)
        assert bus.get("t1") is cap
        assert bus.get("nonexistent") is None

    def test_unregister(self):
        bus = MockBus()
        cap = Capability(id="t1", name="T1", description="T")
        bus.register(cap)
        assert bus.unregister("t1") is True
        assert bus.get("t1") is None
        assert bus.unregister("nonexistent") is False

    def test_list_capabilities(self):
        bus = MockBus()
        bus.register(Capability(id="a", name="A", description="A", risk_level="LOW"))
        bus.register(Capability(id="b", name="B", description="B", risk_level="HIGH"))
        bus.register(Capability(id="c", name="C", description="C", risk_level="HIGH"))
        assert len(bus.list_capabilities()) == 3
        assert len(bus.list_capabilities(risk_level="HIGH")) == 2
        assert len(bus.list_capabilities(risk_level="LOW")) == 1

    def test_list_by_source(self):
        bus = MockBus()
        bus.register(Capability(id="a", name="A", description="A", source=CapabilitySource.MCP))
        bus.register(Capability(id="b", name="B", description="B", source=CapabilitySource.BUILTIN))
        assert len(bus.list_capabilities(source=CapabilitySource.MCP)) == 1
        assert len(bus.list_capabilities(source=CapabilitySource.BUILTIN)) == 1

    def test_discover_by_name(self):
        bus = MockBus()
        bus.register(Capability(id="g1", name="Git Status", description="Check git status"))
        bus.register(Capability(id="g2", name="Git Commit", description="Commit changes"))
        bus.register(Capability(id="s1", name="Shell Run", description="Run shell command"))
        results = bus.discover("git")
        assert len(results) == 2
        assert all("git" in c.name.lower() or "git" in c.description.lower() for c in results)

    def test_discover_by_tag(self):
        bus = MockBus()
        bus.register(Capability(id="a", name="A", description="A", tags=["shell"]))
        bus.register(Capability(id="b", name="B", description="B", tags=["mcp"]))
        bus.register(Capability(id="c", name="C", description="C", tags=["shell", "safe"]))
        results = bus.discover("shell")
        assert len(results) == 2

    def test_execute_with_handler(self):
        bus = MockBus()
        cap = Capability(id="t1", name="T1", description="T")
        cap.execute = lambda params, ctx=None: {"ok": True, "echo": params.get("msg", "")}
        bus.register(cap)
        result = bus.execute("t1", {"msg": "hello"})
        assert result["ok"] is True
        assert result["echo"] == "hello"

    def test_execute_missing_returns_error(self):
        bus = MockBus()
        result = bus.execute("nonexistent", {})
        assert "error" in result

    def test_check_authorization_no_requirement(self):
        bus = MockBus()
        cap = Capability(id="t1", name="T1", description="T")
        bus.register(cap)
        assert bus.check_authorization("t1", "anyone") is True

    def test_check_authorization_match(self):
        bus = MockBus()
        cap = Capability(id="t1", name="T1", description="T", authorization="admin")
        bus.register(cap)
        assert bus.check_authorization("t1", "admin") is True
        assert bus.check_authorization("t1", "user") is False


class TestCapabilitySource:
    def test_source_values(self):
        assert CapabilitySource.BUILTIN == "builtin"
        assert CapabilitySource.CLI == "cli"
        assert CapabilitySource.API == "api"
        assert CapabilitySource.MCP == "mcp"
        assert CapabilitySource.CUSTOM == "custom"


class TestCapabilityOwnership:
    """AUTONOMY_GAPS #9 — Capability ownership + expiry state."""

    def test_defaults_registered_at_to_now(self):
        before = time.time()
        cap = Capability(id="x", name="X", description="Y")
        after = time.time()
        assert cap.registered_by is None
        assert before <= cap.registered_at <= after
        assert cap.expires_at is None

    def test_explicit_ownership_preserved(self):
        cap = Capability(
            id="x", name="X", description="Y",
            registered_by="admin",
            registered_at=100.0,
            expires_at=200.0,
        )
        assert cap.registered_by == "admin"
        assert cap.registered_at == 100.0
        assert cap.expires_at == 200.0

    def test_is_expired_false_without_expiration(self):
        cap = Capability(id="x", name="X", description="Y")
        assert cap.is_expired() is False

    def test_is_expired_true_in_past(self):
        cap = Capability(id="x", name="X", description="Y", expires_at=100.0)
        assert cap.is_expired(now=200.0) is True

    def test_is_expired_false_in_future(self):
        cap = Capability(id="x", name="X", description="Y", expires_at=100.0)
        assert cap.is_expired(now=50.0) is False


class TestInMemoryCapabilityBus:
    """InMemoryCapabilityBus is the canonical CapabilityBus implementation."""

    def test_satisfies_protocol(self):
        from src.core.capability import InMemoryCapabilityBus
        assert isinstance(InMemoryCapabilityBus(), CapabilityBus)

    def test_register_stamps_default_owner(self):
        from src.core.capability import InMemoryCapabilityBus
        bus = InMemoryCapabilityBus()
        cap = Capability(id="t1", name="T1", description="T")
        bus.register(cap)
        assert cap.registered_by == "default"
        assert cap.registered_at is not None

    def test_register_preserves_explicit_owner(self):
        from src.core.capability import InMemoryCapabilityBus
        bus = InMemoryCapabilityBus()
        cap = Capability(id="t1", name="T1", description="T", registered_by="alice")
        bus.register(cap)
        assert cap.registered_by == "alice"

    def test_cleanup_removes_expired(self):
        from src.core.capability import InMemoryCapabilityBus
        bus = InMemoryCapabilityBus()
        future = time.time() + 1000.0
        past = time.time() - 1000.0
        bus.register(Capability(id="a", name="A", description="A", expires_at=past))
        bus.register(Capability(id="b", name="B", description="B", expires_at=future))
        bus.register(Capability(id="c", name="C", description="C"))
        removed = bus.cleanup()
        assert removed == 1
        assert bus.get("a") is None
        assert bus.get("b") is not None
        assert bus.get("c") is not None

    def test_cleanup_returns_zero_when_nothing_expired(self):
        from src.core.capability import InMemoryCapabilityBus
        bus = InMemoryCapabilityBus()
        bus.register(Capability(id="a", name="A", description="A"))
        assert bus.cleanup() == 0

    def test_execute_blocks_expired(self):
        bus = InMemoryCapabilityBus()
        cap = Capability(id="t1", name="T1", description="T", expires_at=100.0)
        cap.execute = lambda params, ctx=None: {"ok": True}
        bus.register(cap)
        result = bus.execute("t1", {})
        assert "expired" in result["error"]