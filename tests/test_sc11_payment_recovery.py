# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""SC11 regression tests for retry-safe VietQR revenue recovery."""

from __future__ import annotations

import concurrent.futures
import sqlite3
import json
import threading

import pytest

from src.core.ke_toan_engine import KeToanEngine
from src.core.promise.evidence import EvidenceIntegrityError, EvidenceStore
from src.core.promise.ops.handlers_finance import vietqr_record_reconciled_payment
from src.core.promise.runtime import HandlerContext
from src.core.vietqr_engine import VietQrEngine


@pytest.fixture()
def recovery_context(tmp_path):
    workspace_id = "sc11-recovery-workspace"
    root = tmp_path / "workspace"
    state = tmp_path / "state"
    accounting = KeToanEngine(db_path=state / "workspaces" / workspace_id / "ke_toan.db")
    invoice = accounting.create_invoice(amount=20_000_000, buyer="SC11 Buyer")
    context = HandlerContext(
        run_id="run-sc11-recovery",
        workspace_id=workspace_id,
        principal_id="sc11-founder",
        workspace_root=root,
        state_dir=state,
        params={},
    )
    params = {
        "bank_tx_id": "SC11-BANK-001",
        "amount_vnd": 20_000_000,
        "memo": "INV SC11-001",
        "provider": "SEPAY",
        "provider_reference": "SC11-STATEMENT-001",
        "invoice_ref": invoice["invoice_id"],
        "currency": "VND",
        "matched_order_id": "mk-a1b2c3",
        "bin_code": "970422",
    }
    return context, params


def call(context, params):
    return vietqr_record_reconciled_payment(context, **params)


def revenue_rows(context):
    return context.evidence_store().query("revenue_transactions", context.workspace_id)


def test_retry_recovers_bank_commit_after_evidence_failure_before_commit(
    recovery_context, monkeypatch
):
    context, params = recovery_context
    original_factory = context.evidence_store

    class FailingBeforeWrite:
        def record_revenue_transaction_once(self, **fields):
            raise sqlite3.OperationalError("synthetic evidence write failure before commit")

    actual_store = original_factory()
    monkeypatch.setattr(HandlerContext, "evidence_store", lambda self: FailingBeforeWrite())
    with pytest.raises(sqlite3.OperationalError, match="before commit"):
        call(context, params)
    assert actual_store.query("revenue_transactions", context.workspace_id) == []

    monkeypatch.setattr(HandlerContext, "evidence_store", lambda self: actual_store)
    recovered = call(context, params)
    assert recovered["status"] == "RECONCILED"
    assert recovered["recovered"] is True
    assert len(revenue_rows(context)) == 1


def test_retry_after_uncertain_evidence_commit_returns_existing_fact(
    recovery_context, monkeypatch
):
    context, params = recovery_context
    store = context.evidence_store()
    original_method = store.record_revenue_transaction_once
    calls = 0

    def commit_then_raise(**fields):
        nonlocal calls
        calls += 1
        result = original_method(**fields)
        if calls == 1:
            raise sqlite3.OperationalError("synthetic lost response after evidence commit")
        return result

    monkeypatch.setattr(store, "record_revenue_transaction_once", commit_then_raise)
    monkeypatch.setattr(HandlerContext, "evidence_store", lambda self: store)
    with pytest.raises(sqlite3.OperationalError, match="after evidence commit"):
        call(context, params)
    assert len(revenue_rows(context)) == 1

    retried = call(context, params)
    assert retried["status"] == "RECONCILED"
    assert retried["is_duplicate"] is True
    assert retried["existing_revenue_tx_id"] == revenue_rows(context)[0]["tx_id"]
    assert len(revenue_rows(context)) == 1


