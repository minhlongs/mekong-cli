# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Graph Repository Prediction, Action, and Analytics Operations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class GraphAnalyticsRepoMixin:
    """Mixin for prediction, action, and analytics PostgreSQL operations."""

    _db: Any

    async def create_prediction(
        self, entity_id: str, prediction_type: str, value: Any, confidence: float,
        model_version: str, prediction_id: Optional[str] = None,
        features: Optional[Dict[str, Any]] = None, expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Store a prediction."""
        prediction_id = prediction_id or str(uuid4())
        query = (
            "INSERT INTO graph_predictions (id, entity_id, prediction_type, value, confidence, features, model_version, expires_at) "
            "VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *"
        )
        result = await self._db.fetch_one(
            query, (prediction_id, entity_id, prediction_type, value, confidence, features or {}, model_version, expires_at),
        )
        return dict(result) if result else {}

    async def validate_prediction(self, prediction_id: str, actual_outcome: Any) -> bool:
        """Validate a prediction with actual outcome."""
        await self._db.execute(
            "UPDATE graph_predictions SET validated = TRUE, actual_outcome = $2 WHERE id = $1",
            (prediction_id, actual_outcome),
        )
        return True

    async def get_predictions(
        self, entity_id: Optional[str] = None, prediction_type: Optional[str] = None,
        validated: Optional[bool] = None, limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get predictions with filters."""
        conditions, params = [], []
        if entity_id:
            conditions.append(f"entity_id = ${len(params) + 1}")
            params.append(entity_id)
        if prediction_type:
            conditions.append(f"prediction_type = ${len(params) + 1}")
            params.append(prediction_type)
        if validated is not None:
            conditions.append(f"validated = ${len(params) + 1}")
            params.append(validated)
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM graph_predictions {where_clause} ORDER BY created_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def get_prediction_accuracy(
        self, prediction_type: Optional[str] = None, model_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate prediction accuracy metrics."""
        conditions, params = ["validated = TRUE"], []
        if prediction_type:
            conditions.append(f"prediction_type = ${len(params) + 1}")
            params.append(prediction_type)
        if model_version:
            conditions.append(f"model_version = ${len(params) + 1}")
            params.append(model_version)
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""
            SELECT COUNT(*) as total_validated,
                   COUNT(*) FILTER (WHERE actual_outcome IS NOT NULL) as with_outcome,
                   AVG(CASE WHEN (value->>'confidence')::float > 0.7 THEN 1.0 ELSE 0.0 END) as high_confidence_rate
            FROM graph_predictions {where_clause}
        """
        result = await self._db.fetch_one(query, tuple(params))
        return dict(result) if result else {"total_validated": 0, "with_outcome": 0, "high_confidence_rate": 0.0}

    async def create_action(
        self,
        entity_id: str,
        action_type: str,
        description: str,
        action_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        priority: int = 1,
        status: str = "pending",
        context: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an action."""
        action_id = action_id or str(uuid4())
        query = """
            INSERT INTO graph_actions (
                id, entity_id, action_type, description, parameters, priority, status, context, reasoning
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9) RETURNING *
        """
        result = await self._db.fetch_one(
            query,
            (action_id, entity_id, action_type, description, parameters or {}, priority, status, context or {}, reasoning),
        )
        return dict(result) if result else {}

    async def update_action_status(
        self, action_id: str, status: str, executed_at: Optional[datetime] = None, reasoning: Optional[str] = None
    ) -> bool:
        """Update action status."""
        if executed_at:
            q = "UPDATE graph_actions SET status = $1, reasoning = COALESCE($2, reasoning), executed_at = $3 WHERE id = $1"
            await self._db.execute(q, (action_id, status, reasoning, executed_at))
        else:
            q = "UPDATE graph_actions SET status = $1, reasoning = COALESCE($2, reasoning) WHERE id = $1"
            await self._db.execute(q, (action_id, status, reasoning))
        return True

    async def get_pending_actions(
        self, entity_id: Optional[str] = None, min_priority: int = 1, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get pending actions."""
        query = """
            SELECT a.*, e.name as entity_name, e.type as entity_type
            FROM graph_actions a JOIN graph_entities e ON a.entity_id = e.id
            WHERE a.status = 'pending' AND a.priority >= $1
        """
        params: List[Any] = [min_priority]
        if entity_id:
            query += f" AND a.entity_id = ${len(params) + 1}"
            params.append(entity_id)
        query += ' ORDER BY a.priority DESC, a.created_at ASC LIMIT $" + str(len(params) + 1)'
        params.append(limit)
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def find_similar_entities(
        self, entity_id: str, similarity_threshold: float = 0.5, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find entities with similar behavior patterns."""
        if not await self.get_entity(entity_id):  # type: ignore[attr-defined]
            return []
        ref_behaviors = await self.get_behaviors(entity_id=entity_id, limit=1000)  # type: ignore[attr-defined]
        query = """
            SELECT e.*, COUNT(DISTINCT b.action_type) as shared_actions,
                   ARRAY_AGG(DISTINCT b.action_type) as action_types
            FROM graph_entities e JOIN graph_behaviors b ON e.id = b.entity_id
            WHERE e.id != $1
              AND b.action_type IN (SELECT DISTINCT action_type FROM graph_behaviors WHERE entity_id = $1)
            GROUP BY e.id HAVING COUNT(DISTINCT b.action_type) >= $2
            ORDER BY shared_actions DESC, e.name LIMIT $3
        """
        rows = await self._db.fetch_all(query, (entity_id, 1, limit))
        entity_action_count = len(set(ref_behaviors))
        return [
            {**dict(row), "similarity_score": row["shared_actions"] / entity_action_count if entity_action_count > 0 else 0.0}
            for row in rows
        ]

    async def get_entity_centrality(self, entity_id: str) -> Dict[str, float]:
        """Calculate simple centrality metrics for an entity."""
        out_degree = await self._db.fetchval("SELECT COUNT(*) FROM graph_edges WHERE source_id = $1", (entity_id,)) or 0
        in_degree = await self._db.fetchval("SELECT COUNT(*) FROM graph_edges WHERE target_id = $1", (entity_id,)) or 0
        return {"out_degree": out_degree, "in_degree": in_degree, "total_degree": out_degree + in_degree}

    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        tables = ("entities", "edges", "behaviors", "trust", "intents", "predictions", "actions")
        keys = ("entities", "edges", "behaviors", "trust_rels", "intents", "predictions", "actions")
        stats: Dict[str, Any] = {k: await self._db.fetchval(f"SELECT COUNT(*) FROM graph_{t}") or 0 for k, t in zip(keys, tables)}
        type_rows = await self._db.fetch_all("SELECT type, COUNT(*) as count FROM graph_entities GROUP BY type ORDER BY count DESC")
        stats["entity_types"] = {row["type"]: row["count"] for row in type_rows}
        return stats
