"""
Mekong CLI - Billing System (re-export shim)

All billing logic now lives in src/raas/billing_*.py.
This module re-exports for backward compatibility.
"""

from src.raas.billing_engine import (
    RateCard,
    LineItem,
    BillingResult,
    RateCardResolver,
    BillingEngine,
    get_engine,
    get_rate_resolver,
    reset_engine,
)
from src.raas.billing_proration import (
    ProrationResult,
    OverageCalculation,
    ProrationCalculator,
    OverageTracker,
    get_calculator,
    reset_calculator,
)
from src.raas.billing_idempotency import (
    BatchStatus,
    BatchRecord,
    BatchResult,
    IdempotencyManager,
    get_idempotency_manager,
    reset_idempotency_manager,
)
from src.raas.billing_event_emitter import (
    BillingEventEmitter,
    get_emitter,
    reset_emitter,
)
from src.raas.billing_audit import (
    AuditResult,
    ReconciliationConfig,
    ReconciliationService,
    get_reconciliation_service,
    reset_reconciliation_service,
)

__all__ = [
    "RateCard",
    "LineItem",
    "BillingResult",
    "RateCardResolver",
    "BillingEngine",
    "ProrationResult",
    "OverageCalculation",
    "ProrationCalculator",
    "OverageTracker",
    "BatchStatus",
    "BatchRecord",
    "BatchResult",
    "IdempotencyManager",
    "BillingEventEmitter",
    "AuditResult",
    "ReconciliationConfig",
    "ReconciliationService",
    "get_engine",
    "get_rate_resolver",
    "get_calculator",
    "get_idempotency_manager",
    "get_emitter",
    "get_reconciliation_service",
    "reset_engine",
    "reset_calculator",
    "reset_idempotency_manager",
    "reset_emitter",
    "reset_reconciliation_service",
]
