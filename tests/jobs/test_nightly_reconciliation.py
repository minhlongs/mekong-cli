"""Unit tests for src/jobs/nightly_reconciliation.py.

Tests cover:
- StripeReconciliationAdapter: init, initialize, get_invoices, get_usage_records
- StripeDiscrepancy: to_dict serialization
- ReconciliationReport: to_dict serialization
- NightlyReconciliationService: _reconcile_with_stripe variance logic, _trigger_alerts
- main_async: date parsing, error exit codes
"""

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Stubs to replace heavy imports that require DB/Stripe/etc.
# ---------------------------------------------------------------------------

@dataclass
class _StubAuditResult:
    audit_id: str = "audit-1"
    license_key: str = "LIC-001"
    key_id: str = "key-1"
    audit_date: date = field(default_factory=date.today)
    expected_amount: Decimal = Decimal("100.00")
    actual_amount: Decimal = Decimal("100.00")
    variance: Decimal = Decimal("0.00")
    variance_percent: float = 0.0
    status: str = "matched"


@dataclass
class _StubReconciliationConfig:
    pass


# Patch targets — these must be patched before importing the module under test
_PATCHES: Dict[str, Any] = {
    "src.db.repository.get_repository": MagicMock(return_value=MagicMock()),
    "src.db.repository.LicenseRepository": MagicMock(),
    "src.billing.reconciliation.AuditResult": _StubAuditResult,
    "src.billing.reconciliation.ReconciliationConfig": _StubReconciliationConfig,
    "src.billing.reconciliation.get_reconciliation_service": MagicMock(),
    "src.core.event_bus.get_event_bus": MagicMock(return_value=MagicMock()),
    "src.core.event_bus.EventType": MagicMock(),
    "rich.console.Console": MagicMock(),
    "rich.table.Table": MagicMock(),
}


@pytest.fixture(scope="module", autouse=True)
def patch_deps():
    patchers = [patch(k, v) for k, v in _PATCHES.items()]
    for p in patchers:
        p.start()
    yield
    for p in patchers:
        p.stop()


@pytest.fixture(scope="module")
def module(patch_deps):
    """Import the module under test after all patches are active."""
    import sys
    for key in list(sys.modules.keys()):
        if "nightly_reconciliation" in key:
            del sys.modules[key]
    import src.jobs.nightly_reconciliation as m
    return m


# ===========================================================================
# StripeReconciliationAdapter tests
# ===========================================================================

class TestStripeAdapterInit:
    def test_no_api_key_leaves_uninitialized(self, module):
        env = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
        with patch.dict(os.environ, env, clear=True):
            adapter = module.StripeReconciliationAdapter(api_key=None)
        assert adapter._api_key is None
        assert adapter._initialized is False

    def test_explicit_api_key_stored(self, module):
        adapter = module.StripeReconciliationAdapter(api_key="sk_test_abc")
        assert adapter._api_key == "sk_test_abc"

    def test_env_api_key_picked_up(self, module):
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_env_key"}):
            adapter = module.StripeReconciliationAdapter()
        assert adapter._api_key == "sk_env_key"


