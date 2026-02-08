"""
Tests for Mekong Governance Layer.

Tests cover:
- Action classification (safe, review_required, forbidden)
- Halt/resume functionality
- Audit trail persistence and FIFO eviction
- Case-insensitive pattern matching
- GovernanceDecision and AuditEntry dataclasses
"""

import os
import tempfile
import unittest

from src.core.governance import (
    ActionClass,
    AuditEntry,
    Governance,
    GovernanceDecision,
)


class TestActionClassEnum(unittest.TestCase):
    """Tests for ActionClass enum values."""

    def test_safe_value(self):
        """SAFE should have value 'safe'."""
        self.assertEqual(ActionClass.SAFE.value, "safe")

    def test_review_required_value(self):
        """REVIEW_REQUIRED should have value 'review_required'."""
        self.assertEqual(ActionClass.REVIEW_REQUIRED.value, "review_required")

    def test_forbidden_value(self):
        """FORBIDDEN should have value 'forbidden'."""
        self.assertEqual(ActionClass.FORBIDDEN.value, "forbidden")


class TestGovernanceDecision(unittest.TestCase):
    """Tests for GovernanceDecision dataclass."""

    def test_fields(self):
        """GovernanceDecision should have expected fields."""
        d = GovernanceDecision(
            action_class=ActionClass.SAFE, reason="ok"
        )
        self.assertEqual(d.action_class, ActionClass.SAFE)
        self.assertEqual(d.reason, "ok")
        self.assertFalse(d.requires_approval)
        self.assertFalse(d.approved)

    def test_timestamp_auto(self):
        """GovernanceDecision should auto-set timestamp."""
        d = GovernanceDecision(action_class=ActionClass.SAFE, reason="t")
        self.assertGreater(d.timestamp, 0)


class TestClassifySafe(unittest.TestCase):
    """Tests for safe goal classification."""

    def setUp(self):
        self.gov = Governance(audit_path="/tmp/_mekong_test_audit.yaml")

    def test_safe_goal(self):
        """Normal goals should be classified as SAFE."""
        d = self.gov.classify("list files in current directory")
        self.assertEqual(d.action_class, ActionClass.SAFE)

    def test_safe_reason(self):
        """Safe decision should say no dangerous patterns."""
        d = self.gov.classify("echo hello")
        self.assertIn("No dangerous", d.reason)


class TestClassifyForbidden(unittest.TestCase):
    """Tests for forbidden goal classification."""

    def setUp(self):
        self.gov = Governance(audit_path="/tmp/_mekong_test_audit.yaml")

    def test_rm_rf_forbidden(self):
        """'rm -rf' should be FORBIDDEN."""
        d = self.gov.classify("rm -rf /tmp/test")
        self.assertEqual(d.action_class, ActionClass.FORBIDDEN)

    def test_drop_database_forbidden(self):
        """'drop database' should be FORBIDDEN."""
        d = self.gov.classify("drop database production")
        self.assertEqual(d.action_class, ActionClass.FORBIDDEN)

    def test_delete_all_forbidden(self):
        """'delete all' should be FORBIDDEN."""
        d = self.gov.classify("delete all records from users")
        self.assertEqual(d.action_class, ActionClass.FORBIDDEN)

    def test_destroy_forbidden(self):
        """'destroy' should be FORBIDDEN."""
        d = self.gov.classify("destroy the infrastructure")
        self.assertEqual(d.action_class, ActionClass.FORBIDDEN)

    def test_truncate_forbidden(self):
        """'truncate' should be FORBIDDEN."""
        d = self.gov.classify("truncate the logs table")
        self.assertEqual(d.action_class, ActionClass.FORBIDDEN)

    def test_case_insensitive(self):
        """Classification should be case-insensitive."""
        d = self.gov.classify("RM -RF /var/data")
        self.assertEqual(d.action_class, ActionClass.FORBIDDEN)


class TestClassifyReview(unittest.TestCase):
    """Tests for review-required goal classification."""

    def setUp(self):
        self.gov = Governance(audit_path="/tmp/_mekong_test_audit.yaml")

    def test_deploy_prod(self):
        """'deploy to prod' should be REVIEW_REQUIRED."""
        d = self.gov.classify("deploy to production")
        self.assertEqual(d.action_class, ActionClass.REVIEW_REQUIRED)
        self.assertTrue(d.requires_approval)

    def test_push_main(self):
        """'push to main' should be REVIEW_REQUIRED."""
        d = self.gov.classify("push changes to main branch")
        self.assertEqual(d.action_class, ActionClass.REVIEW_REQUIRED)

    def test_migrate(self):
        """'migrate' should be REVIEW_REQUIRED."""
        d = self.gov.classify("migrate database schema")
        self.assertEqual(d.action_class, ActionClass.REVIEW_REQUIRED)


class TestHaltResume(unittest.TestCase):
    """Tests for halt/resume functionality."""

    def setUp(self):
        self.gov = Governance(audit_path="/tmp/_mekong_test_audit.yaml")

    def test_not_halted_by_default(self):
        """Governance should not be halted by default."""
        self.assertFalse(self.gov.is_halted())

    def test_halt(self):
        """halt() should set halted state."""
        self.gov.halt()
        self.assertTrue(self.gov.is_halted())

    def test_resume(self):
        """resume() should clear halted state."""
        self.gov.halt()
        self.gov.resume()
        self.assertFalse(self.gov.is_halted())


class TestAuditTrail(unittest.TestCase):
    """Tests for audit trail persistence."""

    def setUp(self):
        self.tmpfile = tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False
        )
        self.tmpfile.close()
        self.gov = Governance(audit_path=self.tmpfile.name)

    def tearDown(self):
        os.unlink(self.tmpfile.name)

    def test_record_and_retrieve(self):
        """Recorded entries should be retrievable."""
        entry = AuditEntry(goal="test", action_class="safe", result="executed")
        self.gov.record_audit(entry)
        trail = self.gov.get_audit_trail()
        self.assertEqual(len(trail), 1)
        self.assertEqual(trail[0].goal, "test")

    def test_persistence(self):
        """Audit trail should survive save/load cycle."""
        entry = AuditEntry(goal="persist", action_class="safe", result="ok")
        self.gov.record_audit(entry)

        gov2 = Governance(audit_path=self.tmpfile.name)
        trail = gov2.get_audit_trail()
        self.assertEqual(len(trail), 1)
        self.assertEqual(trail[0].goal, "persist")

    def test_fifo_eviction(self):
        """Audit trail should evict old entries past MAX_AUDIT."""
        for i in range(Governance.MAX_AUDIT + 5):
            self.gov.record_audit(
                AuditEntry(goal=f"goal-{i}", action_class="safe", result="ok")
            )
        trail = self.gov.get_audit_trail(limit=Governance.MAX_AUDIT + 10)
        self.assertLessEqual(len(trail), Governance.MAX_AUDIT)

    def test_get_audit_trail_limit(self):
        """get_audit_trail should respect limit parameter."""
        for i in range(10):
            self.gov.record_audit(
                AuditEntry(goal=f"g-{i}", action_class="safe", result="ok")
            )
        trail = self.gov.get_audit_trail(limit=3)
        self.assertEqual(len(trail), 3)

    def test_request_approval_returns_true(self):
        """request_approval placeholder should return True."""
        d = GovernanceDecision(
            action_class=ActionClass.REVIEW_REQUIRED, reason="test"
        )
        result = self.gov.request_approval("deploy prod", d)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
