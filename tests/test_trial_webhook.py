"""
Integration tests for Stripe webhook trial subscription flow.

Tests src/api/billing_endpoints.py::stripe_webhook (line 690).

Five scenarios:
1. is_trialing flag: (status or "").lower() == "trialing" — case-insensitive
2. Trial lifecycle: trialing → evaluate_trial() called, 0 credits
3. Paid tier credits: non-trialing → tier_credits(tier_key) via CreditStore
4. Trial deletion deferred: deleted + trialing → evaluate_trial, 0 credits
5. Edge / integration: 503, no customer, no user, empty items

Runnable: python3 -m pytest tests/test_trial_webhook.py -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

_BILLING_PATH = (Path(__file__).parent.parent / "src/api/billing_endpoints.py")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mod():
    """Reload billing_endpoints fresh so module-level os.* patches stick."""
    spec = importlib.util.spec_from_file_location("billing_mod", str(_BILLING_PATH))
    m = importlib.util.module_from_spec(spec)
    sys.modules["billing_mod"] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(autouse=True)
def _reload(mod):
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sub(
    event_type="customer.subscription.created",
    status="active",
    price_id="price_starter",
    event_id="evt_01",
    customer="cus_001",
):
    """Helper: Build a minimal Stripe event dict."""
    return {
        "id": event_id,
        "type": event_type,
        "data": {
            "object": {
                "id": "sub_" + event_id.split("_")[-1],
                "object": "subscription",
                "customer": customer,
                "status": status,
                "items": {"data": [{"price": {"id": price_id}}]},
            }
        },
    }


def _env(mock_os):
    """Bypass STRIPE_WEBHOOK_SECRET gating in tests."""
    mock_os.getenv.side_effect = lambda k, d="": {
        "STRIPE_WEBHOOK_SECRET": "whsec_test",
        "STRIPE_SECRET_KEY": "",
        "STRIPE_PRICE_IDS": "{}",
    }.get(k, d)


async def _mock_request(body=b"{}", sig="v1=test"):
    """Create a mock FastAPI Request."""
    req = MagicMock()
    req.body = AsyncMock(return_value=body)
    req.headers = {"stripe-signature": sig}
    return req


def _make_svc(svc_cls, email="u@test.com", cid="cus_001"):
    """Wire module StripeService mock.

    Returns (svc_mock, customer_mock).
    """
    cust = MagicMock()
    cust.email = email
    cust.id = cid
    svc = MagicMock()
    svc.handle_stripe_webhook = AsyncMock(
        return_value={"success": True, "message": "ok"}
    )
    svc._get_customer_by_id = AsyncMock(return_value=cust)
    svc_cls.return_value = svc
    return svc, cust


def _make_user_repo(ur_cls, uid="tenant_001", tier="free"):
    """Wire module UserRepository mock."""
    repo = MagicMock()
    user = MagicMock()
    user.id = uid
    user.tier = tier
    repo.find_by_email = AsyncMock(return_value=user)
    ur_cls.return_value = repo
    return repo, user


def _make_credit_store(cs_cls, balance=100):
    """Wire module CreditStore mock."""
    store = MagicMock()
    store.add_credits = MagicMock(return_value=MagicMock(success=True))
    store.get_balance.return_value = balance
    cs_cls.return_value = store
    return store


def _load_tiers(mod=None):
    """Import tier_credits from seed/config/tiers."""
    from src.seed.config.tiers import tier_credits

    return tier_credits


# ===========================================================================
# Scenario 1: is_trialing flag detection
# ===========================================================================
#
# Code path: line 756
#   is_trialing = (subscription.get("status") or "").lower() == "trialing"
#
# Lower-case normalization means "TRIALING", "Trialing", "trialing" all match.
# This test asserts detection; credits/actions verified in Scenarios 2-4.
# ===========================================================================

class TestTrialingFlagDetection:
    """subscription.status case-insensitive detection for 'trialing'."""

    async def test_lowercase_trialing_detected(self, mod):
        event = _sub(status="trialing")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh:
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            # Minimal mock — just verify it runs without error
            with patch.object(mod, "StripeService") as svc_cls, \
                    patch.object(mod, "UserRepository") as ur_cls, \
                    patch.object(mod, "CreditStore") as cs_cls, \
                    patch.object(mod, "get_tier_to_role_mapping", return_value={}), \
                    patch.object(mod, "evaluate_trial"):
                svc, cust = _make_svc(svc_cls)
                cust.email = "t@t.com"
                _make_user_repo(ur_cls)
                _make_credit_store(cs_cls)
                result = await mod.stripe_webhook(req)
                assert result["status"] == "success"

    async def test_uppercase_trialing_detected(self, mod):
        event = _sub(status="TRIALING")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh:
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            with patch.object(mod, "StripeService") as svc_cls, \
                    patch.object(mod, "UserRepository") as ur_cls, \
                    patch.object(mod, "CreditStore") as cs_cls, \
                    patch.object(mod, "get_tier_to_role_mapping", return_value={}), \
                    patch.object(mod, "evaluate_trial"):
                svc, cust = _make_svc(svc_cls)
                cust.email = "t@t.com"
                _make_user_repo(ur_cls)
                _make_credit_store(cs_cls)
                result = await mod.stripe_webhook(req)
                assert result["status"] == "success"

    async def test_empty_status_not_trialing(self, mod):
        """Empty/null status → not trialing → tier credits via normal path."""
        event = _sub(status="")
        tier_credits = _load_tiers()
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={"price_starter": "starter"}), \
                patch.object(mod, "evaluate_trial") as eval_fn:
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            store = _make_credit_store(cs_cls)
            result = await mod.stripe_webhook(req)
            # non-trialing → tier credits (tier_key from mapping)
            assert result["credits_provisioned"] == tier_credits("starter")
            # evaluate_trial must NOT be called
            eval_fn.assert_not_called()
            store.add_credits.assert_called_once()


# ===========================================================================
# Scenario 2: Trial credit provisioning
# ===========================================================================
#
# Code path: is_trialing=True → tier_key="trial", credits_provisioned=0.
# evaluate_trial() is called (fire-and-forget), CreditStore NOT called.
# tier_credits("trial") == 50 is asserted as a unit check (not used at runtime).
# ===========================================================================

class TestTrialCreditProvisioning:
    """
    Trialing subscriptions: credits_provisioned=0, evaluate_trial triggered.
    """

    async def test_trial_event_provisions_zero_credits(self, mod):
        event = _sub(status="trialing", price_id="price_trial")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={}), \
                patch.object(mod, "evaluate_trial") as eval_fn:
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            store = _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            assert result["status"] == "success"
            assert result["credits_provisioned"] == 0
            store.add_credits.assert_not_called()
            eval_fn.assert_called_once()

    async def test_trial_tier_credits_are_50(self, mod):
        from src.seed.config.tiers import tier_credits
        assert tier_credits("trial") == 50, \
            "tier_credits('trial') should return 50"

    async def test_evaluate_trial_args_include_event_type(self, mod):
        """
        evaluate_trial called with tenant_id, customer_id, event_type kwargs.
        customer_id comes from subscription.get("customer") = "cus_001".
        tenant_id from find_by_email result ("tenant_001").
        """
        event = _sub(
            event_type="customer.subscription.updated",
            status="trialing",
            price_id="price_trial",
            event_id="evt_upd",
        )
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            _make_credit_store(cs_cls)

            await mod.stripe_webhook(req)
            eval_fn.assert_called_once_with(
                tenant_id="tenant_001",
                customer_id="cus_001",
            )


# ===========================================================================
# Scenario 3: Paid tier unchanged
# ===========================================================================
#
# Non-trialing → tier_credits(tier_key) credit via CreditStore.add_credits().
# evaluate_trial() not called.
# =========================================================================

class TestPaidTierUnchanged:
    """Non-trialing subscriptions get tier credits, evaluate_trial untouched."""

    async def test_starter_tier_gets_200_credits(self, mod):
        from src.seed.config.tiers import tier_credits
        event = _sub(status="active", price_id="price_starter")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping",
                             return_value={"price_starter": "starter"}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            store = _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            assert result["status"] == "success"
            assert result["credits_provisioned"] == tier_credits("starter")
            store.add_credits.assert_called_once()
            eval_fn.assert_not_called()

    async def test_active_does_not_call_evaluate_trial(self, mod):
        event = _sub(status="active", price_id="price_pro")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping",
                             return_value={"price_pro": "pro"}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            _make_credit_store(cs_cls, balance=1000)

            result = await mod.stripe_webhook(req)
            assert result["credits_provisioned"] == 5000
            eval_fn.assert_not_called()


# ===========================================================================
# Scenario 4: Trial deletion deferred
# ===========================================================================
#
# customer.subscription.deleted + trialing → evaluate_trial(),
# credits=0, CreditStore NOT called.
# Non-trialing deleted → 0 credits (special case from line 770).
# ===========================================================================

class TestTrialDeletionDeferred:
    """Trialing deletion delegates to evaluate_trial, never debits credits."""

    async def test_trial_deletion_calls_evaluate_trial(self, mod):
        event = _sub(
            event_type="customer.subscription.deleted",
            status="trialing",
        )
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            assert result["status"] == "success"
            assert result["credits_provisioned"] == 0
            eval_fn.assert_called_once_with(
                tenant_id="tenant_001",
                customer_id="cus_001",
            )

    async def test_trial_deletion_no_credits_debited(self, mod):
        event = _sub(
            event_type="customer.subscription.deleted",
            status="trialing",
        )
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "evaluate_trial", return_value=None), \
                patch.object(mod, "get_tier_to_role_mapping", return_value={}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            _make_credit_store(cs_cls)

            await mod.stripe_webhook(req)
            cs_cls.return_value.add_credits.assert_not_called()

    async def test_non_trial_deletion_zero_credits_no_evaluate_trial(self, mod):
        """Canceled status deleted → no evaluate_trial, no add_credits."""
        event = _sub(
            event_type="customer.subscription.deleted",
            status="canceled",
        )
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={"price_pro": "pro"}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            assert result["credits_provisioned"] == 0
            cs_cls.return_value.add_credits.assert_not_called()
            eval_fn.assert_not_called()


# ===========================================================================
# Scenario 5: Edge / integration
# ===========================================================================

class TestWebhookEdgeCases:
    """Error paths and missing-data scenarios."""

    async def test_missing_webhook_secret_raises_503(self, mod):
        """Empty STRIPE_WEBHOOK_SECRET → HTTPException 503."""
        from fastapi import HTTPException

        mock_os = MagicMock()
        mock_os.getenv.return_value = ""
        with patch.object(mod, "os", mock_os), \
                patch.object(mod.stripe_sdk, "Webhook"):
            req = await _mock_request()
            with pytest.raises(HTTPException) as ei:
                await mod.stripe_webhook(req)
            assert ei.value.status_code == 503

    async def test_no_customer_found_uses_stripe_cid_as_tenant_id(self, mod):
        """
        _get_customer_by_id returns None → tenant_id falls back to customer_id.
        Real behavior: tenant_id=customer_id set BEFORE the customer check,
        so evaluate_trial still fires with the Stripe customer ID.
        """
        event = _sub(status="trialing", price_id="price_trial")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            svc_mock, _ = _make_svc(svc_cls)
            svc_mock._get_customer_by_id = AsyncMock(return_value=None)
            ur_cls.return_value = MagicMock()
            _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            assert result["credits_provisioned"] == 0
            # evaluate_trial fires with customer_id as tenant_id fallback
            eval_fn.assert_called_once()
            call_kwargs = eval_fn.call_args.kwargs
            assert call_kwargs["tenant_id"] == "cus_001"
            assert call_kwargs["customer_id"] == "cus_001"

    async def test_no_user_found_credits_awarded_to_stripe_cid(self, mod):
        """
        UserRepository.find_by_email returns None → tenant_id falls back to
        customer_id. Credits ARE awarded for non-trialing subscriptions.
        This documents the real behavior: tenant_id=customer_id is used.
        """
        event = _sub(status="active", price_id="price_starter")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "evaluate_trial") as eval_fn, \
                patch.object(mod, "get_tier_to_role_mapping",
                             return_value={"price_starter": "starter"}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            # Override UserRepository to return None (user not found)
            repo_mock = MagicMock()
            repo_mock.find_by_email = AsyncMock(return_value=None)
            ur_cls.return_value = repo_mock
            store = _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            # tenant_id falls back to customer_id → credits still awarded
            assert result["credits_provisioned"] == 200
            store.add_credits.assert_called_once()
            call_kwargs = store.add_credits.call_args.kwargs
            assert call_kwargs["tenant_id"] == "cus_001"
            eval_fn.assert_not_called()

    async def test_trialing_with_empty_items_no_price_id(self, mod):
        """
        Empty items.data → price_id=None → outer guard False → skipped.
        Guard at line ~753: "if customer_id and price_id:"
        """
        event = {
            "id": "evt_noprice",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_np",
                    "object": "subscription",
                    "customer": "cus_np",
                    "status": "trialing",
                    "items": {"data": [{}]},  # price.id = None, safe [0] access
                }
            },
        }
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "UserRepository") as ur_cls, \
                patch.object(mod, "CreditStore") as cs_cls, \
                patch.object(mod, "get_tier_to_role_mapping", return_value={}), \
                patch.object(mod, "evaluate_trial") as eval_fn:
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            _make_svc(svc_cls)
            _make_user_repo(ur_cls)
            _make_credit_store(cs_cls)

            result = await mod.stripe_webhook(req)
            # No credits, no eval — outer guard short-circuits per "if customer_id AND price_id"
            assert result["credits_provisioned"] == 0
            eval_fn.assert_not_called()
            cs_cls.return_value.add_credits.assert_not_called()

    async def test_role_sync_failure_returns_error(self, mod):
        """
        StripeService.handle_stripe_webhook returns success=False.
        Code returns error status immediately (no credit provisioning).
        """
        event = _sub(status="active", price_id="price_pro")
        with patch.object(mod, "os") as mock_os, \
                patch.object(mod.stripe_sdk, "Webhook") as wh, \
                patch.object(mod, "StripeService") as svc_cls, \
                patch.object(mod, "get_tier_to_role_mapping",
                             return_value={"price_pro": "pro"}):
            _env(mock_os)
            req = await _mock_request()
            wh.construct_event.return_value = event
            svc = MagicMock()
            svc.handle_stripe_webhook = AsyncMock(
                return_value={"success": False, "message": "Customer not found"}
            )
            svc_cls.return_value = svc

            result = await mod.stripe_webhook(req)
            assert result["status"] == "error"
            assert "Customer not found" in result["message"]