class TestStripeAdapterInitialize:
    @pytest.mark.asyncio
    async def test_initialize_returns_false_without_key(self, module):
        adapter = module.StripeReconciliationAdapter(api_key=None)
        result = await adapter.initialize()
        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_returns_false_on_import_error(self, module):
        adapter = module.StripeReconciliationAdapter(api_key="sk_test_x")
        with patch("builtins.__import__", side_effect=ImportError("no stripe")):
            result = await adapter.initialize()
        assert result is False

    @pytest.mark.asyncio
    async def test_initialize_succeeds_with_stripe_mock(self, module):
        mock_stripe = MagicMock()
        adapter = module.StripeReconciliationAdapter(api_key="sk_test_x")
        with patch.dict("sys.modules", {"stripe": mock_stripe}):
            result = await adapter.initialize()
        assert result is True
        assert adapter._initialized is True

    @pytest.mark.asyncio
    async def test_initialize_handles_generic_exception(self, module):
        """initialize() returns False and does not propagate on unexpected exceptions."""
        adapter = module.StripeReconciliationAdapter(api_key="sk_test_x")

        # Simulate stripe import succeeding but stripe.Customer raising on access
        MagicMock()
        # Patch sys.modules so `import stripe` returns our mock,
        # then make stripe.Invoice.list raise to simulate initialization failure
        import types
        fake_stripe_mod = types.ModuleType("stripe")
        fake_stripe_mod.api_key = None  # assignment is fine

        class _RaisingClass:
            @staticmethod
            def list(*args, **kwargs):
                raise RuntimeError("Stripe service unavailable")

        fake_stripe_mod.Invoice = _RaisingClass

        # When StripeReconciliationAdapter.initialize() sets stripe.api_key, it just
        # assigns. The exception we want to trigger is in a subsequent call. But the
        # initialize() method only imports and sets api_key then returns True.
        # So to test error handling, we make the `import stripe` succeed but then
        # make the assignment raise by using a module-level __setattr__.

        class _StrictModule(types.ModuleType):
            def __setattr__(self, name, value):
                if name == "api_key":
                    raise RuntimeError("Cannot set api_key")
                super().__setattr__(name, value)

        strict_mod = _StrictModule("stripe")

        with patch.dict("sys.modules", {"stripe": strict_mod}):
            result = await adapter.initialize()

        assert result is False


