"""Behavior Graph Service API Router.

Exposes graph operations via REST API for:
- Entity management
- Behavior tracking
- Trust relationships
- Intent management
- Predictions
- Actions
- GraphRAG context enrichment
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from pydantic import BaseModel, Field

from src.graph.service import BehaviorGraphService, get_graph_service
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

graph_router = APIRouter(prefix="/api/v1/graph", tags=["Behavior Graph"])


# ========== Request Models ==========

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


# ========== Dependency ==========

async def get_service() -> BehaviorGraphService:
    """Dependency for graph service."""
    return get_graph_service()


# ========== Entity Endpoints ==========

@graph_router.post("/entities", response_model=Entity, status_code=status.HTTP_201_CREATED)
async def create_entity(
    request: EntityCreate,
    service: BehaviorGraphService = Depends(get_service)
) -> Entity:
    """Create a new graph entity."""
    try:
        return await service.upsert_entity(
            entity_type=request.type,
            name=request.name,
            description=request.description,
            properties=request.properties
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity: {str(e)}"
        )


@graph_router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: str,
    service: BehaviorGraphService = Depends(get_service)
) -> Entity:
    """Get entity by ID."""
    entity = await service.get_entity(entity_id)
    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    return entity


@graph_router.put("/entities/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: str,
    request: EntityUpdate,
    service: BehaviorGraphService = Depends(get_service)
) -> Entity:
    """Update an entity."""
    # First check existence
    existing = await service.get_entity(entity_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )

    updates = request.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No updates provided"
        )

    # Direct repository call for update (service doesn't expose it directly)
    repo = service._repo
    await repo.update_entity(entity_id, updates)

    return await service.get_entity(entity_id)


@graph_router.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: str,
    service: BehaviorGraphService = Depends(get_service)
) -> None:
    """Delete an entity and all its relationships."""
    success = await service.delete_entity(entity_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )


@graph_router.get("/entities", response_model=List[Entity])
async def list_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    name_contains: Optional[str] = Query(None, description="Filter by name substring"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: BehaviorGraphService = Depends(get_service)
) -> List[Entity]:
    """List entities with optional filters."""
    data = await service._repo.list_entities(
        entity_type=entity_type,
        name_contains=name_contains,
        limit=limit,
        offset=offset
    )
    return [Entity.model_validate(d) for d in data]


@graph_router.get("/entities/{entity_id}/graph", response_model=GraphNode)
async def get_entity_graph(
    entity_id: str,
    depth: int = Query(1, ge=1, le=5),
    edge_types: Optional[List[str]] = Query(None),
    service: BehaviorGraphService = Depends(get_service)
) -> GraphNode:
    """Get entity with its connected graph neighbors."""
    result = await service.get_entity_with_graph(
        entity_id=entity_id,
        depth=depth,
        edge_types=edge_types
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    return result


@graph_router.get("/entities/{entity_id}/neighborhood", response_model=NeighborhoodResult)
async def get_neighborhood(
    entity_id: str,
    depth: int = Query(1, ge=1, le=5),
    edge_types: Optional[List[str]] = Query(None),
    service: BehaviorGraphService = Depends(get_service)
) -> NeighborhoodResult:
    """Get neighborhood around an entity."""
    try:
        return await service.get_neighborhood(
            entity_id=entity_id,
            max_depth=depth,
            edge_types=edge_types
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ========== Behavior Endpoints ==========

@graph_router.post("/behaviors", response_model=Behavior, status_code=status.HTTP_201_CREATED)
async def record_behavior(
    request: BehaviorCreate,
    service: BehaviorGraphService = Depends(get_service)
) -> Behavior:
    """Record a behavior for an entity."""
    return await service.record_behavior(
        entity_id=request.entity_id,
        action_type=request.action_type,
        context=request.context,
        outcome=request.outcome,
        confidence=request.confidence
    )


@graph_router.get("/behaviors", response_model=List[Behavior])
async def get_behaviors(
    entity_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: BehaviorGraphService = Depends(get_service)
) -> List[Behavior]:
    """Get behaviors with optional filters."""
    data = await service._repo.get_behaviors(
        entity_id=entity_id,
        action_type=action_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    return [Behavior.model_validate(d) for d in data]


@graph_router.get("/entities/{entity_id}/behaviors", response_model=BehaviorHistory)
async def get_entity_behaviors(
    entity_id: str,
    days: int = Query(30, ge=1, le=365),
    service: BehaviorGraphService = Depends(get_service)
) -> BehaviorHistory:
    """Get behavior history for an entity."""
    try:
        return await service.get_behavior_history(entity_id, days=days)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ========== Trust Endpoints ==========

@graph_router.post("/trust", response_model=Trust, status_code=status.HTTP_201_CREATED)
async def set_trust(
    request: TrustCreate,
    service: BehaviorGraphService = Depends(get_service)
) -> Trust:
    """Set or update trust relationship between entities."""
    return await service.update_trust(
        source_id=request.source_id,
        target_id=request.target_id,
        score=request.score,
        weight=request.weight,
        rationale=request.rationale,
        evidence=request.evidence
    )


@graph_router.get("/trust/{source_id}/{target_id}", response_model=Trust)
async def get_trust(
    source_id: str,
    target_id: str,
    service: BehaviorGraphService = Depends(get_service)
) -> Trust:
    """Get trust score between two entities."""
    data = await service._repo.get_trust(source_id, target_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trust relationship not found"
        )
    return Trust.model_validate(data)


@graph_router.get("/entities/{entity_id}/trust", response_model=TrustNetworkResult)
async def get_trust_network(
    entity_id: str,
    direction: str = Query("both", regex="^(incoming|outgoing|both)$"),
    service: BehaviorGraphService = Depends(get_service)
) -> TrustNetworkResult:
    """Get complete trust network for an entity."""
    try:
        return await service.get_trust_network(entity_id, direction=direction)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ========== Intent Endpoints ==========

@graph_router.post("/intents", response_model=Intent, status_code=status.HTTP_201_CREATED)
async def create_intent(
    request: IntentCreate,
    service: BehaviorGraphService = Depends(get_service)
) -> Intent:
    """Create an intent for an entity."""
    return await service.create_intent(
        entity_id=request.entity_id,
        intent_type=request.intent_type,
        description=request.description,
        confidence=request.confidence,
        related_entities=request.related_entities,
        expires_at=request.expires_at
    )


@graph_router.get("/intents/active", response_model=List[Intent])
async def get_active_intents(
    entity_id: Optional[str] = Query(None),
    intent_type: Optional[str] = Query(None),
    service: BehaviorGraphService = Depends(get_service)
) -> List[Intent]:
    """Get active intents."""
    data = await service._repo.get_active_intents(
        entity_id=entity_id,
        intent_type=intent_type
    )
    return [Intent.model_validate(d) for d in data]


@graph_router.patch("/intents/{intent_id}/status")
async def update_intent_status(
    intent_id: str,
    status: str = Query(..., regex="^(active|satisfied|abandoned|expired)$"),
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Update intent status."""
    success = await service._repo.update_intent_status(intent_id, status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intent {intent_id} not found"
        )
    return {"id": intent_id, "status": status}