def test_concurrent_retries_write_one_revenue_fact(recovery_context):
    context, params = recovery_context

    def retry_once(_index):
        return call(context, params)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        outcomes = list(executor.map(retry_once, range(16)))

    assert len(revenue_rows(context)) == 1
    assert all(outcome["status"] == "RECONCILED" for outcome in outcomes)
    assert sum(not outcome["is_duplicate"] for outcome in outcomes) == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("amount_vnd", 19_000_000),
        ("matched_order_id", "mk-different"),
        ("provider", "MBBANK"),
        ("invoice_ref", "INV-DIFFERENT"),
    ],
)
def test_duplicate_bank_payload_conflicts_are_rejected(recovery_context, field, value):
    context, params = recovery_context
    first = call(context, params)
    assert first["status"] == "RECONCILED"

    if field == "invoice_ref":
        accounting = KeToanEngine(
            db_path=context.state_dir
            / "workspaces"
            / context.workspace_id
            / "ke_toan.db"
        )
        value = accounting.create_invoice(amount=20_000_000, buyer="Other SC11 Buyer")[
            "invoice_id"
        ]
    changed = {**params, field: value}
    with pytest.raises(ValueError, match=field):
        call(context, changed)
    assert len(revenue_rows(context)) == 1


def test_existing_revenue_with_changed_provider_reference_is_rejected(recovery_context):
    context, params = recovery_context
    call(context, params)
    with pytest.raises(ValueError, match="provider_reference"):
        call(context, {**params, "provider_reference": "SC11-OTHER-REF"})
    assert len(revenue_rows(context)) == 1


def test_legacy_random_id_revenue_is_reused_without_double_counting(recovery_context):
    context, params = recovery_context
    store = context.evidence_store()
    legacy = store.record_revenue_transaction(
        workspace_id=context.workspace_id,
        run_id="legacy-run",
        provider=params["provider"],
        method="vietqr_bank_transfer",
        amount=params["amount_vnd"],
        currency=params["currency"],
        invoice_ref=params["invoice_ref"],
        status="RECONCILED",
        provider_confirmation={
            "provider": params["provider"],
            "reference": params["provider_reference"],
            "bank_tx_id": params["bank_tx_id"],
            "amount_vnd": params["amount_vnd"],
            "currency": params["currency"],
            "memo": params["memo"],
            "matched_order_id": params["matched_order_id"],
        },
        reconciled_by="legacy-founder",
    )

    result = call(context, params)

    assert result["status"] == "RECONCILED"
    assert result["is_duplicate"] is True
    assert result["legacy_revenue_match"] is True
    assert result["existing_revenue_tx_id"] == legacy["tx_id"]
    assert len(revenue_rows(context)) == 1


def test_conflicting_legacy_revenue_is_not_reused(recovery_context):
    context, params = recovery_context
    store = context.evidence_store()
    store.record_revenue_transaction(
        workspace_id=context.workspace_id,
        run_id="legacy-run",
        provider=params["provider"],
        method="vietqr_bank_transfer",
        amount=19_000_000,
        currency=params["currency"],
        invoice_ref=params["invoice_ref"],
        status="RECONCILED",
        provider_confirmation={
            "provider": params["provider"],
            "reference": params["provider_reference"],
            "bank_tx_id": params["bank_tx_id"],
            "amount_vnd": 19_000_000,
            "currency": params["currency"],
            "memo": params["memo"],
            "matched_order_id": params["matched_order_id"],
        },
    )

    with pytest.raises(EvidenceIntegrityError, match="amount"):
        call(context, params)
    assert len(revenue_rows(context)) == 1


def test_stable_bank_identity_is_workspace_scoped(tmp_path):
    store = EvidenceStore(tmp_path / "evidence.db")
    first = store.record_revenue_transaction_once(
        workspace_id="workspace-a",
        bank_tx_id="same-bank-id",
        provider="SEPAY",
        amount=100,
        currency="VND",
        invoice_ref="invoice-a",
        status="RECONCILED",
        provider_confirmation={
            "provider": "SEPAY",
            "reference": "reference-1",
            "bank_tx_id": "same-bank-id",
            "amount_vnd": 100,
            "currency": "VND",
            "memo": "memo",
            "matched_order_id": None,
        },
    )
    second = store.record_revenue_transaction_once(
        workspace_id="workspace-b",
        bank_tx_id="same-bank-id",
        provider="SEPAY",
        amount=100,
        currency="VND",
        invoice_ref="invoice-b",
        status="RECONCILED",
        provider_confirmation={
            "provider": "SEPAY",
            "reference": "reference-1",
            "bank_tx_id": "same-bank-id",
            "amount_vnd": 100,
            "currency": "VND",
            "memo": "memo",
            "matched_order_id": None,
        },
    )

    assert first["tx_id"] != second["tx_id"]
    assert len(store.query("revenue_transactions", "workspace-a")) == 1
    assert len(store.query("revenue_transactions", "workspace-b")) == 1


