# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Billing and batch idempotency operations for LicenseRepository."""

import json
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Optional

from src.db.database import DatabaseConnection


class LicenseBillingRepositoryMixin:
    """Mixin providing rate card, billing period, line item, and audit queries."""

    _db: DatabaseConnection

    async def get_rate_card(
        self, plan_tier: str, event_type: str, model_name: Optional[str] = None
    ) -> Optional[Dict]:
        """Get active rate card for plan tier and event type."""
        query = """
            SELECT * FROM rate_cards
            WHERE plan_tier = $1 AND event_type = $2
              AND (model_name = $3 OR (model_name IS NULL AND $3 IS NULL))
              AND is_active = TRUE AND valid_from <= CURRENT_DATE
              AND (valid_to IS NULL OR valid_to > CURRENT_DATE)
            ORDER BY valid_from DESC LIMIT 1
        """
        return await self._db.fetch_one(query, (plan_tier, event_type, model_name))

    async def get_usage_events(
        self, license_key: str, start_date: datetime, end_date: datetime
    ) -> list[Dict]:
        """Get usage events for a license within date range."""
        query = """
            SELECT * FROM usage_events_staging
            WHERE license_key = $1 AND timestamp >= $2 AND timestamp <= $3
            ORDER BY timestamp ASC
        """
        rows = await self._db.fetch_all(query, (license_key, start_date, end_date))
        return [dict(row) for row in rows] if rows else []

    async def create_billing_period(
        self, license_key: str, key_id: str, start_date: date, end_date: date,
        plan_tier: str, base_fee: Decimal = Decimal(0),
    ) -> Dict:
        """Create a new billing period."""
        query = (
            "INSERT INTO billing_periods (license_key, key_id, start_date, end_date, status, plan_tier, base_fee, total_amount) "
            "VALUES ($1, $2, $3, $4, 'open', $5, $6, $6) RETURNING *"
        )
        result = await self._db.fetch_one(query, (license_key, key_id, start_date, end_date, plan_tier, base_fee))
        return dict(result) if result else {}

    async def get_billing_period(
        self, license_key: str, start_date: date, end_date: date
    ) -> Optional[Dict]:
        """Get billing period by dates."""
        return await self._db.fetch_one(
            "SELECT * FROM billing_periods WHERE license_key = $1 AND start_date = $2 AND end_date = $3",
            (license_key, start_date, end_date),
        )

    async def create_billing_record(
        self, billing_period_id: str, license_key: str, key_id: str, record_type: str,
        amount: Decimal, description: Optional[str] = None, metadata: Optional[Dict] = None,
    ) -> Dict:
        """Create a new billing record."""
        query = (
            "INSERT INTO billing_records (billing_period_id, license_key, key_id, record_type, amount, description, metadata) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *"
        )
        result = await self._db.fetch_one(
            query, (billing_period_id, license_key, key_id, record_type, str(amount), description, metadata or {}),
        )
        return dict(result) if result else {}

    async def create_billing_line_item(
        self, billing_record_id: str, event_type: str, model_name: Optional[str],
        quantity: Decimal, unit: str, unit_price: Decimal, subtotal: Decimal,
        timestamp: datetime, usage_batch_id: Optional[str] = None, metadata: Optional[Dict] = None,
    ) -> Dict:
        """Create a billing line item."""
        query = (
            "INSERT INTO billing_line_items (billing_record_id, event_type, model_name, quantity, unit, "
            "unit_price, subtotal, final_amount, timestamp, usage_batch_id, metadata) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $7, $8, $9, $10) RETURNING *"
        )
        result = await self._db.fetch_one(query, (
            billing_record_id, event_type, model_name, str(quantity), unit,
            str(unit_price), str(subtotal), timestamp, usage_batch_id, metadata or {},
        ))
        return dict(result) if result else {}

    async def check_batch_idempotency(self, batch_id: str) -> Optional[Dict]:
        """Check if a batch has been processed."""
        return await self._db.fetch_one(
            "SELECT * FROM batch_idempotency WHERE batch_id = $1 AND status != 'failed'", (batch_id,)
        )

    async def create_batch_idempotency(
        self, batch_id: str, license_key: str, key_id: str, events_count: int
    ) -> Dict:
        """Create a batch idempotency record."""
        query = """
            INSERT INTO batch_idempotency (batch_id, license_key, key_id, events_count, status)
            VALUES ($1, $2, $3, $4, 'pending') RETURNING *
        """
        result = await self._db.fetch_one(query, (batch_id, license_key, key_id, events_count))
        return dict(result) if result else {}

    async def update_batch_idempotency(
        self,
        batch_id: str,
        status: str,
        billing_record_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update batch idempotency record."""
        if status == "completed":
            await self._db.execute(
                "UPDATE batch_idempotency SET status = 'completed', processed_at = NOW(), billing_record_id = $2 WHERE batch_id = $1",
                (batch_id, billing_record_id),
            )
        elif status == "failed":
            await self._db.execute(
                "UPDATE batch_idempotency SET status = 'failed', error_message = $2 WHERE batch_id = $1",
                (batch_id, error_message),
            )
        else:
            await self._db.execute(
                "UPDATE batch_idempotency SET status = $2 WHERE batch_id = $1", (batch_id, status)
            )
        return True

    async def create_reconciliation_audit(
        self,
        audit_date: date,
        license_key: str,
        key_id: str,
        expected_amount: Decimal,
        actual_amount: Decimal,
        variance: Decimal,
        discrepancies: Optional[list] = None,
        status: str = "pending",
        notes: Optional[str] = None,
    ) -> Dict:
        """Create a reconciliation audit record."""
        query = """
            INSERT INTO reconciliation_audits (
                audit_date, license_key, key_id, expected_amount,
                actual_amount, variance, discrepancies, status, notes
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (audit_date, license_key) DO UPDATE
            SET expected_amount = $4, actual_amount = $5, variance = $6,
                discrepancies = $7, status = $8, notes = $9, updated_at = NOW()
            RETURNING *
        """
        result = await self._db.fetch_one(query, (
            audit_date, license_key, key_id, str(expected_amount),
            str(actual_amount), str(variance),
            json.dumps(discrepancies or []), status, notes
        ))
        return dict(result) if result else {}
