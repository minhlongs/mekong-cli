"""NOWPayments checkout — create USDT payment links for RaaS subscriptions.

Uses NOWPayments API to generate checkout URLs for subscription tiers.
Accepts USDT TRC20 as primary payment method.

Env vars:
    NOWPAYMENTS_API_KEY — API key from nowpayments.io
    NOWPAYMENTS_IPN_SECRET — IPN webhook secret
    NOWPAYMENTS_PAYOUT_ADDRESS — USDT TRC20 wallet address
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import URLError

logger = logging.getLogger(__name__)

BASE_URL = "https://api.nowpayments.io/v1"
API_KEY = os.getenv("NOWPAYMENTS_API_KEY", "")
PAYOUT_ADDRESS = os.getenv(
    "NOWPAYMENTS_PAYOUT_ADDRESS",
    "TC6FknawxFcgUn1jr8CN455wsSm87hByDQ",
)

# Subscription tiers — price in USD, credits per month
TIERS: dict[str, dict[str, Any]] = {
    "starter":    {"price_usd": 49,  "credits": 200,   "name": "Starter"},
    "pro":        {"price_usd": 149, "credits": 1000,  "name": "Pro"},
    "growth":     {"price_usd": 299, "credits": 3000,  "name": "Growth"},
    "enterprise": {"price_usd": 499, "credits": 10000, "name": "Enterprise"},
}


def _api_request(
    endpoint: str,
    method: str = "GET",
    data: dict | None = None,
) -> dict:
    """Make authenticated request to NOWPayments API."""
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json",
    }
    body = json.dumps(data).encode() if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except URLError as e:
        logger.error(f"NOWPayments API error: {e}")
        raise


def get_estimated_price(
    amount_usd: float,
    currency_to: str = "usdttrc20",
) -> dict:
    """Get estimated price in crypto for a given USD amount."""
    return _api_request(
        f"estimate?amount={amount_usd}&currency_from=usd&currency_to={currency_to}"
    )


def create_payment(
    tier: str,
    order_id: str,
    customer_email: str = "",
    currency: str = "usdttrc20",
) -> dict:
    """Create a one-time payment for a subscription tier.

    Returns dict with payment_id, pay_address, pay_amount, etc.
    """
    tier_config = TIERS.get(tier)
    if not tier_config:
        raise ValueError(f"Unknown tier: {tier}. Options: {list(TIERS)}")

    payload = {
        "price_amount": tier_config["price_usd"],
        "price_currency": "usd",
        "pay_currency": currency,
        "order_id": order_id,
        "order_description": f"OpenClaw {tier_config['name']} — {tier_config['credits']} credits/mo",
        "ipn_callback_url": os.getenv(
            "NOWPAYMENTS_IPN_URL",
            "https://api.agencyos.network/webhooks/nowpayments",
        ),
        "payout_address": PAYOUT_ADDRESS,
    }
    if customer_email:
        payload["customer_email"] = customer_email

    return _api_request("payment", method="POST", data=payload)


def create_invoice(
    tier: str,
    order_id: str,
    customer_email: str = "",
) -> dict:
    """Create an invoice (hosted checkout page) for a subscription tier.

    Returns dict with invoice_url — redirect customer to this URL.
    """
    tier_config = TIERS.get(tier)
    if not tier_config:
        raise ValueError(f"Unknown tier: {tier}. Options: {list(TIERS)}")

    payload = {
        "price_amount": tier_config["price_usd"],
        "price_currency": "usd",
        "order_id": order_id,
        "order_description": f"OpenClaw {tier_config['name']} — {tier_config['credits']} credits/mo",
        "ipn_callback_url": os.getenv(
            "NOWPAYMENTS_IPN_URL",
            "https://api.agencyos.network/webhooks/nowpayments",
        ),
        "success_url": os.getenv(
            "NOWPAYMENTS_SUCCESS_URL",
            "https://sophia.agencyos.network/thank-you",
        ),
        "cancel_url": os.getenv(
            "NOWPAYMENTS_CANCEL_URL",
            "https://sophia.agencyos.network/pricing",
        ),
    }
    if customer_email:
        payload["customer_email"] = customer_email

    return _api_request("invoice", method="POST", data=payload)


def get_payment_status(payment_id: str) -> dict:
    """Check payment status by ID."""
    return _api_request(f"payment/{payment_id}")


def list_payments(limit: int = 10) -> dict:
    """List recent payments."""
    return _api_request(f"payment/?limit={limit}&page=0&sortBy=created_at&orderBy=desc")


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("=== NOWPayments Status ===")
    print(_api_request("status"))
    print("\n=== USDT TRC20 estimate for $49 ===")
    print(get_estimated_price(49))
    print("\n=== Available tiers ===")
    for k, v in TIERS.items():
        print(f"  {k}: ${v['price_usd']}/mo — {v['credits']} credits")
