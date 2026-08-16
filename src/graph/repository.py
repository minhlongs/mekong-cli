# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Graph Repository Layer - PostgreSQL JSONB operations for behavior graph.

Provides low-level CRUD and graph traversal operations.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from src.db.database import get_database, DatabaseConnection


class GraphRepository:
    """Repository for behavior graph data operations with PostgreSQL JSONB."""

    def __init__(self, db: Optional[DatabaseConnection] = None) -> None:
        self._db = db or get_database()

    # ========== Entity Operations ==========

    async def create_entity(
        self,
        entity_type: str,
        name: str,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new graph entity."""
        entity_id = entity_id or str(uuid4())
        query = """
            INSERT INTO graph_entities (id, type, name, description, properties)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (id) DO UPDATE
            SET name = EXCLUDED.name,
                description = EXCLUDED.description,
                properties = EXCLUDED.properties,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """
        result = await self._db.fetch_one(
            query, (entity_id, entity_type, name, description, properties or {})
        )
        return dict(result) if result else {}

    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID."""
        query = "SELECT * FROM graph_entities WHERE id = $1"
        return await self._db.fetch_one(query, (entity_id,))

    async def update_entity(
        self,
        entity_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update entity fields."""
        if not updates:
            return False

        set_clauses = []
        values = [entity_id]
        for i, (field, value) in enumerate(updates.items(), start=2):
            set_clauses.append(f"{field} = ${i}")
            values.append(value)

        query = f"""
            UPDATE graph_entities
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = $1
        """
        await self._db.execute(query, tuple(values))
        return True

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete entity and cascade to related edges."""
        query = "DELETE FROM graph_entities WHERE id = $1 RETURNING id"
        result = await self._db.fetchval(query, (entity_id,))
        return result is not None

    async def list_entities(
        self,
        entity_type: Optional[str] = None,
        name_contains: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List entities with optional filters."""
        conditions = []
        params: List[Any] = []

        if entity_type:
            conditions.append("type = $" + str(len(params) + 1))
            params.append(entity_type)

        if name_contains:
            conditions.append("name ILIKE $" + str(len(params) + 1))
            params.append(f"%{name_contains}%")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT * FROM graph_entities
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """
        params.extend([limit, offset])
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def count_entities(self, entity_type: Optional[str] = None) -> int:
        """Count entities."""
        if entity_type:
            query = "SELECT COUNT(*) FROM graph_entities WHERE type = $1"
            return await self._db.fetchval(query, (entity_type,))
        query = "SELECT COUNT(*) FROM graph_entities"
        return await self._db.fetchval(query)

    # ========== Edge Operations ==========

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        edge_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a directed edge between entities."""
        query = """
            INSERT INTO graph_edges (source_id, target_id, edge_type, weight, properties)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (source_id, target_id, edge_type)
            DO UPDATE SET
                weight = EXCLUDED.weight,
                properties = EXCLUDED.properties
            RETURNING *
        """
        result = await self._db.fetch_one(
            query, (source_id, target_id, edge_type, weight, properties or {})
        )
        return dict(result) if result else {}

    async def get_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get edge between source and target."""
        if edge_type:
            query = """
                SELECT * FROM graph_edges
                WHERE source_id = $1 AND target_id = $2 AND edge_type = $3
            """
            return await self._db.fetch_one(query, (source_id, target_id, edge_type))
        query = """
            SELECT * FROM graph_edges
            WHERE source_id = $1 AND target_id = $2
            ORDER BY weight DESC
            LIMIT 1
        """
        return await self._db.fetch_one(query, (source_id, target_id))

    async def delete_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: Optional[str] = None
    ) -> bool:
        """Delete edge."""
        if edge_type:
            query = """
                DELETE FROM graph_edges
                WHERE source_id = $1 AND target_id = $2 AND edge_type = $3
            """
            result = await self._db.execute(query, (source_id, target_id, edge_type))
        else:
            query = "DELETE FROM graph_edges WHERE source_id = $1 AND target_id = $2"
            result = await self._db.execute(query, (source_id, target_id))
        return result != "DELETE 0"

    async def get_neighbors(
        self,
        entity_id: str,
        edge_type: Optional[str] = None,
        direction: str = "outgoing"
    ) -> List[Dict[str, Any]]:
        """Get neighboring entities."""
        if direction == "outgoing":
            query = """
                SELECT e.*, ed.edge_type, ed.weight, ed.properties as edge_properties
                FROM graph_edges ed
                JOIN graph_entities e ON ed.target_id = e.id
                WHERE ed.source_id = $1
            """
            params: Tuple = (entity_id,)
        else:
            query = """
                SELECT e.*, ed.edge_type, ed.weight, ed.properties as edge_properties
                FROM graph_edges ed
                JOIN graph_entities e ON ed.source_id = e.id
                WHERE ed.target_id = $1
            """
            params = (entity_id,)

        if edge_type:
            query += " AND ed.edge_type = $" + str(len(params) + 1)
            params = params + (edge_type,)

        query += " ORDER BY ed.weight DESC"
        rows = await self._db.fetch_all(query, params)
        return [dict(row) for row in rows]

    async def get_multi_hop_neighbors(
        self,
        entity_id: str,
        max_depth: int = 2,
        edge_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get neighbors up to N hops using recursive CTE."""
        edge_filter = ""
        params: List[Any] = [entity_id, entity_id, max_depth]
        if edge_types:
            placeholders = ', '.join([f"${i + 3}" for i in range(len(edge_types))])
            edge_filter = f"AND ed.edge_type IN ({placeholders})"
            params.extend(edge_types)

        query = f"""
            WITH RECURSIVE graph_paths AS (
                -- Level 1: direct neighbors
                SELECT
                    e.id,
                    e.type,
                    e.name,
                    e.properties,
                    ed.edge_type,
                    ed.weight,
                    1 as depth,
                    ARRAY[ed.edge_type] as path_edges,
                    ARRAY[e.id] as path_nodes
                FROM graph_edges ed
                JOIN graph_entities e ON ed.target_id = e.id
                WHERE ed.source_id = $1 {edge_filter}

                UNION ALL

                -- Recursive expansion
                SELECT
                    e.id,
                    e.type,
                    e.name,
                    e.properties,
                    ed.edge_type,
                    ed.weight,
                    gp.depth + 1,
                    gp.path_edges || ed.edge_type,
                    gp.path_nodes || e.id
                FROM graph_edges ed
                JOIN graph_entities e ON ed.target_id = e.id
                JOIN graph_paths gp ON ed.source_id = gp.id
                WHERE gp.depth < $2 {edge_filter}
                  AND e.id != ALL(gp.path_nodes)  -- prevent cycles
            )
            SELECT * FROM graph_paths ORDER BY depth, weight DESC
        """
        rows = await self._db.fetch_all(query, tuple(params))
        return {
            "center": entity_id,
            "max_depth": max_depth,
            "nodes": [dict(row) for row in rows],
            "count": len(rows)
        }

    # ========== Behavior Operations ==========

    async def record_behavior(
        self,
        entity_id: str,
        action_type: str,
        behavior_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Record a behavior for an entity."""
        behavior_id = behavior_id or str(uuid4())
        query = """
            INSERT INTO graph_behaviors (
                id, entity_id, action_type, context, outcome, confidence, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self._db.fetch_one(
            query,
            (behavior_id, entity_id, action_type, context or {}, outcome, confidence, metadata or {})
        )
        return dict(result) if result else {}

    async def get_behaviors(
        self,
        entity_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get behaviors with filters."""
        conditions = []
        params: List[Any] = []

        if entity_id:
            conditions.append("entity_id = $" + str(len(params) + 1))
            params.append(entity_id)

        if action_type:
            conditions.append("action_type = $" + str(len(params) + 1))
            params.append(action_type)

        if start_date:
            conditions.append("timestamp >= $" + str(len(params) + 1))
            params.append(start_date)

        if end_date:
            conditions.append("timestamp <= $" + str(len(params) + 1))
            params.append(end_date)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT * FROM graph_behaviors
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${len(params) + 1}
        """
        params.append(limit)
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def get_entity_behavior_stats(
        self,
        entity_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get behavior statistics for an entity."""
        query = """
            SELECT
                COUNT(*) as total_behaviors,
                COUNT(DISTINCT action_type) as unique_action_types,
                MIN(timestamp) as first_seen,
                MAX(timestamp) as last_seen,
                jsonb_object_keys(
                    jsonb_agg(DISTINCT action_type)
                ) as action_types
            FROM graph_behaviors
            WHERE entity_id = $1
              AND timestamp >= CURRENT_DATE - INTERVAL '%s days'
        """ % days
        result = await self._db.fetch_one(query, (entity_id,))
        return dict(result) if result else {
            "total_behaviors": 0,
            "unique_action_types": 0,
            "first_seen": None,
            "last_seen": None,
            "action_types": []
        }

    # ========== Trust Operations ==========

    async def set_trust(
        self,
        source_id: str,
        target_id: str,
        score: float,
        weight: float = 1.0,
        rationale: Optional[str] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
        trust_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Set or update trust relationship."""
        trust_id = trust_id or str(uuid4())
        query = """
            INSERT INTO graph_trust (id, source_id, target_id, score, weight, rationale, evidence)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (source_id, target_id) DO UPDATE
            SET score = EXCLUDED.score,
                weight = EXCLUDED.weight,
                rationale = EXCLUDED.rationale,
                evidence = EXCLUDED.evidence,
                updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """
        result = await self._db.fetch_one(
            query, (trust_id, source_id, target_id, score, weight, rationale, evidence or [])
        )
        return dict(result) if result else {}

    async def get_trust(
        self,
        source_id: str,
        target_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get trust score between two entities."""
        query = "SELECT * FROM graph_trust WHERE source_id = $1 AND target_id = $2"
        return await self._db.fetch_one(query, (source_id, target_id))

    async def get_trust_network(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> Dict[str, Any]:
        """Get complete trust network for an entity."""
        result = {"entity_id": entity_id, "trusted_by": [], "trusts": []}

        if direction in ["incoming", "both"]:
            query = """
                SELECT t.*, e.name as source_name, e.type as source_type
                FROM graph_trust t
                JOIN graph_entities e ON t.source_id = e.id
                WHERE t.target_id = $1
                ORDER BY t.score DESC, t.weight DESC
            """
            rows = await self._db.fetch_all(query, (entity_id,))
            result["trusted_by"] = [dict(row) for row in rows]

        if direction in ["outgoing", "both"]:
            query = """
                SELECT t.*, e.name as target_name, e.type as target_type
                FROM graph_trust t
                JOIN graph_entities e ON t.target_id = e.id
                WHERE t.source_id = $1
                ORDER BY t.score DESC, t.weight DESC
            """
            rows = await self._db.fetch_all(query, (entity_id,))
            result["trusts"] = [dict(row) for row in rows]

        # Calculate aggregated trust score
        incoming_avg = sum(r["score"] for r in result["trusted_by"]) / max(1, len(result["trusted_by"]))
        outgoing_avg = sum(r["score"] for r in result["trusts"]) / max(1, len(result["trusts"]))
        result["aggregated_score"] = (incoming_avg + outgoing_avg) / 2

        return result

    # ========== Intent Operations ==========

    async def create_intent(
        self,
        entity_id: str,
        intent_type: str,
        description: str,
        intent_id: Optional[str] = None,
        confidence: float = 1.0,
        related_entities: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Create an intent."""
        intent_id = intent_id or str(uuid4())
        query = """
            INSERT INTO graph_intents (
                id, entity_id, intent_type, description, confidence,
                related_entities, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING *
        """
        result = await self._db.fetch_one(
            query,
            (intent_id, entity_id, intent_type, description, confidence,
             related_entities or [], expires_at)
        )
        return dict(result) if result else {}

    async def update_intent_status(
        self,
        intent_id: str,
        status: str
    ) -> bool:
        """Update intent status."""
        query = "UPDATE graph_intents SET status = $1 WHERE id = $2"
        await self._db.execute(query, (status, intent_id))
        return True

    async def get_active_intents(
        self,
        entity_id: Optional[str] = None,
        intent_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get active intents."""
        conditions = ["status = 'active'"]
        params: List[Any] = []

        if entity_id:
            conditions.append("entity_id = $" + str(len(params) + 1))
            params.append(entity_id)

        if intent_type:
            conditions.append("intent_type = $" + str(len(params) + 1))
            params.append(intent_type)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""
            SELECT * FROM graph_intents
            {where_clause}
            ORDER BY confidence DESC, created_at DESC
        """
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    # ========== Prediction Operations ==========

    async def create_prediction(
        self,
        entity_id: str,
        prediction_type: str,
        value: Any,
        confidence: float,
        model_version: str,
        prediction_id: Optional[str] = None,
        features: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Store a prediction."""
        prediction_id = prediction_id or str(uuid4())
        query = """
            INSERT INTO graph_predictions (
                id, entity_id, prediction_type, value, confidence,
                features, model_version, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        result = await self._db.fetch_one(
            query,
            (prediction_id, entity_id, prediction_type, value, confidence,
             features or {}, model_version, expires_at)
        )
        return dict(result) if result else {}

    async def validate_prediction(
        self,
        prediction_id: str,
        actual_outcome: Any
    ) -> bool:
        """Validate a prediction with actual outcome."""
        query = """
            UPDATE graph_predictions
            SET validated = TRUE, actual_outcome = $2
            WHERE id = $1
        """
        await self._db.execute(query, (prediction_id, actual_outcome))
        return True

    async def get_predictions(
        self,
        entity_id: Optional[str] = None,
        prediction_type: Optional[str] = None,
        validated: Optional[bool] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get predictions with filters."""
        conditions = []
        params: List[Any] = []

        if entity_id:
            conditions.append("entity_id = $" + str(len(params) + 1))
            params.append(entity_id)

        if prediction_type:
            conditions.append("prediction_type = $" + str(len(params) + 1))
            params.append(prediction_type)

        if validated is not None:
            conditions.append("validated = $" + str(len(params) + 1))
            params.append(validated)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"""
            SELECT * FROM graph_predictions
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${len(params) + 1}
        """
        params.append(limit)
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def get_prediction_accuracy(
        self,
        prediction_type: Optional[str] = None,
        model_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate prediction accuracy metrics."""
        conditions = ["validated = TRUE"]
        params: List[Any] = []

        if prediction_type:
            conditions.append("prediction_type = $" + str(len(params) + 1))
            params.append(prediction_type)

        if model_version:
            conditions.append("model_version = $" + str(len(params) + 1))
            params.append(model_version)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        query = f"""
            SELECT
                COUNT(*) as total_validated,
                COUNT(*) FILTER (WHERE actual_outcome IS NOT NULL) as with_outcome,
                AVG(
                    CASE
                        WHEN (value->>'confidence')::float > 0.7 THEN 1.0
                        ELSE 0.0
                    END
                ) as high_confidence_rate
            FROM graph_predictions
            {where_clause}
        """
        result = await self._db.fetch_one(query, tuple(params))
        return dict(result) if result else {"total_validated": 0, "with_outcome": 0, "high_confidence_rate": 0.0}

    # ========== Action Operations ==========

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
        reasoning: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create an action."""
        action_id = action_id or str(uuid4())
        query = """
            INSERT INTO graph_actions (
                id, entity_id, action_type, description, parameters,
                priority, status, context, reasoning
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """
        result = await self._db.fetch_one(
            query,
            (action_id, entity_id, action_type, description, parameters or {},
             priority, status, context or {}, reasoning)
        )
        return dict(result) if result else {}

    async def update_action_status(
        self,
        action_id: str,
        status: str,
        executed_at: Optional[datetime] = None,
        reasoning: Optional[str] = None
    ) -> bool:
        """Update action status."""
        if executed_at:
            query = """
                UPDATE graph_actions
                SET status = $1, reasoning = COALESCE($2, reasoning), executed_at = $3
                WHERE id = $1
            """
            await self._db.execute(query, (action_id, status, reasoning, executed_at))
        else:
            query = """
                UPDATE graph_actions
                SET status = $1, reasoning = COALESCE($2, reasoning)
                WHERE id = $1
            """
            await self._db.execute(query, (action_id, status, reasoning))
        return True

    async def get_pending_actions(
        self,
        entity_id: Optional[str] = None,
        min_priority: int = 1,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get pending actions."""
        query = """
            SELECT a.*, e.name as entity_name, e.type as entity_type
            FROM graph_actions a
            JOIN graph_entities e ON a.entity_id = e.id
            WHERE a.status = 'pending' AND a.priority >= $1
        """
        params: List[Any] = [min_priority]

        if entity_id:
            query += " AND a.entity_id = $" + str(len(params) + 1)
            params.append(entity_id)

        query += """
            ORDER BY a.priority DESC, a.created_at ASC
            LIMIT $" + str(len(params) + 1)
        """
        params.append(limit)
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    # ========== Graph Analytics ==========

    async def find_similar_entities(
        self,
        entity_id: str,
        similarity_threshold: float = 0.5,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find entities with similar behavior patterns."""
        # First, get the reference entity's behavior signature
        entity = await self.get_entity(entity_id)
        if not entity:
            return []

        # Get behaviors for reference entity
        ref_behaviors = await self.get_behaviors(entity_id=entity_id, limit=1000)

        # Get entities with overlapping behaviors
        query = """
            SELECT e.*,
                   COUNT(DISTINCT b.action_type) as shared_actions,
                   ARRAY_AGG(DISTINCT b.action_type) as action_types
            FROM graph_entities e
            JOIN graph_behaviors b ON e.id = b.entity_id
            WHERE e.id != $1
              AND b.action_type IN (
                  SELECT DISTINCT action_type
                  FROM graph_behaviors
                  WHERE entity_id = $1
              )
            GROUP BY e.id
            HAVING COUNT(DISTINCT b.action_type) >= $2
            ORDER BY shared_actions DESC, e.name
            LIMIT $3
        """
        rows = await self._db.fetch_all(
            query, (entity_id, 1, limit)  # At least 1 shared action type
        )
        results = []
        for row in rows:
            row_dict = dict(row)
            # Calculate similarity score
            entity_action_count = len(set(ref_behaviors))
            if entity_action_count > 0:
                row_dict["similarity_score"] = row_dict["shared_actions"] / entity_action_count
            else:
                row_dict["similarity_score"] = 0.0
            results.append(row_dict)
        return results

    async def get_entity_centrality(
        self,
        entity_id: str
    ) -> Dict[str, float]:
        """Calculate simple centrality metrics for an entity."""
        # Out-degree: number of outgoing edges
        out_deg_query = "SELECT COUNT(*) FROM graph_edges WHERE source_id = $1"
        out_degree = await self._db.fetchval(out_deg_query, (entity_id,)) or 0

        # In-degree: number of incoming edges
        in_deg_query = "SELECT COUNT(*) FROM graph_edges WHERE target_id = $1"
        in_degree = await self._db.fetchval(in_deg_query, (entity_id,)) or 0

        # Total degree
        total_degree = out_degree + in_degree

        return {
            "out_degree": out_degree,
            "in_degree": in_degree,
            "total_degree": total_degree
        }

    async def get_graph_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        queries = {
            "entities": "SELECT COUNT(*) FROM graph_entities",
            "edges": "SELECT COUNT(*) FROM graph_edges",
            "behaviors": "SELECT COUNT(*) FROM graph_behaviors",
            "trust_rels": "SELECT COUNT(*) FROM graph_trust",
            "intents": "SELECT COUNT(*) FROM graph_intents",
            "predictions": "SELECT COUNT(*) FROM graph_predictions",
            "actions": "SELECT COUNT(*) FROM graph_actions",
        }

        stats = {}
        for key, query in queries.items():
            stats[key] = await self._db.fetchval(query) or 0

        # Entity type distribution
        type_query = """
            SELECT type, COUNT(*) as count
            FROM graph_entities
            GROUP BY type
            ORDER BY count DESC
        """
        type_rows = await self._db.fetch_all(type_query)
        stats["entity_types"] = {row["type"]: row["count"] for row in type_rows}

        return stats


# Global instance
_repository: Optional[GraphRepository] = None


def get_graph_repository() -> GraphRepository:
    """Get global graph repository instance."""
    global _repository
    if _repository is None:
        _repository = GraphRepository()
    return _repository


async def init_graph_repository() -> GraphRepository:
    """Initialize repository with database connection."""
    from src.db.database import init_database
    await init_database()
    return get_graph_repository()


__all__ = [
    "GraphRepository",
    "get_graph_repository",
    "init_graph_repository",
]
