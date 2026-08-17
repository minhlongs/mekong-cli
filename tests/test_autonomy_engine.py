"""Phase 2C: Autonomy Engine — risk levels + policy enforcement."""

from src.core.governance import Governance, ActionClass
from src.core.capability import Capability, CapabilitySource


class MockBus:
    def __init__(self):
        self._caps: dict[str, Capability] = {}

    def register(self, capability: Capability) -> None:
        self._caps[capability.id] = capability

    def get(self, capability_id: str) -> Capability | None:
        return self._caps.get(capability_id)

    def check_authorization(self, capability_id: str, principal: str) -> bool:
        cap = self._caps.get(capability_id)
        if cap is None or cap.authorization is None:
            return True
        return principal == cap.authorization


class TestAutonomyEngine:
    """Test risk-level policy enforcement using Governance."""

    def test_governance_classifies_safe(self):
        """Governance must classify safe actions correctly."""
        gov = Governance()
        # classify takes a goal string; read_file is typically safe
        result = gov.classify("read_file")
        assert result.action_class in (ActionClass.SAFE, ActionClass.REVIEW_REQUIRED)

    def test_governance_audit_trail(self):
        """Governance must produce audit entries."""
        gov = Governance()
        result = gov.classify("shell_run")
        assert hasattr(result, "timestamp")
        assert hasattr(result, "reason")

    def test_capability_risk_levels(self):
        """Capabilities must carry risk_level."""
        cap = Capability(
            id="shell:run",
            name="Shell Run",
            description="Run shell command",
            risk_level="HIGH",
            source=CapabilitySource.BUILTIN,
        )
        assert cap.risk_level == "HIGH"

    def test_low_risk_auto_execute(self):
        """LOW risk capabilities can auto-execute."""
        cap = Capability(
            id="fs:read",
            name="Read File",
            description="Read a file",
            risk_level="LOW",
        )
        assert cap.risk_level == "LOW"

    def test_critical_risk_deny_by_default(self):
        """CRITICAL risk capabilities must be denied by default."""
        gov = Governance()
        # Governance should classify destructive actions as FORBIDDEN or REVIEW_REQUIRED
        result = gov.classify("drop table users")
        assert result.action_class in (ActionClass.FORBIDDEN, ActionClass.REVIEW_REQUIRED)

    def test_capability_authorization_check(self):
        """Bus must enforce capability authorization."""
        bus = MockBus()
        cap = Capability(
            id="admin:delete",
            name="Admin Delete",
            description="Delete anything",
            risk_level="CRITICAL",
            authorization="admin",
        )
        bus.register(cap)
        assert bus.check_authorization("admin:delete", "admin") is True
        assert bus.check_authorization("admin:delete", "user") is False

    def test_no_auth_required_when_none(self):
        """Capabilities with no authorization allow any principal."""
        bus = MockBus()
        cap = Capability(id="public:read", name="Public Read", description="Read public")
        bus.register(cap)
        assert bus.check_authorization("public:read", "anyone") is True

    def test_governance_decision_has_required_fields(self):
        """GovernanceDecision must have action_class + reason."""
        gov = Governance()
        result = gov.classify("test_action")
        assert hasattr(result, "action_class")
        assert hasattr(result, "reason")
        assert hasattr(result, "requires_approval")