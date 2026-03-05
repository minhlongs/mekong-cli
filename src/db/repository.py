"""
PostgreSQL Repository Layer — ROIaaS Phase 3

CRUD operations for licenses, usage records, and revocations.
"""

from typing import Optional, Dict, Any
from datetime import datetime, date

from src.db.database import get_database, DatabaseConnection


class LicenseRepository:
    """Repository for license data operations with PostgreSQL."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or get_database()

    # ========== LICENSE CRUD ==========

    async def create_license(
        self,
        license_key: str,
        key_id: str,
        tier: str,
        email: str,
        subscription_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        daily_limit: int = 1000,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Create a new license record."""
        query = """
            INSERT INTO licenses (
                license_key, key_id, tier, email, subscription_id, customer_id,
                status, daily_limit, expires_at, metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, 'active', $7, $8, $9
            ) RETURNING id, created_at
        """
        result = await self._db.fetch_one(query, (
            license_key, key_id, tier, email, subscription_id,
            customer_id, daily_limit, expires_at, metadata or {}
        ))
        return dict(result) if result else {}

    async def get_license_by_key(self, license_key: str) -> Optional[Dict]:
        """Get license by license key."""
        query = "SELECT * FROM licenses WHERE license_key = $1"
        return await self._db.fetch_one(query, (license_key,))

    async def get_license_by_key_id(self, key_id: str) -> Optional[Dict]:
        """Get license by key_id."""
        query = "SELECT * FROM licenses WHERE key_id = $1"
        return await self._db.fetch_one(query, (key_id,))

    async def update_license(
        self,
        key_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update license fields."""
        if not updates:
            return False

        set_clauses = []
        values = [key_id]
        for i, (field, value) in enumerate(updates.items(), start=2):
            set_clauses.append(f"{field} = ${i}")
            values.append(value)

        query = f"""
            UPDATE licenses SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE key_id = $1
        """
        await self._db.execute(query, tuple(values))
        return True

    async def revoke_license(self, key_id: str, reason: str, revoked_by: str = "system") -> bool:
        """Revoke a license and add to revocations table."""
        # Get license info first
        license_info = await self.get_license_by_key_id(key_id)
        if not license_info:
            return False

        # Add to revocations
        await self._db.execute(
            """INSERT INTO revocations (key_id, license_key, reason, revoked_by)
               VALUES ($1, $2, $3, $4)""",
            (key_id, license_info["license_key"], reason, revoked_by)
        )

        # Update license status
        await self.update_license(key_id, {"status": "revoked"})
        return True

    async def is_revoked(self, key_id: str) -> bool:
        """Check if a key is revoked."""
        query = "SELECT 1 FROM revocations WHERE key_id = $1"
        result = await self._db.fetch_one(query, (key_id,))
        return result is not None

    # ========== USAGE RECORDS ==========

    async def record_usage(
        self,
        key_id: str,
        license_id: Optional[int] = None,
        commands_count: int = 1,
        record_date: Optional[date] = None,
    ) -> Dict:
        """Record or update usage for a license key."""
        if record_date is None:
            record_date = date.today()

        # Get license_id if not provided
        if license_id is None:
            license_info = await self.get_license_by_key_id(key_id)
            license_id = license_info["id"] if license_info else None

        query = """
            INSERT INTO usage_records (license_id, key_id, date, commands_count, total_commands)
            VALUES ($1, $2, $3, $4, $4)
            ON CONFLICT (key_id, date) DO UPDATE
            SET commands_count = usage_records.commands_count + $4,
                total_commands = usage_records.total_commands + $4
            RETURNING *
        """
        result = await self._db.fetch_one(query, (license_id, key_id, record_date, commands_count))
        return dict(result) if result else {}

    async def get_usage(self, key_id: str, record_date: Optional[date] = None) -> Optional[Dict]:
        """Get usage record for a specific date."""
        if record_date is None:
            record_date = date.today()

        query = "SELECT * FROM usage_records WHERE key_id = $1 AND date = $2"
        return await self._db.fetch_one(query, (key_id, record_date))

    async def get_usage_summary(
        self,
        key_id: str,
        days: int = 30,
    ) -> Dict:
        """Get usage summary for the last N days."""
        query = """
            SELECT
                COUNT(*) as days_with_usage,
                COALESCE(SUM(commands_count), 0) as total_commands,
                COALESCE(MAX(commands_count), 0) as max_daily_commands,
                COALESCE(AVG(commands_count), 0) as avg_daily_commands
            FROM usage_records
            WHERE key_id = $1 AND date >= CURRENT_DATE - INTERVAL '%s days'
        """ % days
        result = await self._db.fetch_one(query, (key_id,))
        return dict(result) if result else {
            "days_with_usage": 0,
            "total_commands": 0,
            "max_daily_commands": 0,
            "avg_daily_commands": 0,
        }

    # ========== WEBHOOK EVENTS ==========

    async def log_webhook_event(
        self,
        event_type: str,
        event_id: str,
        payload: Dict,
        processed: bool = False,
    ) -> Dict:
        """Log a webhook event."""
        query = """
            INSERT INTO webhook_events (event_type, event_id, payload, processed)
            VALUES ($1, $2, $3, $4)
            RETURNING id, created_at
        """
        result = await self._db.fetch_one(query, (event_type, event_id, payload, processed))
        return dict(result) if result else {}

    async def mark_webhook_processed(self, event_id: str) -> bool:
        """Mark a webhook event as processed."""
        query = "UPDATE webhook_events SET processed = TRUE WHERE event_id = $1"
        await self._db.execute(query, (event_id,))
        return True


# Global instance
_repository: Optional[LicenseRepository] = None


def get_repository() -> LicenseRepository:
    """Get global repository instance."""
    global _repository
    if _repository is None:
        _repository = LicenseRepository()
    return _repository


async def init_repository() -> LicenseRepository:
    """Initialize repository with database connection."""
    from src.db.database import init_database
    await init_database()
    return get_repository()


__all__ = [
    "LicenseRepository",
    "get_repository",
    "init_repository",
]
