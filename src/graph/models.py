# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Pydantic models for Behavior Graph Service.

Type-safe request/response models for the graph API.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# ========== Core Types ==========

EntityId = str  # UUID or string identifier
EntityType = str  # "user", "agent", "tool", "concept", "action", "intent", "prediction"

EdgeType = str  # "performs", "trusts", "has_intent", "predicts", "recommends", "related_to"


# ========== Entity Models ==========

class Entity(BaseModel):
    """A node in the behavior graph."""
    model_config = ConfigDict(from_attributes=True)

    id: EntityId = Field(..., description="Unique entity identifier")
    type: EntityType = Field(..., description="Entity type category")
    name: str = Field(..., description="Human-readable name")
    description: Optional[str] = Field(None, description="Entity description")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Type-specific attributes")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EntityCreate(BaseModel):
    """Request model for creating an entity."""
    type: EntityType
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class EntityUpdate(BaseModel):
    """Request model for updating an entity."""
    name: Optional[str] = None
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


# ========== Behavior Models ==========

class Behavior(BaseModel):
    """Recorded behavior/action performed by an entity."""
    model_config = ConfigDict(from_attributes=True)

    id: EntityId = Field(..., description="Unique behavior ID")
    entity_id: EntityId = Field(..., description="Entity that performed the behavior")
    action_type: str = Field(..., description="Type of action performed")
    context: Dict[str, Any] = Field(default_factory=dict, description="Contextual data")
    outcome: Optional[Dict[str, Any]] = Field(None, description="Result of the behavior")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence in this behavior record")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BehaviorCreate(BaseModel):
    """Request model for recording behavior."""
    entity_id: EntityId
    action_type: str
    context: Dict[str, Any] = Field(default_factory=dict)
    outcome: Optional[Dict[str, Any]] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ========== Trust Models ==========

class Trust(BaseModel):
    """Trust relationship between entities."""
    model_config = ConfigDict(from_attributes=True)

    id: EntityId = Field(..., description="Unique trust record ID")
    source_id: EntityId = Field(..., description="Entity that trusts")
    target_id: EntityId = Field(..., description="Entity that is trusted")
    score: float = Field(..., ge=-1.0, le=1.0, description="Trust score (-1 to 1)")
    weight: float = Field(1.0, ge=0.0, description="Weight of this trust edge")
    rationale: Optional[str] = Field(None, description="Reason for trust score")
    evidence: List[Dict[str, Any]] = Field(default_factory=list, description="Supporting evidence")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TrustCreate(BaseModel):
    """Request model for setting trust."""
    source_id: EntityId
    target_id: EntityId
    score: float = Field(..., ge=-1.0, le=1.0)
    weight: float = Field(1.0, ge=0.0)
    rationale: Optional[str] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


class TrustUpdate(BaseModel):
    """Request model for updating trust."""
    score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    weight: Optional[float] = Field(None, ge=0.0)
    rationale: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = None


# ========== Intent Models ==========

class Intent(BaseModel):
    """Declared or inferred intent of an entity."""
    model_config = ConfigDict(from_attributes=True)

    id: EntityId = Field(..., description="Unique intent ID")
    entity_id: EntityId = Field(..., description="Entity with this intent")
    intent_type: str = Field(..., description="Category of intent")
    description: str = Field(..., description="Intent description")
    confidence: float = Field(..., ge=0.0, le=1.0)
    status: str = Field("active", description="active, satisfied, abandoned, expired")
    related_entities: List[EntityId] = Field(default_factory=list, description="Related entity IDs")
    expires_at: Optional[datetime] = Field(None, description="When intent expires")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class IntentCreate(BaseModel):
    """Request model for creating an intent."""
    entity_id: EntityId
    intent_type: str
    description: str
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    related_entities: List[EntityId] = Field(default_factory=list)
    expires_at: Optional[datetime] = None


# ========== Prediction Models ==========

class Prediction(BaseModel):
    """ML prediction about entity behavior."""
    model_config = ConfigDict(from_attributes=True)

    id: EntityId = Field(..., description="Unique prediction ID")
    entity_id: EntityId = Field(..., description="Entity being predicted")
    prediction_type: str = Field(..., description="Type of prediction")
    value: Any = Field(..., description="Predicted value/outcome")
    confidence: float = Field(..., ge=0.0, le=1.0)
    features: Dict[str, Any] = Field(default_factory=dict, description="Features used for prediction")
    model_version: str = Field(..., description="Version of prediction model")
    validated: bool = Field(False, description="Whether prediction was validated")
    actual_outcome: Optional[Any] = Field(None, description="Actual outcome when known")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(None, description="When prediction expires")


class PredictionCreate(BaseModel):
    """Request model for creating a prediction."""
    entity_id: EntityId
    prediction_type: str
    value: Any
    confidence: float = Field(..., ge=0.0, le=1.0)
    features: Dict[str, Any] = Field(default_factory=dict)
    model_version: str
    expires_at: Optional[datetime] = None


class PredictionValidate(BaseModel):
    """Request model for validating a prediction."""
    actual_outcome: Any
    notes: Optional[str] = None


# ========== Action Models ==========

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


# ========== Graph Edge Models ==========

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


# ========== Query Response Models ==========

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


__all__ = [
    "EntityId",
    "EntityType",
    "EdgeType",
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
]
