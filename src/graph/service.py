"""
Behavior Graph Service - Business logic layer for graph operations.

Provides high-level query and ingest APIs for:
- Entity management
- Behavior tracking
- Trust computation
- Intent inference
- Prediction storage
- Action recommendation
- GraphRAG context generation
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.graph.models import (
    Entity,
    EntityCreate,
    EntityUpdate,
    Behavior,
    BehaviorCreate,
    Trust,
    TrustCreate,
    TrustUpdate,
    Intent,
    IntentCreate,
    Prediction,
    PredictionCreate,
    PredictionValidate,
    Action,
    ActionCreate,
    ActionUpdate,
    Edge,
    EdgeCreate,
    GraphNode,
    NeighborhoodResult,
    TrustNetworkResult,
    BehaviorHistory,
    SimilarEntity,
    PredictionResult,
    ActionRecommendation,
    GraphRAGContext,
)
from src.graph.repository import GraphRepository


class BehaviorGraphService:
    """Service layer for behavior graph operations."""

    def __init__(self, repository: Optional[GraphRepository] = None) -> None:
        self._repo = repository or get_graph_repository()

    # ========== Ingest APIs ==========

    async def upsert_entity(
        self,
        entity_type: str,
        name: str,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """Create or update an entity."""
        data = await self._repo.create_entity(
            entity_type=entity_type,
            name=name,
            entity_id=entity_id,
            description=description,
            properties=properties
        )
        return Entity.model_validate(data)

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity and all its relationships."""
        return await self._repo.delete_entity(entity_id)

    async def record_behavior(
        self,
        entity_id: str,
        action_type: str,
        context: Optional[Dict[str, Any]] = None,
        outcome: Optional[Dict[str, Any]] = None,
        confidence: float = 1.0,
        behavior_id: Optional[str] = None
    ) -> Behavior:
        """Record a behavior for an entity."""
        data = await self._repo.record_behavior(
            entity_id=entity_id,
            action_type=action_type,
            behavior_id=behavior_id,
            context=context,
            outcome=outcome,
            confidence=confidence
        )
        return Behavior.model_validate(data)

    async def update_trust(
        self,
        source_id: str,
        target_id: str,
        score: float,
        weight: float = 1.0,
        rationale: Optional[str] = None,
        evidence: Optional[List[Dict[str, Any]]] = None
    ) -> Trust:
        """Set or update trust between entities."""
        data = await self._repo.set_trust(
            source_id=source_id,
            target_id=target_id,
            score=score,
            weight=weight,
            rationale=rationale,
            evidence=evidence
        )
        return Trust.model_validate(data)

    async def create_intent(
        self,
        entity_id: str,
        intent_type: str,
        description: str,
        confidence: float = 1.0,
        related_entities: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> Intent:
        """Create an intent for an entity."""
        data = await self._repo.create_intent(
            entity_id=entity_id,
            intent_type=intent_type,
            description=description,
            confidence=confidence,
            related_entities=related_entities,
            expires_at=expires_at
        )
        return Intent.model_validate(data)

    async def record_prediction(
        self,
        entity_id: str,
        prediction_type: str,
        value: Any,
        confidence: float,
        model_version: str,
        features: Optional[Dict[str, Any]] = None,
        expires_at: Optional[datetime] = None
    ) -> Prediction:
        """Store a prediction."""
        data = await self._repo.create_prediction(
            entity_id=entity_id,
            prediction_type=prediction_type,
            value=value,
            confidence=confidence,
            model_version=model_version,
            features=features,
            expires_at=expires_at
        )
        return Prediction.model_validate(data)

    async def validate_prediction(
        self,
        prediction_id: str,
        actual_outcome: Any,
        notes: Optional[str] = None
    ) -> bool:
        """Validate a prediction with actual outcome."""
        return await self._repo.validate_prediction(prediction_id, actual_outcome)

    async def create_action(
        self,
        entity_id: str,
        action_type: str,
        description: str,
        parameters: Optional[Dict[str, Any]] = None,
        priority: int = 1,
        context: Optional[Dict[str, Any]] = None,
        reasoning: Optional[str] = None
    ) -> Action:
        """Create an action recommendation."""
        data = await self._repo.create_action(
            entity_id=entity_id,
            action_type=action_type,
            description=description,
            parameters=parameters,
            priority=priority,
            context=context,
            reasoning=reasoning
        )
        return Action.model_validate(data)

    async def link_entities(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None
    ) -> Edge:
        """Create a directed relationship between entities."""
        data = await self._repo.create_edge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            properties=properties
        )
        return Edge.model_validate(data)

    # ========== Query APIs ==========

    async def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get entity by ID."""
        data = await self._repo.get_entity(entity_id)
        return Entity.model_validate(data) if data else None

    async def get_entity_with_graph(
        self,
        entity_id: str,
        depth: int = 1,
        edge_types: Optional[List[str]] = None
    ) -> Optional[GraphNode]:
        """Get entity with its connected neighbors."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            return None

        entity = Entity.model_validate(entity_data)

        # Get direct neighbors
        neighbors = await self._repo.get_multi_hop_neighbors(
            entity_id=entity_id,
            max_depth=depth,
            edge_types=edge_types
        )

        edges: List[Edge] = []
        neighbor_nodes: List[GraphNode] = []

        for node_data in neighbors["nodes"]:
            edge = Edge(
                source_id=entity_id,
                target_id=node_data["id"],
                edge_type=node_data["edge_type"],
                weight=node_data["weight"],
                properties=node_data.get("edge_properties", {})
            )
            edges.append(edge)

            neighbor_entity = Entity(
                id=node_data["id"],
                type=node_data["type"],
                name=node_data["name"],
                properties=node_data["properties"]
            )

            metrics = await self._repo.get_entity_centrality(node_data["id"])
            neighbor_node = GraphNode(
                entity=neighbor_entity,
                edges=[],
                metrics=metrics
            )
            neighbor_nodes.append(neighbor_node)

        metrics = await self._repo.get_entity_centrality(entity_id)
        return GraphNode(
            entity=entity,
            edges=edges,
            metrics=metrics
        )

    async def get_neighborhood(
        self,
        entity_id: str,
        max_depth: int = 1,
        edge_types: Optional[List[str]] = None
    ) -> NeighborhoodResult:
        """Get neighborhood around an entity."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            raise ValueError(f"Entity {entity_id} not found")

        center = Entity.model_validate(entity_data)

        neighbors_data = await self._repo.get_multi_hop_neighbors(
            entity_id=entity_id,
            max_depth=max_depth,
            edge_types=edge_types
        )

        neighbors: List[GraphNode] = []
        seen_entities: Dict[str, GraphNode] = {}

        for node_data in neighbors_data["nodes"]:
            entity = Entity(
                id=node_data["id"],
                type=node_data["type"],
                name=node_data["name"],
                properties=node_data["properties"]
            )

            if entity.id in seen_entities:
                seen_entities[entity.id].edges.append(Edge(
                    source_id=entity_id,
                    target_id=entity.id,
                    edge_type=node_data["edge_type"],
                    weight=node_data["weight"]
                ))
            else:
                metrics = self._calculate_neighbor_metrics(entity.id, neighbors_data)
                neighbor_node = GraphNode(
                    entity=entity,
                    edges=[Edge(
                        source_id=entity_id,
                        target_id=entity.id,
                        edge_type=node_data["edge_type"],
                        weight=node_data["weight"]
                    )],
                    metrics=metrics
                )
                seen_entities[entity.id] = neighbor_node
                neighbors.append(neighbor_node)

        return NeighborhoodResult(
            center_entity=center,
            neighbors=neighbors,
            depth=max_depth,
            total_nodes=len(seen_entities) + 1
        )

    def _calculate_neighbor_metrics(
        self,
        entity_id: str,
        neighbors_data: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate metrics for a neighbor node."""
        # Count occurrences in path
        count = sum(1 for n in neighbors_data["nodes"] if n["id"] == entity_id)
        return {
            "connection_strength": min(count * 0.1, 1.0),
            "path_count": count
        }

    async def get_trust_network(
        self,
        entity_id: str,
        direction: str = "both"
    ) -> TrustNetworkResult:
        """Get trust relationships for an entity."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            raise ValueError(f"Entity {entity_id} not found")

        entity = Entity.model_validate(entity_data)
        network_data = await self._repo.get_trust_network(entity_id, direction)

        trusted_by_nodes: List[GraphNode] = []
        for trust_row in network_data["trusted_by"]:
            ent = Entity(
                id=trust_row["source_id"],
                type=trust_row["source_type"],
                name=trust_row["source_name"]
            )
            metrics = await self._repo.get_entity_centrality(trust_row["source_id"])
            trusted_by_nodes.append(GraphNode(entity=ent, metrics=metrics))

        trusts_nodes: List[GraphNode] = []
        for trust_row in network_data["trusts"]:
            ent = Entity(
                id=trust_row["target_id"],
                type=trust_row["target_type"],
                name=trust_row["target_name"]
            )
            metrics = await self._repo.get_entity_centrality(trust_row["target_id"])
            trusts_nodes.append(GraphNode(entity=ent, metrics=metrics))

        return TrustNetworkResult(
            entity=entity,
            trusted_by=trusted_by_nodes,
            trusts=trusts_nodes,
            trust_score=network_data["aggregated_score"]
        )

    async def get_behavior_history(
        self,
        entity_id: str,
        days: int = 30
    ) -> BehaviorHistory:
        """Get behavior history for an entity."""
        entity_data = await self._repo.get_entity(entity_id)
        if not entity_data:
            raise ValueError(f"Entity {entity_id} not found")

        entity = Entity.model_validate(entity_data)
        behaviors_data = await self._repo.get_behaviors(
            entity_id=entity_id,
            start_date=datetime.now(timezone.utc) - timedelta(days=days)
        )
        behaviors = [Behavior.model_validate(b) for b in behaviors_data]

        stats = await self._repo.get_entity_behavior_stats(entity_id, days=days)

        return BehaviorHistory(
            entity=entity,
            behaviors=behaviors,
            action_types=stats.get("action_types", []),
            first_seen=stats.get("first_seen"),
            last_seen=stats.get("last_seen"),
            total_actions=stats.get("total_behaviors", len(behaviors))
        )

    async def find_similar_entities(
        self,
        entity_id: str,
        min_similarity: float = 0.3,
        limit: int = 10
    ) -> List[SimilarEntity]:
        """Find entities with similar behavior patterns."""
        results_data = await self._repo.find_similar_entities(
            entity_id=entity_id,
            similarity_threshold=min_similarity,
            limit=limit
        )

        entity = await self.get_entity(entity_id)
        if not entity:
            return []

        similar: List[SimilarEntity] = []
        for row in results_data:
            if row["similarity_score"] >= min_similarity:
                similar_entity = Entity(
                    id=row["id"],
                    type=row["type"],
                    name=row["name"],
                    properties=row["properties"]
                )
                similar.append(SimilarEntity(
                    entity=similar_entity,
                    similarity_score=row["similarity_score"],
                    shared_behaviors=row.get("action_types", [])
                ))

        return similar

    async def get_predictions(
        self,
        entity_id: Optional[str] = None,
        prediction_type: Optional[str] = None,
        validated: Optional[bool] = None,
        limit: int = 100
    ) -> PredictionResult:
        """Get predictions with optional filters."""
        predictions_data = await self._repo.get_predictions(
            entity_id=entity_id,
            prediction_type=prediction_type,
            validated=validated,
            limit=limit
        )

        predictions = [Prediction.model_validate(p) for p in predictions_data]
        entity = None
        if entity_id:
            entity = await self.get_entity(entity_id)

        return PredictionResult(
            predictions=predictions,
            entity=entity,
            prediction_type=prediction_type
        )

    async def get_pending_actions(
        self,
        entity_id: Optional[str] = None,
        min_priority: int = 1,
        limit: int = 50
    ) -> List[ActionRecommendation]:
        """Get pending actions as recommendations."""
        actions_data = await self._repo.get_pending_actions(
            entity_id=entity_id,
            min_priority=min_priority,
            limit=limit
        )

        recommendations: List[ActionRecommendation] = []
        for action_data in actions_data:
            action = Action.model_validate({
                k: v for k, v in action_data.items()
                if k not in ["entity_name", "entity_type"]
            })

            # Generate reasoning based on context
            reasoning = self._generate_action_reasoning(action, action_data.get("entity_name"))

            # Calculate confidence based on priority and entity history
            confidence = min(0.5 + (action.priority * 0.05), 0.95)

            recommendations.append(ActionRecommendation(
                action=action,
                reasoning=reasoning,
                confidence=confidence,
                supporting_evidence=[]
            ))

        return recommendations

    def _generate_action_reasoning(
        self,
        action: Action,
        entity_name: Optional[str] = None
    ) -> str:
        """Generate human-readable reasoning for an action recommendation."""
        entity_ref = entity_name or action.entity_id
        priority_desc = {10: "critical", 8: "high", 5: "medium", 1: "low"}
        prio = priority_desc.get(action.priority, f"priority {action.priority}")

        if action.reasoning:
            return f"Recommended for {entity_ref} ({prio}): {action.reasoning}"

        return f"Action {action.action_type} recommended for {entity_ref} at {prio} priority"

    async def get_graph_statistics(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        return await self._repo.get_graph_stats()

    # ========== GraphRAG Integration ==========

    async def enrich_query_with_graph(
        self,
        query: str,
        entity_id: Optional[str] = None,
        max_entities: int = 5,
        max_behaviors: int = 20,
        max_depth: int = 2
    ) -> GraphRAGContext:
        """
        Enrich a query with relevant graph context for RAG.

        Args:
            query: The user query to enrich
            entity_id: Optional specific entity to focus on
            max_entities: Maximum number of entities to include
            max_behaviors: Maximum behaviors to fetch
            max_depth: Graph traversal depth

        Returns:
            GraphRAGContext with enriched context for LLM
        """
        context = GraphRAGContext(query=query)

        if entity_id:
            # Focus on specific entity
            entity = await self.get_entity(entity_id)
            if entity:
                context.relevant_entities.append(entity)

                # Get neighborhood
                neighborhood = await self.get_neighborhood(entity_id, max_depth=max_depth)
                context.relevant_entities.extend([n.entity for n in neighborhood.neighbors[:max_entities-1]])

                # Get recent behaviors
                history = await self.get_behavior_history(entity_id, days=30)
                context.relevant_behaviors = history.behaviors[:max_behaviors]

                # Get intents
                intents_data = await self._repo.get_active_intents(entity_id=entity_id)
                context.related_intents = [Intent.model_validate(i) for i in intents_data]

                # Get trust network
                trust_net = await self.get_trust_network(entity_id)
                context.trust_network = trust_net.trusted_by[:10] + trust_net.trusts[:10]
        else:
            # Extract potential entity names from query (simple keyword match)
            # In production, this would use NLP entity extraction
            entities_data = await self._repo.list_entities(limit=max_entities)
            context.relevant_entities = [Entity.model_validate(e) for e in entities_data]

        # Generate formatted context string
        context.context_string = self._format_context_for_llm(context)
        return context

    def _format_context_for_llm(self, context: GraphRAGContext) -> str:
        """Format graph context into LLM-friendly string."""
        parts: List[str] = []

        if context.relevant_entities:
            parts.append("## Related Entities")
            for entity in context.relevant_entities[:5]:
                props_str = ", ".join(f"{k}: {v}" for k, v in list(entity.properties.items())[:5])
                parts.append(f"- {entity.name} (type: {entity.type}, id: {entity.id})")
                if props_str:
                    parts.append(f"  Properties: {props_str}")

        if context.relevant_behaviors:
            parts.append("\n## Recent Behaviors")
            for behavior in context.relevant_behaviors[:10]:
                outcome_str = f" -> {behavior.outcome}" if behavior.outcome else ""
                parts.append(f"- {behavior.action_type}{outcome_str} (confidence: {behavior.confidence:.2f})")

        if context.trust_network:
            parts.append("\n## Trust Relationships")
            for trust in context.trust_network[:5]:
                parts.append(f"- Trust score {trust.score:.2f} (weight: {trust.weight:.2f})")

        if context.related_intents:
            parts.append("\n## Active Intents")
            for intent in context.related_intents[:5]:
                parts.append(f"- {intent.intent_type}: {intent.description} (confidence: {intent.confidence:.2f})")

        return "\n".join(parts) if parts else "No graph context available."

    async def get_context_for_llm(
        self,
        query: str,
        entity_ids: Optional[List[str]] = None,
        include_behaviors: bool = True,
        include_trust: bool = True,
        include_intents: bool = True,
        max_items: int = 10
    ) -> Dict[str, Any]:
        """
        Get graph context formatted for LLM consumption.

        This is the primary GraphRAG integration point.
        """
        context: Dict[str, Any] = {
            "query": query,
            "entities": [],
            "behaviors": [],
            "trust_network": [],
            "intents": [],
            "summary": ""
        }

        if entity_ids:
            # Fetch specified entities
            for eid in entity_ids[:max_items]:
                entity = await self.get_entity(eid)
                if entity:
                    context["entities"].append(entity.model_dump())

                    if include_behaviors:
                        history = await self.get_behavior_history(eid, days=30)
                        context["behaviors"].extend([b.model_dump() for b in history.behaviors[:max_items]])

                    if include_trust:
                        trust_net = await self.get_trust_network(eid)
                        context["trust_network"].extend([t.model_dump() for t in trust_net.trusted_by[:max_items//2]])
                        context["trust_network"].extend([t.model_dump() for t in trust_net.trusts[:max_items//2]])

                    if include_intents:
                        intents_data = await self._repo.get_active_intents(entity_id=eid)
                        context["intents"].extend([i for i in intents_data][:max_items])

        # Generate summary
        context["summary"] = self._generate_context_summary(context)
        return context

    def _generate_context_summary(self, context: Dict[str, Any]) -> str:
        """Generate a concise summary of the graph context."""
        parts: List[str] = []

        if context["entities"]:
            parts.append(f"Entities: {len(context['entities'])}")

        if context["behaviors"]:
            parts.append(f"Behaviors: {len(context['behaviors'])}")

        if context["trust_network"]:
            parts.append(f"Trust relationships: {len(context['trust_network'])}")

        if context["intents"]:
            parts.append(f"Active intents: {len(context['intents'])}")

        return " | ".join(parts) if parts else "No context"

    async def recommend_actions(
        self,
        entity_id: str,
        action_types: Optional[List[str]] = None,
        min_priority: int = 1,
        limit: int = 5
    ) -> List[ActionRecommendation]:
        """Recommend actions for an entity based on graph analysis."""
        recommendations = await self.get_pending_actions(
            entity_id=entity_id,
            min_priority=min_priority,
            limit=limit * 2
        )

        if action_types:
            recommendations = [r for r in recommendations if r.action.action_type in action_types]

        # Sort by confidence and priority
        recommendations.sort(key=lambda r: (r.confidence, r.action.priority), reverse=True)

        return recommendations[:limit]

    async def calculate_entity_metrics(
        self,
        entity_id: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive metrics for an entity."""
        centrality = await self._repo.get_entity_centrality(entity_id)
        trust_net = await self.get_trust_network(entity_id)
        history = await self.get_behavior_history(entity_id)

        # Calculate activity score
        days_active = (history.last_seen - history.first_seen).days if history.last_seen else 0
        activity_score = min(history.total_actions / max(days_active, 1), 1.0)

        # Calculate engagement score
        engagement_score = (centrality["total_degree"] * 0.4 +
                          trust_net.trust_score * 0.4 +
                          activity_score * 0.2)

        return {
            "centrality": centrality,
            "trust_score": trust_net.trust_score,
            "activity_score": activity_score,
            "engagement_score": engagement_score,
            "total_behaviors": history.total_actions,
            "unique_action_types": len(history.action_types),
            "days_active": days_active,
            "first_seen": history.first_seen.isoformat() if history.first_seen else None,
            "last_seen": history.last_seen.isoformat() if history.last_seen else None
        }


# Global service instance
_service: Optional[BehaviorGraphService] = None


def get_graph_service() -> BehaviorGraphService:
    """Get global graph service instance."""
    global _service
    if _service is None:
        _service = BehaviorGraphService()
    return _service


async def init_graph_service() -> BehaviorGraphService:
    """Initialize graph service with database connection."""
    from src.db.database import init_database
    await init_database()
    return get_graph_service()


__all__ = [
    "BehaviorGraphService",
    "get_graph_service",
    "init_graph_service",
]
