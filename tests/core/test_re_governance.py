"""Tests for 3-tier RE Governance and capability bus execution gating."""

import os
import unittest
from typing import Any, Dict
from unittest.mock import patch

from src.core.capability import Capability, CapabilitySource, InMemoryCapabilityBus
from src.core.governance import ActionClass, Governance, ReRiskTier


class DummyReCapability(Capability):
    """Test capability that records the context passed to execute()."""

    def execute(self, params: Dict[str, Any], context: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "status": "ok",
            "params": params,
            "context": context or {},
        }


class TestReGovernance(unittest.TestCase):
    """Verify 3-tier RE governance behavior."""

    def setUp(self) -> None:
        self.gov = Governance(audit_path="/tmp/_mekong_test_re_audit.yaml")
        self.bus = InMemoryCapabilityBus(governance=self.gov)

    def test_low_risk_execution(self) -> None:
        cap = DummyReCapability(
            id="re:codebase_audit",
            name="Static Audit",
            description="Static audit",
            risk_level="LOW_RISK",
            source=CapabilitySource.BUILTIN,
        )
        self.bus.register(cap)
        res = self.bus.execute("re:codebase_audit", {"target": "src/"})
        self.assertEqual(res.get("status"), "ok")
        ctx = res.get("context", {})
        self.assertEqual(ctx.get("re_policy", {}).get("tier"), ReRiskTier.LOW_RISK.value)
        self.assertFalse(ctx.get("re_policy", {}).get("isolated_workspace"))

    def test_medium_risk_workspace_isolation(self) -> None:
        cap = DummyReCapability(
            id="re:ghidra_decompile",
            name="Ghidra Decompile",
            description="Medium risk decompile",
            risk_level="MEDIUM_RISK",
            source=CapabilitySource.MCP,
        )
        self.bus.register(cap)
        res = self.bus.execute("re:ghidra_decompile", {"binary": "sample.bin"})
        self.assertEqual(res.get("status"), "ok")
        ctx = res.get("context", {})
        self.assertEqual(ctx.get("re_policy", {}).get("tier"), ReRiskTier.MEDIUM_RISK.value)
        self.assertTrue(ctx.get("re_policy", {}).get("isolated_workspace"))
        self.assertIn("isolated_workspace", ctx)
        self.assertEqual(ctx.get("python_flags"), ["-I"])

    def test_high_risk_requires_approval_rejected(self) -> None:
        with patch.dict(os.environ, {"GOVERNANCE_AUTO_APPROVE": ""}):
            cap = DummyReCapability(
                id="re:frida_trace",
                name="Frida Trace",
                description="Live instrumentation",
                risk_level="HIGH_RISK",
                source=CapabilitySource.CLI,
            )
            self.bus.register(cap)
            res = self.bus.execute("re:frida_trace", {"pid": 1234})
            self.assertIn("error", res)
            self.assertTrue(res.get("requires_approval"))
            self.assertEqual(res.get("governance"), ActionClass.REVIEW_REQUIRED.value)

    def test_high_risk_auto_approve_or_explicit_approved(self) -> None:
        cap = DummyReCapability(
            id="re:frida_trace",
            name="Frida Trace",
            description="Live instrumentation",
            risk_level="HIGH_RISK",
            source=CapabilitySource.CLI,
        )
        self.bus.register(cap)
        # Caller-supplied context={"approved": True} must NOT bypass Governance
        with patch.dict(os.environ, {"GOVERNANCE_AUTO_APPROVE": ""}):
            blocked_res = self.bus.execute(
                "re:frida_trace", {"pid": 1234}, context={"approved": True}
            )
            self.assertIn("error", blocked_res)
            self.assertTrue(blocked_res.get("requires_approval"))

        # Trusted GOVERNANCE_AUTO_APPROVE=true approves execution
        with patch.dict(os.environ, {"GOVERNANCE_AUTO_APPROVE": "true"}):
            res = self.bus.execute("re:frida_trace", {"pid": 1234})
            self.assertEqual(res.get("status"), "ok")
            ctx = res.get("context", {})
            self.assertEqual(ctx.get("re_policy", {}).get("tier"), ReRiskTier.HIGH_RISK.value)
            self.assertTrue(ctx.get("re_policy", {}).get("network_disabled"))
            self.assertTrue(ctx.get("network_disabled"))
            self.assertEqual(ctx.get("re_policy", {}).get("docker_flags"), ["--network", "none"])

    def test_critical_risk_blocked(self) -> None:
        cap = DummyReCapability(
            id="re:critical_op",
            name="Critical Op",
            description="Forbidden op",
            risk_level="CRITICAL",
            source=CapabilitySource.CUSTOM,
        )
        self.bus.register(cap)
        res = self.bus.execute("re:critical_op", {})
        self.assertIn("error", res)
        self.assertIn("Governance blocked", res["error"])


if __name__ == "__main__":
    unittest.main()
