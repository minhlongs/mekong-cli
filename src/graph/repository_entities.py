# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Graph Repository Entity and Edge Operations."""

from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


class GraphEntityEdgeRepoMixin:
    """Mixin for entity and edge PostgreSQL JSONB operations."""

    _db: Any

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
            SET name = EXCLUDED.name, description = EXCLUDED.description,
                properties = EXCLUDED.properties, updated_at = CURRENT_TIMESTAMP
            RETURNING *
        """
        result = await self._db.fetch_one(
            query, (entity_id, entity_type, name, description, properties or {})
        )
        return dict(result) if result else {}

    async def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity by ID."""
        return await self._db.fetch_one("SELECT * FROM graph_entities WHERE id = $1", (entity_id,))

    async def update_entity(self, entity_id: str, updates: Dict[str, Any]) -> bool:
        """Update entity fields."""
        if not updates:
            return False
        set_clauses = [f"{f} = ${i}" for i, f in enumerate(updates.keys(), start=2)]
        values: List[Any] = [entity_id, *updates.values()]
        query = f"UPDATE graph_entities SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = $1"
        await self._db.execute(query, tuple(values))
        return True

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete entity and cascade to related edges."""
        result = await self._db.fetchval(
            "DELETE FROM graph_entities WHERE id = $1 RETURNING id", (entity_id,)
        )
        return result is not None

    async def list_entities(
        self,
        entity_type: Optional[str] = None,
        name_contains: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List entities with optional filters."""
        conditions, params = [], []
        if entity_type:
            conditions.append(f"type = ${len(params) + 1}")
            params.append(entity_type)
        if name_contains:
            conditions.append(f"name ILIKE ${len(params) + 1}")
            params.append(f"%{name_contains}%")
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM graph_entities {where_clause} ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        rows = await self._db.fetch_all(query, tuple(params))
        return [dict(row) for row in rows]

    async def count_entities(self, entity_type: Optional[str] = None) -> int:
        """Count entities."""
        if entity_type:
            return await self._db.fetchval(
                "SELECT COUNT(*) FROM graph_entities WHERE type = $1", (entity_type,)
            )
        return await self._db.fetchval("SELECT COUNT(*) FROM graph_entities")

    async def create_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
        edge_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a directed edge between entities."""
        query = """
            INSERT INTO graph_edges (source_id, target_id, edge_type, weight, properties)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (source_id, target_id, edge_type)
            DO UPDATE SET weight = EXCLUDED.weight, properties = EXCLUDED.properties
            RETURNING *
        """
        result = await self._db.fetch_one(
            query, (source_id, target_id, edge_type, weight, properties or {})
        )
        return dict(result) if result else {}

    async def get_edge(
        self, source_id: str, target_id: str, edge_type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get edge between source and target."""
        if edge_type:
            query = "SELECT * FROM graph_edges WHERE source_id = $1 AND target_id = $2 AND edge_type = $3"
            return await self._db.fetch_one(query, (source_id, target_id, edge_type))
        query = "SELECT * FROM graph_edges WHERE source_id = $1 AND target_id = $2 ORDER BY weight DESC LIMIT 1"
        return await self._db.fetch_one(query, (source_id, target_id))

    async def delete_edge(
        self, source_id: str, target_id: str, edge_type: Optional[str] = None
    ) -> bool:
        """Delete edge."""
        if edge_type:
            query = "DELETE FROM graph_edges WHERE source_id = $1 AND target_id = $2 AND edge_type = $3"
            result = await self._db.execute(query, (source_id, target_id, edge_type))
        else:
            query = "DELETE FROM graph_edges WHERE source_id = $1 AND target_id = $2"
            result = await self._db.execute(query, (source_id, target_id))
        return result != "DELETE 0"

    async def get_neighbors(
        self, entity_id: str, edge_type: Optional[str] = None, direction: str = "outgoing"
    ) -> List[Dict[str, Any]]:
        """Get neighboring entities."""
        join_col, where_col = ("target_id", "source_id") if direction == "outgoing" else ("source_id", "target_id")
        query = f"""
            SELECT e.*, ed.edge_type, ed.weight, ed.properties as edge_properties
            FROM graph_edges ed JOIN graph_entities e ON ed.{join_col} = e.id
            WHERE ed.{where_col} = $1
        """
        params: Tuple[Any, ...] = (entity_id,)
        if edge_type:
            query += f" AND ed.edge_type = ${len(params) + 1}"
            params = params + (edge_type,)
        query += " ORDER BY ed.weight DESC"
        rows = await self._db.fetch_all(query, params)
        return [dict(row) for row in rows]

    async def get_multi_hop_neighbors(
        self, entity_id: str, max_depth: int = 2, edge_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get neighbors up to N hops using recursive CTE."""
        edge_filter = ""
        params: List[Any] = [entity_id, entity_id, max_depth]
        if edge_types:
            placeholders = ", ".join([f"${i + 3}" for i in range(len(edge_types))])
            edge_filter = f"AND ed.edge_type IN ({placeholders})"
            params.extend(edge_types)
        query = f"""
            WITH RECURSIVE graph_paths AS (
                SELECT e.id, e.type, e.name, e.properties, ed.edge_type, ed.weight,
                       1 as depth, ARRAY[ed.edge_type] as path_edges, ARRAY[e.id] as path_nodes
                FROM graph_edges ed JOIN graph_entities e ON ed.target_id = e.id
                WHERE ed.source_id = $1 {edge_filter}
                UNION ALL
                SELECT e.id, e.type, e.name, e.properties, ed.edge_type, ed.weight,
                       gp.depth + 1, gp.path_edges || ed.edge_type, gp.path_nodes || e.id
                FROM graph_edges ed JOIN graph_entities e ON ed.target_id = e.id
                JOIN graph_paths gp ON ed.source_id = gp.id
                WHERE gp.depth < $2 {edge_filter} AND e.id != ALL(gp.path_nodes)
            )
            SELECT * FROM graph_paths ORDER BY depth, weight DESC
        """
        rows = await self._db.fetch_all(query, tuple(params))
        return {"center": entity_id, "max_depth": max_depth, "nodes": [dict(row) for row in rows], "count": len(rows)}
