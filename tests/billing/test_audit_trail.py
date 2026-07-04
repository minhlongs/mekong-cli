"""Tests for BillingAuditTrail — immutable financial audit log."""
import json
import time


from src.billing.audit_trail import (
    AuditEntry,
    BillingAuditTrail,
    get_audit_trail,
    reset_audit_trail,
)


def _make_entry(
    tenant_id: str = "tenant_abc",
    action: str = "debit",
    amount: float = 1.0,
    balance_before: float = 10.0,
    balance_after: float = 9.0,
    reason: str = "mission usage",
    mission_id: str | None = None,
    idempotency_key: str | None = None,
) -> AuditEntry:
    return AuditEntry(
        timestamp=time.time(),
        tenant_id=tenant_id,
        action=action,
        amount=amount,
        balance_before=balance_before,
        balance_after=balance_after,
        reason=reason,
        mission_id=mission_id,
        idempotency_key=idempotency_key,
    )


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_record_returns_entry_id(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        entry = _make_entry()
        entry_id = trail.record(entry)
        assert entry_id  # non-empty string
        assert "tenant_abc" in entry_id
        assert "debit" in entry_id

    def test_record_creates_jsonl_file(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="t1"))
        log_file = tmp_path / "t1.jsonl"
        assert log_file.exists()

    def test_record_appends_valid_json(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="t2", reason="first"))
        trail.record(_make_entry(tenant_id="t2", reason="second"))
        lines = (tmp_path / "t2.jsonl").read_text().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            parsed = json.loads(line)
            assert parsed["tenant_id"] == "t2"

    def test_record_includes_optional_fields(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        entry = _make_entry(
            tenant_id="t3",
            mission_id="mission-99",
            idempotency_key="idem-xyz",
        )
        trail.record(entry)
        data = json.loads((tmp_path / "t3.jsonl").read_text().strip())
        assert data["mission_id"] == "mission-99"
        assert data["idempotency_key"] == "idem-xyz"

    def test_record_none_optional_fields_serialized(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="t4"))
        data = json.loads((tmp_path / "t4.jsonl").read_text().strip())
        assert data["mission_id"] is None
        assert data["idempotency_key"] is None


# ---------------------------------------------------------------------------
# get_history()
# ---------------------------------------------------------------------------


