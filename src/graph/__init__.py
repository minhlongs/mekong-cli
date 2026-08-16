# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Behavior Graph Service - GraphRAG integration for AI context.

Provides:
- Entity relationship graph (users, agents, tools, concepts)
- Behavior tracking and analysis
- Trust score computation
- Intent inference
- Prediction storage
- Action recommendation

Storage: PostgreSQL JSONB (adjacency list pattern)
"""

from src.graph.models import (
    EntityId,
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
    GraphTraversal,
    NeighborhoodResult,
    TrustNetworkResult,
    BehaviorHistory,
    SimilarEntity,
    PredictionResult,
    ActionRecommendation,
    GraphRAGContext,
)
from src.graph.service import BehaviorGraphService, get_graph_service, init_graph_service
from src.graph.repository import GraphRepository, get_graph_repository, init_graph_repository
from src.graph.schema import SCHEMA_SQL, MIGRATION_001

__all__ = [
    "EntityId",
    "Entity",
    "EntityCreate",
    "EntityUpdate",
    "Behavior",
    "BehaviorCreate",
    "Trust",
    "TrustCreate",
    "TrustUpdate",
    "Intent",
    "IntentCreate",
    "Prediction",
    "PredictionCreate",
    "PredictionValidate",
    "Action",
    "ActionCreate",
    "ActionUpdate",
    "Edge",
    "EdgeCreate",
    "GraphNode",
    "GraphTraversal",
    "NeighborhoodResult",
    "TrustNetworkResult",
    "BehaviorHistory",
    "SimilarEntity",
    "PredictionResult",
    "ActionRecommendation",
    "GraphRAGContext",
    "BehaviorGraphService",
    "get_graph_service",
    "init_graph_service",
    "GraphRepository",
    "get_graph_repository",
    "init_graph_repository",
    "SCHEMA_SQL",
    "MIGRATION_001",
]
