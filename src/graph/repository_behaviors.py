# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Graph Repository Behavior, Trust, and Intent Operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class GraphBehaviorTrustRepoMixin:
    """Mixin for behavior, trust, and intent PostgreSQL operations."""

    _db: Any

    async def record_behavior(
        self, entity_id: str, action_type: str, behavior_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None, outcome: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0, metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a behavior for an entity."""
        behavior_id = behavior_id or str(uuid4())
        query = (
            "INSERT INTO graph_behaviors (id, entity_id, action_type, context, outcome, confidence, metadata) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *"
        )
        result = await self._db.fetch_one(
            query, (behavior_id, entity_id, action_type, context or {}, outcome, confidence, metadata or {}),
        )
        return dict(result) if result else {}

    async def get_behaviors(
        self, entity_id: Optional[str] = None, action_type: Optional[str] = None,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None, limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get behaviors with filters."""
        conditions, params = [], []
        if entity_id:
            conditions.append(f"entity_id = ${len(params) + 1}")
            params.append(entity_id)
        if action_type:
            conditions.append(f"action_type = ${len(params) + 1}")
            params.append(action_type)
        if start_date:
            conditions.append(f"timestamp >= ${len(params) + 1}")
            params.append(start_date)
        if end_date:
            conditions.append(f"timestamp <= ${len(params) + 1}")
            params.append(end_date)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM graph_behaviors {where_clause} ORDER BY timestamp DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def get_entity_behavior_stats(self, entity_id: str, days: int = 30) -> Dict[str, Any]:
        """Get behavior statistics for an entity."""
        query = """
            SELECT COUNT(*) as total_behaviors, COUNT(DISTINCT action_type) as unique_action_types,
                   MIN(timestamp) as first_seen, MAX(timestamp) as last_seen,
                   jsonb_object_keys(jsonb_agg(DISTINCT action_type)) as action_types
            FROM graph_behaviors
            WHERE entity_id = $1 AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
        """ % days
        result = await self._db.fetch_one(query, (entity_id,))
        return dict(result) if result else {
            "total_behaviors": 0, "unique_action_types": 0,
            "first_seen": None, "last_seen": None, "action_types": [],
        }

    async def set_trust(
        self,
        source_id: str,
        target_id: str,
        score: float,
        weight: float = 1.0,
        rationale: Optional[str] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
        trust_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Set or update trust relationship."""
        trust_id = trust_id or str(uuid4())
        query = """
            INSERT INTO graph_trust (id, source_id, target_id, score, weight, rationale, evidence)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (source_id, target_id) DO UPDATE
            SET score = EXCLUDED.score, weight = EXCLUDED.weight,
                rationale = EXCLUDED.rationale, evidence = EXCLUDED.evidence,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """
        result = await self._db.fetch_one(
            query, (trust_id, source_id, target_id, score, weight, rationale, evidence or [])
        )
        return dict(result) if result else {}

    async def get_trust(self, source_id: str, target_id: str) -> Optional[Dict[str, Any]]:
        """Get trust score between two entities."""
        return await self._db.fetch_one(
            "SELECT * FROM graph_trust WHERE source_id = $1 AND target_id = $2",
            (source_id, target_id),
        )

    async def get_trust_network(self, entity_id: str, direction: str = "both") -> Dict[str, Any]:
        """Get complete trust network for an entity."""
        result: Dict[str, Any] = {"entity_id": entity_id, "trusted_by": [], "trusts": []}
        if direction in ["incoming", "both"]:
            query = """
                SELECT t.*, e.name as source_name, e.type as source_type
                FROM graph_trust t JOIN graph_entities e ON t.source_id = e.id
                WHERE t.target_id = $1 ORDER BY t.score DESC, t.weight DESC
            """
            rows = await self._db.fetch_all(query, (entity_id,))
            result["trusted_by"] = [dict(row) for row in rows]
        if direction in ["outgoing", "both"]:
            query = """
                SELECT t.*, e.name as target_name, e.type as target_type
                FROM graph_trust t JOIN graph_entities e ON t.target_id = e.id
                WHERE t.source_id = $1 ORDER BY t.score DESC, t.weight DESC
            """
            rows = await self._db.fetch_all(query, (entity_id,))
            result["trusts"] = [dict(row) for row in rows]
        incoming_avg = sum(r["score"] for r in result["trusted_by"]) / max(1, len(result["trusted_by"]))
        outgoing_avg = sum(r["score"] for r in result["trusts"]) / max(1, len(result["trusts"]))
        result["aggregated_score"] = (incoming_avg + outgoing_avg) / 2
        return result

    async def create_intent(
        self,
        entity_id: str,
        intent_type: str,
        description: str,
        intent_id: Optional[str] = None,
        confidence: float = 1.0,
        related_entities: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Create an intent."""
        intent_id = intent_id or str(uuid4())
        query = """
            INSERT INTO graph_intents (
                id, entity_id, intent_type, description, confidence, related_entities, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *
        """
        result = await self._db.fetch_one(
            query,
            (intent_id, entity_id, intent_type, description, confidence, related_entities or [], expires_at),
        )
        return dict(result) if result else {}

    async def update_intent_status(self, intent_id: str, status: str) -> bool:
        """Update intent status."""
        await self._db.execute("UPDATE graph_intents SET status = $1 WHERE id = $2", (status, intent_id))
        return True

    async def get_active_intents(
        self, entity_id: Optional[str] = None, intent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active intents."""
        conditions, params = ["status = 'active'"], []
        if entity_id:
            conditions.append(f"entity_id = ${len(params) + 1}")
            params.append(entity_id)
        if intent_type:
            conditions.append(f"intent_type = ${len(params) + 1}")
            params.append(intent_type)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"SELECT * FROM graph_intents {where_clause} ORDER BY confidence DESC, created_at DESC"
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]
