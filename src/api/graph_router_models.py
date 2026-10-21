# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Models and service dependency for Behavior Graph API router."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.graph.service import BehaviorGraphService, get_graph_service
from src.graph.models import (
    Action,
    ActionCreate,
    ActionRecommendation,
    Behavior,
    BehaviorCreate,
    BehaviorHistory,
    Edge,
    Entity,
    EntityCreate,
    EntityUpdate,
    GraphNode,
    GraphRAGContext,
    Intent,
    IntentCreate,
    NeighborhoodResult,
    Prediction,
    PredictionCreate,
    PredictionResult,
    PredictionValidate,
    SimilarEntity,
    Trust,
    TrustCreate,
    TrustNetworkResult,
)


class GraphQueryRequest(BaseModel):
    """Request for graph context enrichment."""

    query: str
    entity_ids: Optional[List[str]] = None
    max_entities: int = Field(5, ge=1, le=50)
    max_behaviors: int = Field(20, ge=1, le=200)
    max_depth: int = Field(2, ge=1, le=5)


class FindSimilarRequest(BaseModel):
    """Request to find similar entities."""

    entity_id: str
    min_similarity: float = Field(0.3, ge=0.0, le=1.0)
    limit: int = Field(10, ge=1, le=100)


class LinkEntitiesRequest(BaseModel):
    """Request to link two entities."""

    source_id: str
    target_id: str
    edge_type: str
    weight: float = Field(1.0, ge=0.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class EntitySearchRequest(BaseModel):
    """Request to search entities."""

    entity_type: Optional[str] = None
    name_contains: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


async def get_service() -> BehaviorGraphService:
    """Dependency for graph service."""
    return get_graph_service()


__all__ = [
    "Action",
    "ActionCreate",
    "ActionRecommendation",
    "Behavior",
    "BehaviorCreate",
    "BehaviorGraphService",
    "BehaviorHistory",
    "Edge",
    "Entity",
    "EntityCreate",
    "EntitySearchRequest",
    "EntityUpdate",
    "FindSimilarRequest",
    "GraphNode",
    "GraphQueryRequest",
    "GraphRAGContext",
    "Intent",
    "IntentCreate",
    "LinkEntitiesRequest",
    "NeighborhoodResult",
    "Prediction",
    "PredictionCreate",
    "PredictionResult",
    "PredictionValidate",
    "SimilarEntity",
    "Trust",
    "TrustCreate",
    "TrustNetworkResult",
    "get_graph_service",
    "get_service",
]