def bank_engine(context):
    return VietQrEngine(
        context.state_dir / "workspaces" / context.workspace_id / "vietqr.db"
    )


def record_legacy_bank(context, params):
    return bank_engine(context).record_transaction(**{
        key: params[key] for key in
        ("bank_tx_id", "amount_vnd", "memo", "bin_code", "matched_order_id")
    })


def seed_legacy_evidence(context, params):
    return context.evidence_store().record_revenue_transaction(
        workspace_id=context.workspace_id, run_id="legacy-run",
        provider=params["provider"], method="vietqr_bank_transfer",
        amount=params["amount_vnd"], currency=params["currency"],
        invoice_ref=params["invoice_ref"], status="RECONCILED",
        provider_confirmation={
            "provider": params["provider"], "reference": params["provider_reference"],
            **{key: params[key] for key in (
                "bank_tx_id", "amount_vnd", "currency", "memo", "matched_order_id"
            )},
        },
        reconciled_by="legacy-founder",
    )


def different_invoice(context):
    return KeToanEngine(
        context.state_dir / "workspaces" / context.workspace_id / "ke_toan.db"
    ).create_invoice(amount=20_000_000, buyer="Other Buyer")["invoice_id"]


@pytest.mark.parametrize("field,value", [
    ("provider", "MBBANK"), ("provider_reference", "another-statement"),
    ("invoice_ref", None), ("currency", "USD"),
    ("amount_vnd", 19_000_000), ("memo", "changed memo"),
    ("bin_code", "970436"), ("matched_order_id", "another-order"),
])
def test_bank_only_failure_preserves_full_intent(recovery_context, monkeypatch, field, value):
    context, params = recovery_context
    store = context.evidence_store()

    def fail_before_write(**fields):
        raise sqlite3.OperationalError("before evidence commit")

    with monkeypatch.context() as patch:
        patch.setattr(store, "record_revenue_transaction_once", fail_before_write)
        patch.setattr(HandlerContext, "evidence_store", lambda self: store)
        with pytest.raises(sqlite3.OperationalError, match="before evidence commit"):
            call(context, params)
    original_bank = bank_engine(context).list_transactions()[0]
    intent = json.loads(original_bank["reconciliation_intent_json"])
    assert intent == {"workspace_id": context.workspace_id, **params}
    if field == "invoice_ref":
        value = different_invoice(context)
    with pytest.raises(ValueError, match=field):
        call(context, {**params, field: value})
    assert bank_engine(context).list_transactions() == [original_bank]
    assert revenue_rows(context) == []
    assert call(context, params)["recovered"] is True
    assert len(revenue_rows(context)) == 1


@pytest.mark.parametrize("field,value", [
    ("provider", "MBBANK"), ("provider_reference", "another-statement"),
    ("invoice_ref", None), ("currency", "USD"),
])
def test_concurrent_distinct_metadata_has_only_one_winner(recovery_context, field, value):
    context, params = recovery_context
    if field == "invoice_ref":
        value = different_invoice(context)
    changed = {**params, field: value}
    barrier = threading.Barrier(2)

    def submit(payload):
        barrier.wait(timeout=10)
        try:
            return call(context, payload)
        except ValueError as exc:
            return exc

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(submit, [params, changed]))
    successes = [result for result in results if isinstance(result, dict)]
    failures = [result for result in results if isinstance(result, ValueError)]
    assert len(successes) == len(failures) == 1
    assert field in str(failures[0])
    assert len(revenue_rows(context)) == 1
    stored = json.loads(bank_engine(context).list_transactions()[0]["reconciliation_intent_json"])
    assert successes[0]["reconciliation"][field] == stored[field]


