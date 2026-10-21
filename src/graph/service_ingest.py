# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior Graph Service - Ingest Operations Mixin."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.graph.models import Action, Behavior, Edge, Entity, Intent, Prediction, Trust


class GraphIngestServiceMixin:
    """Mixin for ingesting entities, behaviors, trust, intents, predictions, and actions."""

    _repo: Any

    async def upsert_entity(
        self,
        entity_type: str,
        name: str,
        entity_id: Optional[str] = None,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Entity:
        """Create or update an entity."""
        data = await self._repo.create_entity(
            entity_type=entity_type,
            name=name,
            entity_id=entity_id,
            description=description,
            properties=properties,
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
        behavior_id: Optional[str] = None,
    ) -> Behavior:
        """Record a behavior for an entity."""
        data = await self._repo.record_behavior(
            entity_id=entity_id,
            action_type=action_type,
            behavior_id=behavior_id,
            context=context,
            outcome=outcome,
            confidence=confidence,
        )
        return Behavior.model_validate(data)

    async def update_trust(
        self,
        source_id: str,
        target_id: str,
        score: float,
        weight: float = 1.0,
        rationale: Optional[str] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Trust:
        """Set or update trust between entities."""
        data = await self._repo.set_trust(
            source_id=source_id,
            target_id=target_id,
            score=score,
            weight=weight,
            rationale=rationale,
            evidence=evidence,
        )
        return Trust.model_validate(data)

    async def create_intent(
        self,
        entity_id: str,
        intent_type: str,
        description: str,
        confidence: float = 1.0,
        related_entities: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None,
    ) -> Intent:
        """Create an intent for an entity."""
        data = await self._repo.create_intent(
            entity_id=entity_id,
            intent_type=intent_type,
            description=description,
            confidence=confidence,
            related_entities=related_entities,
            expires_at=expires_at,
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
        expires_at: Optional[datetime] = None,
    ) -> Prediction:
        """Store a prediction."""
        data = await self._repo.create_prediction(
            entity_id=entity_id,
            prediction_type=prediction_type,
            value=value,
            confidence=confidence,
            model_version=model_version,
            features=features,
            expires_at=expires_at,
        )
        return Prediction.model_validate(data)

    async def validate_prediction(
        self,
        prediction_id: str,
        actual_outcome: Any,
        notes: Optional[str] = None,
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
        reasoning: Optional[str] = None,
    ) -> Action:
        """Create an action recommendation."""
        data = await self._repo.create_action(
            entity_id=entity_id,
            action_type=action_type,
            description=description,
            parameters=parameters,
            priority=priority,
            context=context,
            reasoning=reasoning,
        )
        return Action.model_validate(data)

    async def link_entities(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Edge:
        """Create a directed relationship between entities."""
        data = await self._repo.create_edge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            properties=properties,
        )
        return Edge.model_validate(data)
