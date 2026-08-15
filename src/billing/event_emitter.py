"""Backward-compat shim — logic moved to src/raas/billing_event_emitter.py"""
from src.raas.billing_event_emitter import (  # noqa: F401
    BillingEventEmitter,
    get_emitter,
    reset_emitter,
)

__all__ = [
    "BillingEventEmitter",
    "get_emitter",
    "reset_emitter",
]
