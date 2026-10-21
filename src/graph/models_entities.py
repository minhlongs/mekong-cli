# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Domain Entity Models for Behavior Graph Service."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

EntityId = str
EntityType = str
EdgeType = str


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