def test_legacy_bank_only_requires_manual_reconciliation(recovery_context):
    context, params = recovery_context
    original = record_legacy_bank(context, params)
    with pytest.raises(EvidenceIntegrityError, match="manual reconciliation required"):
        call(context, params)
    assert revenue_rows(context) == []
    assert bank_engine(context).list_transactions()[0]["transaction_id"] == original["transaction_id"]
    assert bank_engine(context).list_transactions()[0]["reconciliation_intent_json"] is None


def test_legacy_bank_and_matching_evidence_are_reused_unchanged(recovery_context):
    context, params = recovery_context
    record_legacy_bank(context, params)
    legacy = seed_legacy_evidence(context, params)
    before = revenue_rows(context)
    result = call(context, params)
    assert result["status"] == "RECONCILED"
    assert result["is_duplicate"] is True
    assert result["legacy_revenue_match"] is True
    assert result["revenue_record"]["tx_id"] == legacy["tx_id"]
    assert revenue_rows(context) == before
    assert bank_engine(context).list_transactions()[0]["reconciliation_intent_json"] is None


@pytest.mark.parametrize("field,value", [
    ("provider", "MBBANK"), ("provider_reference", "another-statement"),
    ("invoice_ref", None), ("currency", "USD"),
    ("memo", "different memo"), ("amount_vnd", 19_000_000),
    ("matched_order_id", "another-order"), ("bin_code", "970436"),
])
def test_legacy_evidence_reuse_rejects_conflicts(recovery_context, field, value):
    context, params = recovery_context
    record_legacy_bank(context, params)
    seed_legacy_evidence(context, params)
    before = revenue_rows(context)
    if field == "invoice_ref":
        value = different_invoice(context)
    with pytest.raises((EvidenceIntegrityError, ValueError), match=field):
        call(context, {**params, field: value})
    assert revenue_rows(context) == before


@pytest.mark.parametrize("field,value", [
    ("amount_vnd", 19_000_000), ("memo", "tampered"),
    ("bin_code", "970436"), ("matched_order_id", "another-order"),
])
def test_bank_fields_must_agree_even_with_matching_intent(recovery_context, field, value):
    context, params = recovery_context
    call(context, params)
    engine = bank_engine(context)
    before = revenue_rows(context)
    assert field in {"amount_vnd", "memo", "bin_code", "matched_order_id"}
    with sqlite3.connect(str(engine.db_path)) as conn:
        conn.execute(f"UPDATE transactions SET {field} = ?", (value,))
    with pytest.raises(ValueError, match=field):
        call(context, params)
    assert revenue_rows(context) == before


@pytest.mark.parametrize("intent", ["", "{", "[]", "{}", "null"])
def test_malformed_or_incomplete_intent_is_not_legacy(recovery_context, intent):
    context, params = recovery_context
    call(context, params)
    engine = bank_engine(context)
    before = revenue_rows(context)
    with sqlite3.connect(str(engine.db_path)) as conn:
        conn.execute("UPDATE transactions SET reconciliation_intent_json = ?", (intent,))
    with pytest.raises(ValueError, match="intent"):
        call(context, params)
    assert revenue_rows(context) == before


def create_old_bank_database(path):
    with sqlite3.connect(str(path)) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("""CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY, bank_tx_id TEXT UNIQUE NOT NULL,
            bin_code TEXT NOT NULL, amount_vnd INTEGER NOT NULL, memo TEXT NOT NULL,
            matched_order_id TEXT, status TEXT NOT NULL, received_at TEXT NOT NULL
        )""")
        conn.execute("""INSERT INTO transactions VALUES
            ('old-tx', 'old-bank', '970422', 100, 'old-memo', NULL, 'success', '2026-01-01')""")