class TestGetHistory:
    def test_empty_when_no_file(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        assert trail.get_history("nonexistent") == []

    def test_returns_entries_in_order(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        for i in range(5):
            trail.record(_make_entry(tenant_id="t5", reason=f"event-{i}"))
        history = trail.get_history("t5")
        reasons = [e["reason"] for e in history]
        assert reasons == [f"event-{i}" for i in range(5)]

    def test_limit_returns_most_recent(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        for i in range(10):
            trail.record(_make_entry(tenant_id="t6", reason=f"event-{i}"))
        history = trail.get_history("t6", limit=3)
        assert len(history) == 3
        assert history[-1]["reason"] == "event-9"

    def test_limit_larger_than_entries(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="t7"))
        history = trail.get_history("t7", limit=100)
        assert len(history) == 1

    def test_default_limit_100(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        for _ in range(120):
            trail.record(_make_entry(tenant_id="t8"))
        assert len(trail.get_history("t8")) == 100


# ---------------------------------------------------------------------------
# get_balance_proof()
# ---------------------------------------------------------------------------


class TestGetBalanceProof:
    def test_empty_tenant_returns_zero(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        proof = trail.get_balance_proof("nobody")
        assert proof["calculated_balance"] == 0.0
        assert proof["entries_count"] == 0
        assert proof["last_entry"] is None

    def test_credits_increase_balance(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="bp1", action="credit", amount=100.0))
        trail.record(_make_entry(tenant_id="bp1", action="credit", amount=50.0))
        proof = trail.get_balance_proof("bp1")
        assert proof["calculated_balance"] == 150.0

    def test_debits_decrease_balance(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="bp2", action="credit", amount=100.0))
        trail.record(_make_entry(tenant_id="bp2", action="debit", amount=30.0))
        proof = trail.get_balance_proof("bp2")
        assert proof["calculated_balance"] == 70.0

    def test_refund_increases_balance(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="bp3", action="credit", amount=100.0))
        trail.record(_make_entry(tenant_id="bp3", action="debit", amount=30.0))
        trail.record(_make_entry(tenant_id="bp3", action="refund", amount=10.0))
        proof = trail.get_balance_proof("bp3")
        assert proof["calculated_balance"] == 80.0

    def test_adjustment_decreases_balance(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="bp4", action="credit", amount=100.0))
        trail.record(_make_entry(tenant_id="bp4", action="adjustment", amount=5.0))
        proof = trail.get_balance_proof("bp4")
        assert proof["calculated_balance"] == 95.0

    def test_last_entry_populated(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="bp5", action="credit", amount=100.0, reason="top-up"))
        proof = trail.get_balance_proof("bp5")
        assert proof["last_entry"] is not None
        assert proof["last_entry"]["reason"] == "top-up"

    def test_entries_count(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        for _ in range(7):
            trail.record(_make_entry(tenant_id="bp6", action="debit", amount=1.0))
        proof = trail.get_balance_proof("bp6")
        assert proof["entries_count"] == 7


# ---------------------------------------------------------------------------
# JSONL append-only format integrity
# ---------------------------------------------------------------------------


class TestJsonlFormat:
    def test_each_line_is_independent_json(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        actions = ["credit", "debit", "refund", "adjustment"]
        for action in actions:
            trail.record(_make_entry(tenant_id="fmt1", action=action))
        lines = (tmp_path / "fmt1.jsonl").read_text().strip().split("\n")
        assert len(lines) == 4
        for i, line in enumerate(lines):
            obj = json.loads(line)
            assert obj["action"] == actions[i]

    def test_file_ends_with_newline(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="fmt2"))
        raw = (tmp_path / "fmt2.jsonl").read_text()
        assert raw.endswith("\n")

    def test_all_required_fields_present(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="fmt3"))
        data = json.loads((tmp_path / "fmt3.jsonl").read_text().strip())
        required = {
            "timestamp", "tenant_id", "action", "amount",
            "balance_before", "balance_after", "reason",
        }
        assert required.issubset(data.keys())


# ---------------------------------------------------------------------------
# Multiple tenants isolation
# ---------------------------------------------------------------------------


class TestMultipleTenants:
    def test_separate_files_per_tenant(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="alice"))
        trail.record(_make_entry(tenant_id="bob"))
        assert (tmp_path / "alice.jsonl").exists()
        assert (tmp_path / "bob.jsonl").exists()

    def test_tenant_data_is_isolated(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="alice", action="credit", amount=500.0))
        trail.record(_make_entry(tenant_id="bob", action="credit", amount=200.0))
        alice_proof = trail.get_balance_proof("alice")
        bob_proof = trail.get_balance_proof("bob")
        assert alice_proof["calculated_balance"] == 500.0
        assert bob_proof["calculated_balance"] == 200.0

    def test_one_tenant_does_not_appear_in_another_history(self, tmp_path):
        trail = BillingAuditTrail(log_dir=str(tmp_path))
        trail.record(_make_entry(tenant_id="carol", reason="carol-event"))
        trail.record(_make_entry(tenant_id="dave", reason="dave-event"))
        carol_history = trail.get_history("carol")
        assert all(e["tenant_id"] == "carol" for e in carol_history)


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------


class TestSingleton:
    def teardown_method(self):
        reset_audit_trail()

    def test_get_audit_trail_returns_same_instance(self):
        a = get_audit_trail()
        b = get_audit_trail()
        assert a is b

    def test_reset_creates_new_instance(self):
        a = get_audit_trail()
        reset_audit_trail()
        b = get_audit_trail()
        assert a is not b
