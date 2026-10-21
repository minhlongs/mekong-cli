# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rate Limit Metrics Emitter — ROIaaS Phase 6."""

import json
import logging
from typing import Any, Dict, List, Optional

from src.db.database import DatabaseConnection
from src.telemetry.rate_limit_models import RateLimitEvent

logger = logging.getLogger("mekong.rate_limits.metrics")


class RateLimitMetricsEmitter:
    """Emits and queries rate limit metrics."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or DatabaseConnection()
        self._batch_buffer: List[RateLimitEvent] = []
        self._batch_size: int = 100

    async def emit_event(self, event: RateLimitEvent) -> bool:
        try:
            await self._persist_event(event)
            logger.debug(f"Emitted rate limit event: {event.event_type} for tenant {event.tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to emit rate limit event: {e}")
            return False

    async def emit_batch(self, events: List[RateLimitEvent]) -> int:
        success_count = sum([1 for event in events if await self.emit_event(event)])
        logger.info(f"Emitted {success_count}/{len(events)} rate limit events")
        return success_count

    async def _persist_event(self, event: RateLimitEvent) -> str:
        query = """
            INSERT INTO rate_limit_events (
                tenant_id, tier, endpoint, preset, event_type,
                quota_limit, quota_remaining, quota_utilization_pct,
                client_ip, method, path, user_agent,
                response_status, retry_after, metadata, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16
            )
            RETURNING id
        """
        params = (
            event.tenant_id, event.tier, event.endpoint, event.preset, event.event_type,
            event.quota_limit, event.quota_remaining, event.quota_utilization_pct,
            event.client_ip, event.method, event.path, event.user_agent,
            event.response_status, event.retry_after,
            json.dumps(event.metadata) if event.metadata else None,
            event.created_at,
        )
        return await self._db.execute(query, params)

    async def get_throttle_count(self, tenant_id: str, hours: int = 24) -> int:
        query = f"""
            SELECT COUNT(*) as count FROM rate_limit_events
            WHERE tenant_id = $1 AND event_type = 'rate_limited'
              AND created_at > NOW() - INTERVAL '{hours} hours'
        """
        result = await self._db.fetch_one(query, (tenant_id,))
        return int(result.get('count', 0)) if result else 0

    async def get_quota_utilization(self, tenant_id: str, hours: int = 24) -> Dict[str, Any]:
        query = f"""
            SELECT AVG(quota_utilization_pct) as avg_utilization,
                   MAX(quota_utilization_pct) as max_utilization,
                   COUNT(*) as total_requests
            FROM rate_limit_events
            WHERE tenant_id = $1 AND created_at > NOW() - INTERVAL '{hours} hours'
        """
        result = await self._db.fetch_one(query, (tenant_id,))
        if not result:
            return {"avg_utilization": 0, "max_utilization": 0, "total_requests": 0}
        return {
            "avg_utilization": float(result.get('avg_utilization', 0) or 0),
            "max_utilization": float(result.get('max_utilization', 0) or 0),
            "total_requests": int(result.get('total_requests', 0)),
        }

    async def get_events_by_tier(self, hours: int = 24) -> List[Dict[str, Any]]:
        query = f"""
            SELECT tier, event_type, COUNT(*) as count
            FROM rate_limit_events
            WHERE created_at > NOW() - INTERVAL '{hours} hours'
            GROUP BY tier, event_type ORDER BY tier, count DESC
        """
        return [dict(row) for row in await self._db.fetch_all(query)]

    async def get_top_violated_tenants(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        query = f"""
            SELECT tenant_id, tier, COUNT(*) as violation_count
            FROM rate_limit_events
            WHERE event_type = 'rate_limited' AND created_at > NOW() - INTERVAL '{hours} hours'
            GROUP BY tenant_id, tier ORDER BY violation_count DESC LIMIT {limit}
        """
        return [dict(row) for row in await self._db.fetch_all(query)]

    async def get_recent_events(
        self, tenant_id: Optional[str] = None, event_type: Optional[str] = None, limit: int = 50,
    ) -> List[Dict[str, Any]]:
        conditions = ["created_at > NOW() - INTERVAL '24 hours'"]
        params: List[Any] = []
        if tenant_id:
            conditions.append(f"tenant_id = ${len(params) + 1}")
            params.append(tenant_id)
        if event_type:
            conditions.append(f"event_type = ${len(params) + 1}")
            params.append(event_type)
        query = f"""
            SELECT id, tenant_id, tier, endpoint, preset, event_type,
                   quota_limit, quota_remaining, quota_utilization_pct,
                   response_status, retry_after, created_at
            FROM rate_limit_events WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC LIMIT ${len(params) + 1}
        """
        params.append(limit)
        return [dict(row) for row in await self._db.fetch_all(query, tuple(params))]

    async def get_violations_summary(self, hours: int = 24) -> Dict[str, Any]:
        total_q = f"SELECT COUNT(*) as total FROM rate_limit_events WHERE event_type = 'rate_limited' AND created_at > NOW() - INTERVAL '{hours} hours'"
        by_tenant_q = f"SELECT tenant_id, COUNT(*) as count FROM rate_limit_events WHERE event_type = 'rate_limited' AND created_at > NOW() - INTERVAL '{hours} hours' GROUP BY tenant_id ORDER BY count DESC"
        top_end_q = f"SELECT endpoint, COUNT(*) as count FROM rate_limit_events WHERE event_type = 'rate_limited' AND created_at > NOW() - INTERVAL '{hours} hours' GROUP BY endpoint ORDER BY count DESC LIMIT 10"

        total_res = await self._db.fetch_one(total_q)
        by_tenant = await self._db.fetch_all(by_tenant_q)
        top_endpoints = await self._db.fetch_all(top_end_q)
        return {
            "total": int(total_res.get('total', 0)) if total_res else 0,
            "by_tenant": [dict(row) for row in by_tenant],
            "top_endpoints": [dict(row) for row in top_endpoints],
        }


class TelemetryIntegration:
    """Integrates rate limit metrics with core telemetry system."""

    def __init__(self, emitter: Optional[RateLimitMetricsEmitter] = None) -> None:
        self._emitter = emitter or RateLimitMetricsEmitter()

    async def record_rate_limit_event(
        self, tenant_id: str, tier: str, event_type: str, endpoint: str = "", preset: str = "api_default", **kwargs: Any,
    ) -> bool:
        event = RateLimitEvent(tenant_id=tenant_id, tier=tier, endpoint=endpoint, preset=preset, event_type=event_type, **kwargs)
        return await self._emitter.emit_event(event)


__all__ = ["RateLimitEvent", "RateLimitMetricsEmitter", "TelemetryIntegration"]
