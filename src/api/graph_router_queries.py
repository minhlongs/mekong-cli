# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Prediction, action, stats, GraphRAG, and recommendation endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.graph_router_models import (
    Action, ActionCreate, ActionRecommendation, BehaviorGraphService,
    GraphQueryRequest, GraphRAGContext, Prediction, PredictionCreate,
    PredictionResult, PredictionValidate, get_service,
)

queries_router = APIRouter()


@queries_router.post("/predictions", response_model=Prediction, status_code=status.HTTP_201_CREATED)
async def create_prediction(
    request: PredictionCreate, service: BehaviorGraphService = Depends(get_service)
) -> Prediction:
    """Store a prediction for an entity."""
    return await service.record_prediction(
        entity_id=request.entity_id, prediction_type=request.prediction_type,
        value=request.value, confidence=request.confidence,
        model_version=request.model_version, features=request.features,
        expires_at=request.expires_at,
    )


@queries_router.get("/predictions", response_model=PredictionResult)
async def get_predictions(
    entity_id: Optional[str] = Query(None),
    prediction_type: Optional[str] = Query(None),
    validated: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: BehaviorGraphService = Depends(get_service),
) -> PredictionResult:
    """Get predictions with optional filters."""
    return await service.get_predictions(
        entity_id=entity_id, prediction_type=prediction_type, validated=validated, limit=limit
    )


@queries_router.post("/predictions/{prediction_id}/validate")
async def validate_prediction(
    prediction_id: str, request: PredictionValidate, service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Validate a prediction with actual outcome."""
    success = await service.validate_prediction(prediction_id=prediction_id, actual_outcome=request.actual_outcome)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Prediction {prediction_id} not found")
    return {"id": prediction_id, "validated": True}


@queries_router.post("/actions", response_model=Action, status_code=status.HTTP_201_CREATED)
async def create_action(
    request: ActionCreate, service: BehaviorGraphService = Depends(get_service)
) -> Action:
    """Create an action recommendation."""
    return await service.create_action(
        entity_id=request.entity_id, action_type=request.action_type,
        description=request.description, parameters=request.parameters,
        priority=request.priority, context=request.context, reasoning=request.reasoning,
    )


@queries_router.get("/actions/pending", response_model=List[ActionRecommendation])
async def get_pending_actions(
    entity_id: Optional[str] = Query(None),
    min_priority: int = Query(1, ge=1, le=10),
    limit: int = Query(50, ge=1, le=200),
    service: BehaviorGraphService = Depends(get_service),
) -> List[ActionRecommendation]:
    """Get pending actions as recommendations."""
    return await service.get_pending_actions(entity_id=entity_id, min_priority=min_priority, limit=limit)


@queries_router.patch("/actions/{action_id}/status")
async def update_action_status(
    action_id: str,
    status: str = Query(..., regex="^(pending|approved|executed|rejected|cancelled)$"),
    reasoning: Optional[str] = Query(None),
    service: BehaviorGraphService = Depends(get_service),
) -> Dict[str, Any]:
    """Update action status."""
    success = await service._repo.update_action_status(action_id, status, reasoning=reasoning)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Action {action_id} not found")
    return {"id": action_id, "status": status}


@queries_router.get("/stats", response_model=Dict[str, Any])
async def get_graph_stats(service: BehaviorGraphService = Depends(get_service)) -> Dict[str, Any]:
    """Get overall graph statistics."""
    return await service.get_graph_statistics()


@queries_router.post("/rag/enrich", response_model=GraphRAGContext)
async def enrich_query_with_graph(
    request: GraphQueryRequest, service: BehaviorGraphService = Depends(get_service)
) -> GraphRAGContext:
    """Enrich a query with relevant graph context for RAG."""
    return await service.enrich_query_with_graph(
        query=request.query, entity_id=request.entity_ids[0] if request.entity_ids else None,
        max_entities=request.max_entities, max_behaviors=request.max_behaviors, max_depth=request.max_depth,
    )


@queries_router.post("/rag/context")
async def get_llm_context(
    request: GraphQueryRequest, service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Get graph context formatted for LLM consumption."""
    return await service.get_context_for_llm(
        query=request.query, entity_ids=request.entity_ids, max_items=request.max_entities
    )


@queries_router.get("/entities/{entity_id}/rag-context")
async def get_entity_rag_context(
    entity_id: str,
    include_behaviors: bool = Query(True),
    include_trust: bool = Query(True),
    include_intents: bool = Query(True),
    max_items: int = Query(10, ge=1, le=50),
    service: BehaviorGraphService = Depends(get_service),
) -> Dict[str, Any]:
    """Get RAG context for a specific entity."""
    return await service.get_context_for_llm(
        query="", entity_ids=[entity_id], include_behaviors=include_behaviors,
        include_trust=include_trust, include_intents=include_intents, max_items=max_items,
    )


@queries_router.get("/entities/{entity_id}/recommendations", response_model=List[ActionRecommendation])
async def recommend_actions(
    entity_id: str,
    action_types: Optional[List[str]] = Query(None),
    min_priority: int = Query(1, ge=1, le=10),
    limit: int = Query(5, ge=1, le=20),
    service: BehaviorGraphService = Depends(get_service),
) -> List[ActionRecommendation]:
    """Recommend actions for an entity based on graph analysis."""
    try:
        return await service.recommend_actions(
            entity_id=entity_id, action_types=action_types, min_priority=min_priority, limit=limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

