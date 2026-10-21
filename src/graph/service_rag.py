# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior Graph Service - GraphRAG and Recommendations Mixin."""

from typing import Any, Dict, List, Optional

from src.graph.models import ActionRecommendation, Entity, GraphRAGContext, Intent


class GraphRagServiceMixin:
    """Mixin for GraphRAG context generation, recommendations, and entity metrics."""

    _repo: Any

    async def enrich_query_with_graph(
        self,
        query: str,
        entity_id: Optional[str] = None,
        max_entities: int = 5,
        max_behaviors: int = 20,
        max_depth: int = 2,
    ) -> GraphRAGContext:
        """Enrich a query with relevant graph context for RAG."""
        context = GraphRAGContext(query=query)

        if entity_id:
            entity = await self.get_entity(entity_id)  # type: ignore[attr-defined]
            if entity:
                context.relevant_entities.append(entity)
                neighborhood = await self.get_neighborhood(entity_id, max_depth=max_depth)  # type: ignore[attr-defined]
                context.relevant_entities.extend(
                    [n.entity for n in neighborhood.neighbors[: max_entities - 1]]
                )
                history = await self.get_behavior_history(entity_id, days=30)  # type: ignore[attr-defined]
                context.relevant_behaviors = history.behaviors[:max_behaviors]
                intents_data = await self._repo.get_active_intents(entity_id=entity_id)
                context.related_intents = [Intent.model_validate(i) for i in intents_data]
                trust_net = await self.get_trust_network(entity_id)  # type: ignore[attr-defined]
                context.trust_network = trust_net.trusted_by[:10] + trust_net.trusts[:10]
        else:
            entities_data = await self._repo.list_entities(limit=max_entities)
            context.relevant_entities = [Entity.model_validate(e) for e in entities_data]

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
                parts.append(
                    f"- {intent.intent_type}: {intent.description} (confidence: {intent.confidence:.2f})"
                )

        return "\n".join(parts) if parts else "No graph context available."

    async def get_context_for_llm(
        self,
        query: str,
        entity_ids: Optional[List[str]] = None,
        include_behaviors: bool = True,
        include_trust: bool = True,
        include_intents: bool = True,
        max_items: int = 10,
    ) -> Dict[str, Any]:
        """Get graph context formatted for LLM consumption."""
        context: Dict[str, Any] = {
            "query": query,
            "entities": [],
            "behaviors": [],
            "trust_network": [],
            "intents": [],
            "summary": "",
        }
        if entity_ids:
            for eid in entity_ids[:max_items]:
                entity = await self.get_entity(eid)  # type: ignore[attr-defined]
                if entity:
                    context["entities"].append(entity.model_dump())
                    if include_behaviors:
                        history = await self.get_behavior_history(eid, days=30)  # type: ignore[attr-defined]
                        context["behaviors"].extend(
                            [b.model_dump() for b in history.behaviors[:max_items]]
                        )
                    if include_trust:
                        trust_net = await self.get_trust_network(eid)  # type: ignore[attr-defined]
                        context["trust_network"].extend(
                            [t.model_dump() for t in trust_net.trusted_by[: max_items // 2]]
                        )
                        context["trust_network"].extend(
                            [t.model_dump() for t in trust_net.trusts[: max_items // 2]]
                        )
                    if include_intents:
                        intents_data = await self._repo.get_active_intents(entity_id=eid)
                        context["intents"].extend([i for i in intents_data][:max_items])

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
        limit: int = 5,
    ) -> List[ActionRecommendation]:
        """Recommend actions for an entity based on graph analysis."""
        recommendations = await self.get_pending_actions(  # type: ignore[attr-defined]
            entity_id=entity_id, min_priority=min_priority, limit=limit * 2
        )
        if action_types:
            recommendations = [r for r in recommendations if r.action.action_type in action_types]
        recommendations.sort(key=lambda r: (r.confidence, r.action.priority), reverse=True)
        return recommendations[:limit]

    async def calculate_entity_metrics(self, entity_id: str) -> Dict[str, Any]:
        """Calculate comprehensive metrics for an entity."""
        centrality = await self._repo.get_entity_centrality(entity_id)
        trust_net = await self.get_trust_network(entity_id)  # type: ignore[attr-defined]
        history = await self.get_behavior_history(entity_id)  # type: ignore[attr-defined]

        days_active = (history.last_seen - history.first_seen).days if history.last_seen else 0
        activity_score = min(history.total_actions / max(days_active, 1), 1.0)
        engagement_score = (
            centrality["total_degree"] * 0.4 + trust_net.trust_score * 0.4 + activity_score * 0.2
        )

        return {
            "centrality": centrality,
            "trust_score": trust_net.trust_score,
            "activity_score": activity_score,
            "engagement_score": engagement_score,
            "total_behaviors": history.total_actions,
            "unique_action_types": len(history.action_types),
            "days_active": days_active,
            "first_seen": history.first_seen.isoformat() if history.first_seen else None,
            "last_seen": history.last_seen.isoformat() if history.last_seen else None,
        }