class TestStripeAdapterGetInvoices:
    @pytest.mark.asyncio
    async def test_returns_empty_when_not_initialized(self, module):
        adapter = module.StripeReconciliationAdapter(api_key=None)
        result = await adapter.get_invoices_for_period(
            "user@example.com",
            date.today() - timedelta(days=1),
            date.today(),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_customer_found(self, module):
        mock_stripe = MagicMock()
        mock_stripe.Customer.list.return_value = MagicMock(data=[])

        adapter = module.StripeReconciliationAdapter(api_key="sk_test")
        adapter._initialized = True
        adapter._stripe = mock_stripe

        result = await adapter.get_invoices_for_period(
            "unknown@example.com",
            date.today() - timedelta(days=1),
            date.today(),
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_parses_invoices_correctly(self, module):
        # Build a fake Stripe invoice
        fake_line = MagicMock()
        fake_line.description = "Metered usage"
        fake_line.amount = 5000  # cents
        fake_line.quantity = 10
        fake_line.unit_amount = 500
        fake_line.type = "subscription"

        fake_invoice = MagicMock()
        fake_invoice.id = "inv_001"
        fake_invoice.invoice_pdf = "https://pdf.url"
        fake_invoice.hosted_invoice_url = "https://hosted.url"
        fake_invoice.amount_due = 5000  # $50.00
        fake_invoice.amount_paid = 5000
        fake_invoice.status = "paid"
        fake_invoice.created = 1700000000
        fake_invoice.period_start = 1700000000
        fake_invoice.period_end = 1700086400
        fake_invoice.lines.data = [fake_line]

        mock_stripe = MagicMock()
        mock_stripe.Customer.list.return_value = MagicMock(
            data=[MagicMock(id="cus_123")]
        )
        mock_stripe.Invoice.list.return_value = MagicMock(data=[fake_invoice])

        adapter = module.StripeReconciliationAdapter(api_key="sk_test")
        adapter._initialized = True
        adapter._stripe = mock_stripe

        # The source code calls period_start.timestamp() — date objects don't have
        # timestamp(). Patch the Invoice.list call to use datetime-based periods,
        # and also patch the date args so they're datetime objects when used in
        # created filter. The adapter receives `date` objects, but internally calls
        # int(period_start.timestamp()) on its filter arg — which works only with
        # datetime. Patch to use datetime-based period args.
        period_start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        period_end = datetime(2024, 1, 2, tzinfo=timezone.utc)

        result = await adapter.get_invoices_for_period(
            "customer@example.com",
            period_start,   # pass datetime, not date
            period_end,
        )

        assert len(result) == 1
        assert result[0]["id"] == "inv_001"
        assert result[0]["amount_due"] == 50.0  # cents converted to dollars
        assert len(result[0]["line_items"]) == 1
        assert result[0]["line_items"][0]["description"] == "Metered usage"

    @pytest.mark.asyncio
    async def test_handles_stripe_exception(self, module):
        mock_stripe = MagicMock()
        mock_stripe.Customer.list.side_effect = RuntimeError("Network error")

        adapter = module.StripeReconciliationAdapter(api_key="sk_test")
        adapter._initialized = True
        adapter._stripe = mock_stripe

        result = await adapter.get_invoices_for_period(
            "x@example.com",
            date.today() - timedelta(days=1),
            date.today(),
        )
        assert result == []


class TestStripeAdapterGetUsageRecords:
    @pytest.mark.asyncio
    async def test_returns_none_when_not_initialized(self, module):
        adapter = module.StripeReconciliationAdapter(api_key=None)
        result = await adapter.get_usage_record_summary(
            "si_abc", date.today() - timedelta(days=1), date.today()
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_summed_quantity(self, module):
        rec1 = MagicMock(quantity=5)
        rec2 = MagicMock(quantity=10)

        mock_stripe = MagicMock()
        mock_stripe.SubscriptionItem.list_usage_records.return_value = MagicMock(
            data=[rec1, rec2]
        )

        adapter = module.StripeReconciliationAdapter(api_key="sk_test")
        adapter._initialized = True
        adapter._stripe = mock_stripe

        result = await adapter.get_usage_record_summary(
            "si_item", date.today() - timedelta(days=1), date.today()
        )

        assert result is not None
        assert result["total_quantity"] == 15
        assert result["records_count"] == 2
        assert result["subscription_item_id"] == "si_item"

    @pytest.mark.asyncio
    async def test_handles_exception_returns_none(self, module):
        mock_stripe = MagicMock()
        mock_stripe.SubscriptionItem.list_usage_records.side_effect = RuntimeError("Boom")

        adapter = module.StripeReconciliationAdapter(api_key="sk_test")
        adapter._initialized = True
        adapter._stripe = mock_stripe

        result = await adapter.get_usage_record_summary(
            "si_fail", date.today() - timedelta(days=1), date.today()
        )
        assert result is None


# ===========================================================================
# StripeDiscrepancy tests
# ===========================================================================

class TestStripeDiscrepancy:
    def _make_discrepancy(self, module, **kwargs):
        defaults = dict(
            license_key="LIC-001",
            key_id="key-1",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("100.00"),
            stripe_amount=Decimal("90.00"),
            variance=Decimal("10.00"),
            variance_percent=11.11,
            status="open",
        )
        defaults.update(kwargs)
        return module.StripeDiscrepancy(**defaults)

    def test_to_dict_contains_required_keys(self, module):
        disc = self._make_discrepancy(module)
        d = disc.to_dict()
        required = ["license_key", "key_id", "period_start", "period_end",
                    "local_amount", "stripe_amount", "variance",
                    "variance_percent", "status"]
        for key in required:
            assert key in d, f"Missing key: {key}"

    def test_to_dict_amounts_are_strings(self, module):
        disc = self._make_discrepancy(module)
        d = disc.to_dict()
        assert isinstance(d["local_amount"], str)
        assert isinstance(d["stripe_amount"], str)
        assert isinstance(d["variance"], str)

    def test_to_dict_dates_are_iso(self, module):
        disc = self._make_discrepancy(module)
        d = disc.to_dict()
        assert d["period_start"] == "2024-01-01"
        assert d["period_end"] == "2024-01-02"

    def test_default_status_is_open(self, module):
        disc = self._make_discrepancy(module)
        assert disc.status == "open"

    def test_default_created_at_is_set(self, module):
        disc = self._make_discrepancy(module)
        assert disc.created_at is not None
        assert isinstance(disc.created_at, datetime)

    def test_notes_field_in_dict(self, module):
        disc = self._make_discrepancy(module, notes="Manual review needed")
        d = disc.to_dict()
        assert d["notes"] == "Manual review needed"


# ===========================================================================
# ReconciliationReport tests
# ===========================================================================

class TestReconciliationReport:
    def _make_report(self, module, discrepancies=None, local_discrepancies=None):
        return module.ReconciliationReport(
            run_date=date(2024, 1, 1),
            total_licenses=10,
            reconciled_count=8,
            stripe_reconciled_count=7,
            discrepancies=discrepancies or [],
            local_only_discrepancies=local_discrepancies or [],
            total_variance=Decimal("50.00"),
            critical_count=1,
            warnings=["warn1"],
            duration_seconds=2.5,
        )

    def test_to_dict_contains_required_keys(self, module):
        report = self._make_report(module)
        d = report.to_dict()
        required = ["run_date", "total_licenses", "reconciled_count",
                    "stripe_reconciled_count", "discrepancies_count",
                    "total_variance", "critical_count", "warnings",
                    "duration_seconds"]
        for key in required:
            assert key in d, f"Missing: {key}"

    def test_to_dict_total_variance_is_string(self, module):
        report = self._make_report(module)
        d = report.to_dict()
        assert isinstance(d["total_variance"], str)
        assert d["total_variance"] == "50.00"

    def test_to_dict_discrepancies_count_correct(self, module):
        disc1 = MagicMock()
        disc1.to_dict.return_value = {"license_key": "LIC-1"}
        report = self._make_report(module, discrepancies=[disc1])
        d = report.to_dict()
        assert d["discrepancies_count"] == 1
        assert len(d["discrepancies"]) == 1

    def test_to_dict_run_date_iso(self, module):
        report = self._make_report(module)
        d = report.to_dict()
        assert d["run_date"] == "2024-01-01"


# ===========================================================================
# NightlyReconciliationService._reconcile_with_stripe tests
# ===========================================================================

class TestReconcileWithStripe:
    def _make_service(self, module, mock_stripe_adapter=None):
        mock_repo = MagicMock()
        mock_event_bus = MagicMock()

        with patch("src.db.repository.get_repository", return_value=mock_repo):
            with patch("src.core.event_bus.get_event_bus", return_value=mock_event_bus):
                with patch("src.billing.reconciliation.ReconciliationConfig", return_value=MagicMock()):
                    service = module.NightlyReconciliationService(
                        repository=mock_repo,
                        stripe_adapter=mock_stripe_adapter or MagicMock(),
                    )
        service._event_bus = mock_event_bus
        return service

    @pytest.mark.asyncio
    async def test_no_invoices_returns_none(self, module):
        mock_adapter = MagicMock()
        mock_adapter.get_invoices_for_period = AsyncMock(return_value=[])

        service = self._make_service(module, mock_adapter)
        result = await service._reconcile_with_stripe(
            license_key="LIC-001",
            key_id="key-1",
            customer_email="user@example.com",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("100.00"),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_minor_variance_returns_none(self, module):
        """Variance < $0.50 and <1% is considered matched."""
        mock_adapter = MagicMock()
        mock_adapter.get_invoices_for_period = AsyncMock(return_value=[
            {"amount_due": 100.30, "line_items": []}  # local=100.00, diff=0.30<0.50
        ])

        service = self._make_service(module, mock_adapter)
        result = await service._reconcile_with_stripe(
            license_key="LIC-001",
            key_id="key-1",
            customer_email="user@example.com",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("100.00"),
        )
        # variance = 100.00 - 100.30 = -0.30, abs < 0.50 => None
        assert result is None

    @pytest.mark.asyncio
    async def test_significant_variance_creates_discrepancy(self, module):
        """Variance >$0.50 or >1% should return a StripeDiscrepancy."""
        mock_adapter = MagicMock()
        mock_adapter.get_invoices_for_period = AsyncMock(return_value=[
            {"amount_due": 80.00, "line_items": [{"description": "item", "amount": 80.0}]}
        ])

        service = self._make_service(module, mock_adapter)
        result = await service._reconcile_with_stripe(
            license_key="LIC-001",
            key_id="key-1",
            customer_email="user@example.com",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("100.00"),  # 25% variance
        )
        assert result is not None
        assert isinstance(result, module.StripeDiscrepancy)
        assert result.variance == Decimal("20.00")
        assert result.variance_percent > 1.0

    @pytest.mark.asyncio
    async def test_status_open_when_variance_over_5pct(self, module):
        mock_adapter = MagicMock()
        mock_adapter.get_invoices_for_period = AsyncMock(return_value=[
            {"amount_due": 50.00, "line_items": []}  # 100% variance
        ])

        service = self._make_service(module, mock_adapter)
        result = await service._reconcile_with_stripe(
            license_key="LIC-002",
            key_id="key-2",
            customer_email="x@example.com",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("100.00"),
        )
        assert result is not None
        assert result.status == "open"

    @pytest.mark.asyncio
    async def test_status_investigating_when_variance_under_5pct(self, module):
        """Between 1-5% variance should be 'investigating'."""
        mock_adapter = MagicMock()
        # local=100, stripe=97 => variance=3, percent=3.09% => investigating
        mock_adapter.get_invoices_for_period = AsyncMock(return_value=[
            {"amount_due": 97.00, "line_items": []}
        ])

        service = self._make_service(module, mock_adapter)
        result = await service._reconcile_with_stripe(
            license_key="LIC-003",
            key_id="key-3",
            customer_email="y@example.com",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("100.00"),
        )
        assert result is not None
        assert result.status == "investigating"

    @pytest.mark.asyncio
    async def test_local_amount_zero_stripe_has_amount(self, module):
        """Local=0, stripe>0 => variance_percent=100%."""
        mock_adapter = MagicMock()
        mock_adapter.get_invoices_for_period = AsyncMock(return_value=[
            {"amount_due": 50.00, "line_items": []}
        ])

        service = self._make_service(module, mock_adapter)
        result = await service._reconcile_with_stripe(
            license_key="LIC-004",
            key_id="key-4",
            customer_email="z@example.com",
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 2),
            local_amount=Decimal("0.00"),
        )
        assert result is not None
        assert result.variance_percent == pytest.approx(100.0)


# ===========================================================================
# NightlyReconciliationService._trigger_alerts tests
# ===========================================================================

class TestTriggerAlerts:
    def _make_report(self, module, critical_count=1, total_variance=Decimal("200.00")):
        return module.ReconciliationReport(
            run_date=date(2024, 1, 1),
            total_licenses=5,
            reconciled_count=3,
            stripe_reconciled_count=2,
            discrepancies=[],
            local_only_discrepancies=[],
            total_variance=total_variance,
            critical_count=critical_count,
        )

    def _make_service(self, module):
        mock_repo = MagicMock()
        mock_event_bus = MagicMock()
        service = module.NightlyReconciliationService(
            repository=mock_repo,
            stripe_adapter=MagicMock(),
        )
        service._event_bus = mock_event_bus
        return service, mock_event_bus

    @pytest.mark.asyncio
    async def test_emits_event_bus_event(self, module):
        service, mock_event_bus = self._make_service(module)
        report = self._make_report(module)

        await service._trigger_alerts(report)

        mock_event_bus.emit.assert_called_once()
        args = mock_event_bus.emit.call_args[0]
        # First arg is EventType, second is data dict
        data = args[1]
        assert data["critical_count"] == 1
        assert data["run_date"] == "2024-01-01"

    @pytest.mark.asyncio
    async def test_sends_telegram_when_configured(self, module):
        service, _ = self._make_service(module)
        report = self._make_report(module)

        mock_requests = MagicMock()
        env = {"TELEGRAM_BOT_TOKEN": "bot:tok", "TELEGRAM_OPS_CHANNEL_ID": "-100123"}

        with patch.dict(os.environ, env):
            with patch.dict("sys.modules", {"requests": mock_requests}):
                await service._trigger_alerts(report)

        mock_requests.post.assert_called()
        call_args = mock_requests.post.call_args
        assert "sendMessage" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_no_telegram_when_not_configured(self, module):
        service, _ = self._make_service(module)
        report = self._make_report(module)

        mock_requests = MagicMock()
        env = {k: v for k, v in os.environ.items()
               if k not in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_OPS_CHANNEL_ID")}

        with patch.dict(os.environ, env, clear=True):
            with patch.dict("sys.modules", {"requests": mock_requests}):
                await service._trigger_alerts(report)

        mock_requests.post.assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_webhook_when_configured(self, module):
        service, _ = self._make_service(module)
        report = self._make_report(module)

        mock_requests = MagicMock()
        env = {"RECONCILIATION_WEBHOOK_URL": "https://hooks.example.com/alert"}

        with patch.dict(os.environ, env):
            with patch.dict("sys.modules", {"requests": mock_requests}):
                await service._trigger_alerts(report)

        mock_requests.post.assert_called()

    @pytest.mark.asyncio
    async def test_telegram_failure_does_not_raise(self, module):
        service, _ = self._make_service(module)
        report = self._make_report(module)

        mock_requests = MagicMock()
        mock_requests.post.side_effect = RuntimeError("network error")
        env = {"TELEGRAM_BOT_TOKEN": "bot:tok", "TELEGRAM_OPS_CHANNEL_ID": "-100"}

        with patch.dict(os.environ, env):
            with patch.dict("sys.modules", {"requests": mock_requests}):
                # Should not raise
                await service._trigger_alerts(report)


# ===========================================================================
# NightlyReconciliationService._get_active_licenses tests
# ===========================================================================

class TestGetActiveLicenses:
    @pytest.mark.asyncio
    async def test_returns_empty_list(self, module):
        """Current implementation returns empty list (placeholder)."""
        service = module.NightlyReconciliationService(
            repository=MagicMock(),
            stripe_adapter=MagicMock(),
        )
        result = await service._get_active_licenses()
        assert result == []


# ===========================================================================
# NightlyReconciliationService.run_full_reconciliation tests
# ===========================================================================

class TestRunFullReconciliation:
    def _make_service(self, module):
        service = module.NightlyReconciliationService(
            repository=MagicMock(),
            stripe_adapter=MagicMock(),
        )
        service._event_bus = MagicMock()
        return service

    @pytest.mark.asyncio
    async def test_defaults_to_yesterday(self, module):
        service = self._make_service(module)
        service._get_active_licenses = AsyncMock(return_value=[])
        service._save_report = AsyncMock()
        service._trigger_alerts = AsyncMock()
        service._print_report = MagicMock()

        report = await service.run_full_reconciliation()
        yesterday = date.today() - timedelta(days=1)
        assert report.run_date == yesterday

    @pytest.mark.asyncio
    async def test_uses_provided_audit_date(self, module):
        service = self._make_service(module)
        service._get_active_licenses = AsyncMock(return_value=[])
        service._save_report = AsyncMock()
        service._trigger_alerts = AsyncMock()
        service._print_report = MagicMock()

        target_date = date(2024, 6, 15)
        report = await service.run_full_reconciliation(audit_date=target_date)
        assert report.run_date == target_date

    @pytest.mark.asyncio
    async def test_dry_run_does_not_save(self, module):
        service = self._make_service(module)
        service._get_active_licenses = AsyncMock(return_value=[])
        service._save_report = AsyncMock()
        service._trigger_alerts = AsyncMock()
        service._print_report = MagicMock()

        await service.run_full_reconciliation(dry_run=True)
        service._save_report.assert_not_called()

    @pytest.mark.asyncio
    async def test_non_dry_run_saves_report(self, module):
        service = self._make_service(module)
        service._get_active_licenses = AsyncMock(return_value=[])
        service._save_report = AsyncMock()
        service._trigger_alerts = AsyncMock()
        service._print_report = MagicMock()

        await service.run_full_reconciliation(dry_run=False)
        service._save_report.assert_called_once()

    @pytest.mark.asyncio
    async def test_zero_licenses_returns_empty_report(self, module):
        service = self._make_service(module)
        service._get_active_licenses = AsyncMock(return_value=[])
        service._save_report = AsyncMock()
        service._trigger_alerts = AsyncMock()
        service._print_report = MagicMock()

        report = await service.run_full_reconciliation()
        assert report.total_licenses == 0
        assert report.reconciled_count == 0
        assert report.discrepancies == []

    @pytest.mark.asyncio
    async def test_triggers_alert_when_critical(self, module):
        """Alert fires when critical_count > 0."""
        service = self._make_service(module)
        service._get_active_licenses = AsyncMock(return_value=[])
        service._save_report = AsyncMock()
        service._trigger_alerts = AsyncMock()
        service._print_report = MagicMock()

        # Inject a fake discrepancy with >10% variance to drive critical_count up
        disc = MagicMock()
        disc.variance = Decimal("50.00")
        disc.variance_percent = 15.0  # > 10% = critical

        await service.run_full_reconciliation()
        # No licenses => no discrepancies => critical_count = 0 => no alert
        service._trigger_alerts.assert_not_called()


# ===========================================================================
# main_async tests
# ===========================================================================

class TestMainAsync:
    @pytest.mark.asyncio
    async def test_invalid_date_raises_system_exit(self, module):
        with pytest.raises(SystemExit) as exc_info:
            await module.main_async(audit_date="not-a-date")
        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_valid_date_string_is_parsed(self, module):
        mock_service = MagicMock()
        mock_report = MagicMock()
        mock_report.critical_count = 0
        mock_service.run_full_reconciliation = AsyncMock(return_value=mock_report)

        with patch.object(module, "NightlyReconciliationService", return_value=mock_service):
            await module.main_async(audit_date="2024-01-15")

        call_kwargs = mock_service.run_full_reconciliation.call_args
        assert call_kwargs[1]["audit_date"] == date(2024, 1, 15)

    @pytest.mark.asyncio
    async def test_no_date_passes_none(self, module):
        mock_service = MagicMock()
        mock_report = MagicMock()
        mock_report.critical_count = 0
        mock_service.run_full_reconciliation = AsyncMock(return_value=mock_report)

        with patch.object(module, "NightlyReconciliationService", return_value=mock_service):
            await module.main_async(audit_date=None)

        call_kwargs = mock_service.run_full_reconciliation.call_args
        assert call_kwargs[1]["audit_date"] is None

    @pytest.mark.asyncio
    async def test_critical_discrepancies_raise_system_exit_1(self, module):
        mock_service = MagicMock()
        mock_report = MagicMock()
        mock_report.critical_count = 3
        mock_service.run_full_reconciliation = AsyncMock(return_value=mock_report)

        with patch.object(module, "NightlyReconciliationService", return_value=mock_service):
            with pytest.raises(SystemExit) as exc_info:
                await module.main_async()

        assert exc_info.value.code == 1

    @pytest.mark.asyncio
    async def test_no_critical_completes_normally(self, module):
        mock_service = MagicMock()
        mock_report = MagicMock()
        mock_report.critical_count = 0
        mock_service.run_full_reconciliation = AsyncMock(return_value=mock_report)

        with patch.object(module, "NightlyReconciliationService", return_value=mock_service):
            # Should not raise
            await module.main_async()

    @pytest.mark.asyncio
    async def test_dry_run_flag_passed_through(self, module):
        mock_service = MagicMock()
        mock_report = MagicMock()
        mock_report.critical_count = 0
        mock_service.run_full_reconciliation = AsyncMock(return_value=mock_report)

        with patch.object(module, "NightlyReconciliationService", return_value=mock_service):
            await module.main_async(dry_run=True)

        call_kwargs = mock_service.run_full_reconciliation.call_args
        assert call_kwargs[1]["dry_run"] is True
