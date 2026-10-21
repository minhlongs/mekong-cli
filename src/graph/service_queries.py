# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior Graph Service - Query and Traversal Operations Mixin."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from src.graph.models import (
    Action, ActionRecommendation, Behavior, BehaviorHistory, Edge, Entity,
    GraphNode, NeighborhoodResult, Prediction, PredictionResult, SimilarEntity, TrustNetworkResult,
)


class GraphQueryServiceMixin:
    """Mixin for querying graph entities, neighborhoods, trust, behaviors, and actions."""

    _repo: Any

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        data = await self._repo.get_entity(entity_id)
        return Entity.model_validate(data) if data else None

    async def get_entity_with_graph(
        self, entity_id: str, depth: int = 1, edge_types: Optional[List[str]] = None
    ) -> Optional[GraphNode]:
        """Get entity with its connected neighbors."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            return None
        entity = Entity.model_validate(entity_data)
        neighbors = await self._repo.get_multi_hop_neighbors(entity_id=entity_id, max_depth=depth, edge_types=edge_types)
        edges: List[Edge] = []
        for node_data in neighbors["nodes"]:
            edges.append(Edge(
                source_id=entity_id, target_id=node_data["id"], edge_type=node_data["edge_type"],
                weight=node_data["weight"], properties=node_data.get("edge_properties", {}),
            ))
            await self._repo.get_entity_centrality(node_data["id"])
        metrics = await self._repo.get_entity_centrality(entity_id)
        return GraphNode(entity=entity, edges=edges, metrics=metrics)

    async def get_neighborhood(
        self, entity_id: str, max_depth: int = 1, edge_types: Optional[List[str]] = None
    ) -> NeighborhoodResult:
        """Get neighborhood around an entity."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            raise ValueError(f"Entity {entity_id} not found")
        center = Entity.model_validate(entity_data)
        neighbors_data = await self._repo.get_multi_hop_neighbors(entity_id=entity_id, max_depth=max_depth, edge_types=edge_types)
        neighbors: List[GraphNode] = []
        seen_entities: Dict[str, GraphNode] = {}
        for node_data in neighbors_data["nodes"]:
            entity = Entity(id=node_data["id"], type=node_data["type"], name=node_data["name"], properties=node_data["properties"])
            edge = Edge(source_id=entity_id, target_id=entity.id, edge_type=node_data["edge_type"], weight=node_data["weight"])
            if entity.id in seen_entities:
                seen_entities[entity.id].edges.append(edge)
            else:
                metrics = self._calculate_neighbor_metrics(entity.id, neighbors_data)
                neighbor_node = GraphNode(entity=entity, edges=[edge], metrics=metrics)
                seen_entities[entity.id] = neighbor_node
                neighbors.append(neighbor_node)
        return NeighborhoodResult(center_entity=center, neighbors=neighbors, depth=max_depth, total_nodes=len(seen_entities) + 1)

    def _calculate_neighbor_metrics(self, entity_id: str, neighbors_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate metrics for a neighbor node."""
        count = sum(1 for n in neighbors_data["nodes"] if n["id"] == entity_id)
        return {"connection_strength": min(count * 0.1, 1.0), "path_count": count}

    async def get_trust_network(self, entity_id: str, direction: str = "both") -> TrustNetworkResult:
        """Get trust relationships for an entity."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            raise ValueError(f"Entity {entity_id} not found")
        entity = Entity.model_validate(entity_data)
        network_data = await self._repo.get_trust_network(entity_id, direction)

        trusted_by_nodes: List[GraphNode] = []
        for row in network_data["trusted_by"]:
            ent = Entity(id=row["source_id"], type=row["source_type"], name=row["source_name"])
            trusted_by_nodes.append(GraphNode(entity=ent, metrics=await self._repo.get_entity_centrality(row["source_id"])))

        trusts_nodes: List[GraphNode] = []
        for row in network_data["trusts"]:
            ent = Entity(id=row["target_id"], type=row["target_type"], name=row["target_name"])
            trusts_nodes.append(GraphNode(entity=ent, metrics=await self._repo.get_entity_centrality(row["target_id"])))

        return TrustNetworkResult(
            entity=entity, trusted_by=trusted_by_nodes, trusts=trusts_nodes, trust_score=network_data["aggregated_score"]
        )

    async def get_behavior_history(self, entity_id: str, days: int = 30) -> BehaviorHistory:
        """Get behavior history for an entity."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            raise ValueError(f"Entity {entity_id} not found")
        entity = Entity.model_validate(entity_data)
        behaviors_data = await self._repo.get_behaviors(
            entity_id=entity_id, start_date=datetime.now(timezone.utc) - timedelta(days=days)
        )
        behaviors = [Behavior.model_validate(b) for b in behaviors_data]
        stats = await self._repo.get_entity_behavior_stats(entity_id, days=days)
        return BehaviorHistory(
            entity=entity, behaviors=behaviors, action_types=stats.get("action_types", []),
            first_seen=stats.get("first_seen"), last_seen=stats.get("last_seen"),
            total_actions=stats.get("total_behaviors", len(behaviors)),
        )

    async def find_similar_entities(
        self, entity_id: str, min_similarity: float = 0.3, limit: int = 10
    ) -> List[SimilarEntity]:
        """Find entities with similar behavior patterns."""
        results_data = await self._repo.find_similar_entities(
            entity_id=entity_id, similarity_threshold=min_similarity, limit=limit
        )
        if not await self.get_entity(entity_id):
            return []
        return [
            SimilarEntity(
                entity=Entity(id=row["id"], type=row["type"], name=row["name"], properties=row["properties"]),
                similarity_score=row["similarity_score"],
                shared_behaviors=row.get("action_types", []),
            )
            for row in results_data
            if row["similarity_score"] >= min_similarity
        ]

    async def get_predictions(
        self, entity_id: Optional[str] = None, prediction_type: Optional[str] = None,
        validated: Optional[bool] = None, limit: int = 100,
    ) -> PredictionResult:
        """Get predictions with optional filters."""
        predictions_data = await self._repo.get_predictions(
            entity_id=entity_id, prediction_type=prediction_type, validated=validated, limit=limit
        )
        predictions = [Prediction.model_validate(p) for p in predictions_data]
        entity = await self.get_entity(entity_id) if entity_id else None
        return PredictionResult(predictions=predictions, entity=entity, prediction_type=prediction_type)

    async def get_pending_actions(
        self, entity_id: Optional[str] = None, min_priority: int = 1, limit: int = 50
    ) -> List[ActionRecommendation]:
        """Get pending actions as recommendations."""
        actions_data = await self._repo.get_pending_actions(entity_id=entity_id, min_priority=min_priority, limit=limit)
        recommendations: List[ActionRecommendation] = []
        for action_data in actions_data:
            action = Action.model_validate({k: v for k, v in action_data.items() if k not in ["entity_name", "entity_type"]})
            reasoning = self._generate_action_reasoning(action, action_data.get("entity_name"))
            recommendations.append(
                ActionRecommendation(
                    action=action, reasoning=reasoning,
                    confidence=min(0.5 + (action.priority * 0.05), 0.95), supporting_evidence=[],
                )
            )
        return recommendations

    def _generate_action_reasoning(self, action: Action, entity_name: Optional[str] = None) -> str:
        """Generate human-readable reasoning for an action recommendation."""
        entity_ref = entity_name or action.entity_id
        prio = {10: "critical", 8: "high", 5: "medium", 1: "low"}.get(action.priority, f"priority {action.priority}")
        if action.reasoning:
            return f"Recommended for {entity_ref} ({prio}): {action.reasoning}"
        return f"Action {action.action_type} recommended for {entity_ref} at {prio} priority"

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        return await self._repo.get_graph_stats()