# ========== Prediction Endpoints ==========

@graph_router.post("/predictions", response_model=Prediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    request: PredictionCreate,
    service: BehaviorGraphService = Depends(get_service)
) -> Prediction:
    """Store a prediction for an entity."""
    return await service.record_prediction(
        entity_id=request.entity_id,
        prediction_type=request.prediction_type,
        value=request.value,
        confidence=request.confidence,
        model_version=request.model_version,
        features=request.features,
        expires_at=request.expires_at
    )


@graph_router.get("/predictions", response_model=PredictionResult)
async def get_predictions(
    entity_id: Optional[str] = Query(None),
    prediction_type: Optional[str] = Query(None),
    validated: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: BehaviorGraphService = Depends(get_service)
) -> PredictionResult:
    """Get predictions with optional filters."""
    return await service.get_predictions(
        entity_id=entity_id,
        prediction_type=prediction_type,
        validated=validated,
        limit=limit
    )


@graph_router.post("/predictions/{prediction_id}/validate")
async def validate_prediction(
    prediction_id: str,
    request: PredictionValidate,
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Validate a prediction with actual outcome."""
    success = await service.validate_prediction(
        prediction_id=prediction_id,
        actual_outcome=request.actual_outcome
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {prediction_id} not found"
        )
    return {"id": prediction_id, "validated": True}


# ========== Action Endpoints ==========

@graph_router.post("/actions", response_model=Action, status_code=status.HTTP_201_CREATED)
async def create_action(
    request: ActionCreate,
    service: BehaviorGraphService = Depends(get_service)
) -> Action:
    """Create an action recommendation."""
    return await service.create_action(
        entity_id=request.entity_id,
        action_type=request.action_type,
        description=request.description,
        parameters=request.parameters,
        priority=request.priority,
        context=request.context,
        reasoning=request.reasoning
    )


@graph_router.get("/actions/pending", response_model=List[ActionRecommendation])
async def get_pending_actions(
    entity_id: Optional[str] = Query(None),
    min_priority: int = Query(1, ge=1, le=10),
    limit: int = Query(50, ge=1, le=200),
    service: BehaviorGraphService = Depends(get_service)
) -> List[ActionRecommendation]:
    """Get pending actions as recommendations."""
    return await service.get_pending_actions(
        entity_id=entity_id,
        min_priority=min_priority,
        limit=limit
    )


@graph_router.patch("/actions/{action_id}/status")
async def update_action_status(
    action_id: str,
    status: str = Query(..., regex="^(pending|approved|executed|rejected|cancelled)$"),
    reasoning: Optional[str] = Query(None),
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Update action status."""
    success = await service._repo.update_action_status(action_id, status, reasoning=reasoning)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Action {action_id} not found"
        )
    return {"id": action_id, "status": status}


