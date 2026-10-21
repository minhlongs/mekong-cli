# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Action, Edge, and Query Response Models for Behavior Graph Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.graph.models_entities import (
    Behavior,
    EdgeType,
    Entity,
    EntityId,
    Intent,
    Prediction,
    Trust,
)


class Action(BaseModel):
    """Recommended or executed action."""
    model_config = ConfigDict(from_attributes=True)

    id: EntityId = Field(..., description="Unique action ID")
    entity_id: EntityId = Field(..., description="Entity to perform/recommended")
    action_type: str = Field(..., description="Type of action")
    description: str = Field(..., description="Action description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")
    priority: int = Field(1, ge=1, le=10, description="Priority (1-10)")
    status: str = Field("pending", description="pending, approved, executed, rejected, cancelled")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context for action")
    reasoning: Optional[str] = Field(None, description="Why this action was chosen")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = Field(None)


class ActionCreate(BaseModel):
    """Request model for creating an action."""
    entity_id: EntityId
    action_type: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(1, ge=1, le=10)
    context: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None


class ActionUpdate(BaseModel):
    """Request model for updating action status."""
    status: str
    reasoning: Optional[str] = None
    executed_at: Optional[datetime] = None


class Edge(BaseModel):
    """Directed edge in the graph."""
    model_config = ConfigDict(from_attributes=True)

    source_id: EntityId = Field(..., description="Source entity")
    target_id: EntityId = Field(..., description="Target entity")
    edge_type: EdgeType = Field(..., description="Type of relationship")
    weight: float = Field(1.0, ge=0.0, description="Edge weight")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Edge metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EdgeCreate(BaseModel):
    """Request model for creating an edge."""
    source_id: EntityId
    target_id: EntityId
    edge_type: EdgeType
    weight: float = Field(1.0, ge=0.0)
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphNode(BaseModel):
    """Node with its connected edges."""
    entity: Entity
    edges: List[Edge] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict, description="Computed metrics")


class GraphTraversal(BaseModel):
    """Result of a graph traversal."""
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[Edge] = Field(default_factory=list)
    path_length: int = Field(0, description="Path length traversed")
    total_weight: float = Field(0.0, description="Sum of edge weights")


class NeighborhoodResult(BaseModel):
    """Neighborhood query result."""
    center_entity: Entity
    neighbors: List[GraphNode] = Field(default_factory=list)
    depth: int = Field(1, description="Traversal depth")
    total_nodes: int = Field(0)


class TrustNetworkResult(BaseModel):
    """Trust network query result."""
    entity: Entity
    trusted_by: List[GraphNode] = Field(default_factory=list, description="Entities that trust this")
    trusts: List[GraphNode] = Field(default_factory=list, description="Entities this trusts")
    trust_score: float = Field(0.0, description="Aggregated trust score")


class BehaviorHistory(BaseModel):
    """Behavior history for an entity."""
    entity: Entity
    behaviors: List[Behavior] = Field(default_factory=list)
    action_types: List[str] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    total_actions: int = Field(0)


class SimilarEntity(BaseModel):
    """Similar entity result."""
    entity: Entity
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    shared_behaviors: List[str] = Field(default_factory=list)
    shared_intents: List[str] = Field(default_factory=list)


class PredictionResult(BaseModel):
    """Prediction query result."""
    predictions: List[Prediction] = Field(default_factory=list)
    entity: Optional[Entity] = None
    prediction_type: Optional[str] = None


class ActionRecommendation(BaseModel):
    """Recommended action result."""
    action: Action
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    supporting_evidence: List[Dict[str, Any]] = Field(default_factory=list)


class GraphRAGContext(BaseModel):
    """Graph-enhanced context for LLM."""
    query: str
    relevant_entities: List[Entity] = Field(default_factory=list)
    relevant_behaviors: List[Behavior] = Field(default_factory=list)
    trust_network: List[Trust] = Field(default_factory=list)
    related_intents: List[Intent] = Field(default_factory=list)
    similar_patterns: List[Dict[str, Any]] = Field(default_factory=list)
    context_string: str = Field("", description="Formatted context string for LLM prompt")