def test_schema_upgrade_preserves_rows_and_creates_readable_backup(tmp_path):
    path = tmp_path / "bank.db"
    create_old_bank_database(path)
    engine = VietQrEngine(path)
    assert engine.list_transactions()[0]["reconciliation_intent_json"] is None
    backups = list(tmp_path.glob("bank.db.pre-reconciliation-intent-*.bak"))
    assert len(backups) == 1
    with sqlite3.connect(str(backups[0])) as backup:
        assert backup.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup.execute("SELECT bank_tx_id, amount_vnd FROM transactions").fetchall() == [
            ("old-bank", 100)
        ]
        assert "reconciliation_intent_json" not in {
            row[1] for row in backup.execute("PRAGMA table_info(transactions)")
        }
    VietQrEngine(path)
    assert list(tmp_path.glob("bank.db.pre-reconciliation-intent-*.bak")) == backups


@pytest.mark.parametrize("old_schema", [False, True])
def test_concurrent_schema_initialization_is_serialized(tmp_path, old_schema):
    path = tmp_path / "bank.db"
    if old_schema:
        create_old_bank_database(path)
    barrier = threading.Barrier(8)

    def initialize(_):
        barrier.wait(timeout=10)
        return VietQrEngine(path).get_default_account()["account_id"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        assert list(executor.map(initialize, range(8))) == ["ACC-MEKONG-CORP"] * 8
    with sqlite3.connect(str(path)) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT count(*) FROM bank_accounts").fetchone()[0] == 1
        assert [row[1] for row in conn.execute("PRAGMA table_info(transactions)")].count(
            "reconciliation_intent_json"
        ) == 1
    assert len(list(tmp_path.glob("bank.db.pre-reconciliation-intent-*.bak"))) == int(old_schema)


def test_uncertain_bank_commit_recovers_without_changing_intent(recovery_context, monkeypatch):
    context, params = recovery_context
    original = VietQrEngine.record_transaction

    def commit_then_raise(self, **fields):
        original(self, **fields)
        raise sqlite3.OperationalError("lost bank commit response")

    with monkeypatch.context() as patch:
        patch.setattr(VietQrEngine, "record_transaction", commit_then_raise)
        with pytest.raises(sqlite3.OperationalError, match="lost bank commit response"):
            call(context, params)
    assert revenue_rows(context) == []
    original_bank = bank_engine(context).list_transactions()[0]
    recovered = call(context, params)
    assert recovered["status"] == "RECONCILED"
    assert recovered["recovered"] is True
    assert bank_engine(context).list_transactions() == [original_bank]
    assert len(revenue_rows(context)) == 1


def test_schema_backup_failure_does_not_upgrade_or_lose_rows(tmp_path, monkeypatch):
    path = tmp_path / "bank.db"
    create_old_bank_database(path)
    original_connect = sqlite3.connect

    def reject_backup(database, *args, **kwargs):
        if str(database).endswith(".bak"):
            raise sqlite3.OperationalError("synthetic backup failure")
        return original_connect(database, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(sqlite3, "connect", reject_backup)
        with pytest.raises(sqlite3.OperationalError, match="backup failure"):
            VietQrEngine(path)
    with sqlite3.connect(str(path)) as conn:
        assert conn.execute("SELECT bank_tx_id, amount_vnd FROM transactions").fetchall() == [
            ("old-bank", 100)
        ]
        assert "reconciliation_intent_json" not in {
            row[1] for row in conn.execute("PRAGMA table_info(transactions)")
        }
    assert VietQrEngine(path).list_transactions()[0]["reconciliation_intent_json"] is None


@pytest.mark.parametrize("currency", ["USD", "EUR", "", "usd"])
def test_non_vnd_handler_rejected_before_payment_writes(recovery_context, currency):
    context, params = recovery_context
    engine = bank_engine(context)
    assert engine.list_transactions() == []
    assert revenue_rows(context) == []
    with pytest.raises(ValueError, match="currency.*VND"):
        call(context, {**params, "currency": currency})
    assert engine.list_transactions() == []
    assert revenue_rows(context) == []
    valid = call(context, params)
    assert valid["status"] == "RECONCILED"
    assert len(engine.list_transactions()) == 1
    assert len(revenue_rows(context)) == 1
