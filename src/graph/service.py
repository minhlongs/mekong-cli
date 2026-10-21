# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior Graph Service - Business logic layer for graph operations."""

from typing import Optional

from src.graph.models import (
    Action,
    ActionRecommendation,
    Behavior,
    BehaviorHistory,
    Edge,
    Entity,
    GraphNode,
    GraphRAGContext,
    Intent,
    NeighborhoodResult,
    Prediction,
    PredictionResult,
    SimilarEntity,
    Trust,
    TrustNetworkResult,
)
from src.graph.repository import GraphRepository, get_graph_repository
from src.graph.service_ingest import GraphIngestServiceMixin
from src.graph.service_queries import GraphQueryServiceMixin
from src.graph.service_rag import GraphRagServiceMixin


class BehaviorGraphService(
    GraphIngestServiceMixin,
    GraphQueryServiceMixin,
    GraphRagServiceMixin,
):
    """Service layer for behavior graph operations."""

    def __init__(self, repository: Optional[GraphRepository] = None) -> None:
        self._repo = repository or get_graph_repository()


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
    "Entity",
    "Behavior",
    "Trust",
    "Intent",
    "Prediction",
    "Action",
    "Edge",
    "GraphNode",
    "NeighborhoodResult",
    "TrustNetworkResult",
    "BehaviorHistory",
    "SimilarEntity",
    "PredictionResult",
    "ActionRecommendation",
    "GraphRAGContext",
]
