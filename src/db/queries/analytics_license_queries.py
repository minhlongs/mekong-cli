# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""License revenue, tier distribution, and health analytics queries."""

from typing import Any, Dict, List

from src.db.database import DatabaseConnection


def _analytics_mod() -> Any:
    import src.db.queries.analytics_queries as _mod
    return _mod


class AnalyticsLicenseQueriesMixin:
    """Mixin providing license revenue, distribution, and renewal queries."""

    _db: DatabaseConnection

    async def get_revenue_summary(self) -> Dict[str, Any]:
        """Get estimated MRR from subscription data."""
        query = """
            SELECT
                tier,
                COUNT(*) as count,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count
            FROM licenses
            GROUP BY tier
        """
        results = await self._db.fetch_all(query)
        tier_fn = _analytics_mod().get_tier

        total_mrr = 0
        by_tier = {}

        for row in results:
            tier = row["tier"]
            tier_obj = tier_fn(tier)
            price = tier_obj.monthly_price_usd if tier_obj else 0
            mrr = price * row["active_count"]
            total_mrr += mrr
            by_tier[tier] = {
                "count": row["count"],
                "active": row["active_count"],
                "mrr": mrr,
            }

        return {
            "total_mrr": total_mrr,
            "by_tier": by_tier,
            "active_subscriptions": sum(r["active_count"] for r in results),
        }

    async def get_license_tier_distribution(self) -> Dict[str, Any]:
        """Get count of licenses by tier."""
        query = """
            SELECT
                tier,
                status,
                COUNT(*) as count
            FROM licenses
            GROUP BY tier, status
            ORDER BY tier
        """
        results = await self._db.fetch_all(query)

        by_tier: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        total = 0

        for row in results:
            tier = row["tier"]
            status = row["status"]
            by_tier[tier] = by_tier.get(tier, 0) + row["count"]
            by_status[status] = by_status.get(status, 0) + row["count"]
            total += row["count"]

        return {
            "total": total,
            "by_tier": by_tier,
            "by_status": by_status,
        }

    async def get_license_health_summary(self) -> Dict[str, Any]:
        """Get license health summary by status."""
        query = """
            SELECT
                status,
                COUNT(*) as count
            FROM licenses
            GROUP BY status
            ORDER BY status
        """
        results = await self._db.fetch_all(query)

        by_status: Dict[str, int] = {}
        total = 0

        for row in results:
            status = row["status"]
            count = int(row["count"])
            by_status[status.upper()] = count
            total += count

        expiring_soon_query = """
            SELECT COUNT(*) as count
            FROM licenses
            WHERE status = 'active'
              AND expires_at IS NOT NULL
              AND expires_at BETWEEN NOW() AND NOW() + INTERVAL '7 days'
        """
        expiring_soon = await self._db.fetch_one(expiring_soon_query)

        expired_query = """
            SELECT COUNT(*) as count
            FROM licenses
            WHERE status = 'active'
              AND expires_at < NOW()
        """
        expired = await self._db.fetch_one(expired_query)

        return {
            "total": total,
            "by_status": by_status,
            "active_count": by_status.get("ACTIVE", 0),
            "suspended_count": by_status.get("SUSPENDED", 0),
            "revoked_count": by_status.get("REVOKED", 0),
            "expired_count": by_status.get("EXPIRED", 0),
            "invalid_count": by_status.get("INVALID", 0),
            "expiring_soon_count": int(expiring_soon["count"]) if expiring_soon else 0,
            "expired_but_active_count": int(expired["count"]) if expired else 0,
        }

    async def get_expired_licenses_for_renewal(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get expired or expiring licenses that need renewal prompts."""
        query = """
            SELECT
                license_key,
                email,
                org_name,
                tier,
                status,
                expires_at,
                created_at,
                CASE
                    WHEN expires_at < NOW() THEN 'expired'
                    WHEN expires_at <= NOW() + INTERVAL '%s days' THEN 'expiring_soon'
                    ELSE 'active'
                END as renewal_status,
                CASE
                    WHEN expires_at < NOW() THEN EXTRACT(DAY FROM NOW() - expires_at)::int
                    ELSE EXTRACT(DAY FROM expires_at - NOW())::int
                END as days_since_or_until_expiry
            FROM licenses
            WHERE status = 'active'
              AND expires_at IS NOT NULL
              AND (
                  expires_at < NOW()
                  OR expires_at <= NOW() + INTERVAL '%s days'
              )
            ORDER BY expires_at ASC
        """ % (days, days)

        results = await self._db.fetch_all(query)
        return [dict(row) for row in results]