# ========== Edge/Link Endpoints ==========

@graph_router.post("/edges", response_model=Edge, status_code=status.HTTP_201_CREATED)
async def link_entities(
    request: LinkEntitiesRequest,
    service: BehaviorGraphService = Depends(get_service)
) -> Edge:
    """Create a directed relationship between entities."""
    return await service.link_entities(
        source_id=request.source_id,
        target_id=request.target_id,
        edge_type=request.edge_type,
        weight=request.weight,
        properties=request.properties
    )


# ========== Search & Analytics Endpoints ==========

@graph_router.post("/entities/similar", response_model=List[SimilarEntity])
async def find_similar_entities(
    request: FindSimilarRequest,
    service: BehaviorGraphService = Depends(get_service)
) -> List[SimilarEntity]:
    """Find entities with similar behavior patterns."""
    try:
        return await service.find_similar_entities(
            entity_id=request.entity_id,
            min_similarity=request.min_similarity,
            limit=request.limit
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@graph_router.get("/entities/{entity_id}/metrics", response_model=Dict[str, Any])
async def get_entity_metrics(
    entity_id: str,
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Calculate comprehensive metrics for an entity."""
    try:
        return await service.calculate_entity_metrics(entity_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@graph_router.get("/stats", response_model=Dict[str, Any])
async def get_graph_stats(
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Get overall graph statistics."""
    return await service.get_graph_statistics()


# ========== GraphRAG Integration Endpoints ==========

@graph_router.post("/rag/enrich", response_model=GraphRAGContext)
async def enrich_query_with_graph(
    request: GraphQueryRequest,
    service: BehaviorGraphService = Depends(get_service)
) -> GraphRAGContext:
    """Enrich a query with relevant graph context for RAG."""
    return await service.enrich_query_with_graph(
        query=request.query,
        entity_id=request.entity_ids[0] if request.entity_ids else None,
        max_entities=request.max_entities,
        max_behaviors=request.max_behaviors,
        max_depth=request.max_depth
    )


@graph_router.post("/rag/context")
async def get_llm_context(
    request: GraphQueryRequest,
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Get graph context formatted for LLM consumption."""
    return await service.get_context_for_llm(
        query=request.query,
        entity_ids=request.entity_ids,
        max_items=request.max_entities
    )


@graph_router.get("/entities/{entity_id}/rag-context")
async def get_entity_rag_context(
    entity_id: str,
    include_behaviors: bool = Query(True),
    include_trust: bool = Query(True),
    include_intents: bool = Query(True),
    max_items: int = Query(10, ge=1, le=50),
    service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Get RAG context for a specific entity."""
    return await service.get_context_for_llm(
        query="",  # Empty query for entity-focused context
        entity_ids=[entity_id],
        include_behaviors=include_behaviors,
        include_trust=include_trust,
        include_intents=include_intents,
        max_items=max_items
    )


# ========== Recommendation Endpoints ==========

@graph_router.get("/entities/{entity_id}/recommendations", response_model=List[ActionRecommendation])
async def recommend_actions(
    entity_id: str,
    action_types: Optional[List[str]] = Query(None),
    min_priority: int = Query(1, ge=1, le=10),
    limit: int = Query(5, ge=1, le=20),
    service: BehaviorGraphService = Depends(get_service)
) -> List[ActionRecommendation]:
    """Recommend actions for an entity based on graph analysis."""
    try:
        return await service.recommend_actions(
            entity_id=entity_id,
            action_types=action_types,
            min_priority=min_priority,
            limit=limit
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


__all__ = ["graph_router"]
