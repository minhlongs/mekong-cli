# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior, trust, intent, and edge endpoints for Behavior Graph API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.graph_router_models import (
    Behavior,
    BehaviorCreate,
    BehaviorGraphService,
    BehaviorHistory,
    Edge,
    Intent,
    IntentCreate,
    LinkEntitiesRequest,
    Trust,
    TrustCreate,
    TrustNetworkResult,
    get_service,
)

mutations_router = APIRouter()


@mutations_router.post("/behaviors", response_model=Behavior, status_code=status.HTTP_201_CREATED)
async def record_behavior(
    request: BehaviorCreate,
    service: BehaviorGraphService = Depends(get_service),
) -> Behavior:
    """Record a behavior for an entity."""
    return await service.record_behavior(
        entity_id=request.entity_id,
        action_type=request.action_type,
        context=request.context,
        outcome=request.outcome,
        confidence=request.confidence,
    )


@mutations_router.get("/behaviors", response_model=List[Behavior])
async def get_behaviors(
    entity_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    service: BehaviorGraphService = Depends(get_service),
) -> List[Behavior]:
    """Get behaviors with optional filters."""
    data = await service._repo.get_behaviors(
        entity_id=entity_id,
        action_type=action_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
    )
    return [Behavior.model_validate(d) for d in data]


@mutations_router.get("/entities/{entity_id}/behaviors", response_model=BehaviorHistory)
async def get_entity_behaviors(
    entity_id: str,
    days: int = Query(30, ge=1, le=365),
    service: BehaviorGraphService = Depends(get_service),
) -> BehaviorHistory:
    """Get behavior history for an entity."""
    try:
        return await service.get_behavior_history(entity_id, days=days)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@mutations_router.post("/trust", response_model=Trust, status_code=status.HTTP_201_CREATED)
async def set_trust(
    request: TrustCreate,
    service: BehaviorGraphService = Depends(get_service),
) -> Trust:
    """Set or update trust relationship between entities."""
    return await service.update_trust(
        source_id=request.source_id,
        target_id=request.target_id,
        score=request.score,
        weight=request.weight,
        rationale=request.rationale,
        evidence=request.evidence,
    )


@mutations_router.get("/trust/{source_id}/{target_id}", response_model=Trust)
async def get_trust(
    source_id: str,
    target_id: str,
    service: BehaviorGraphService = Depends(get_service),
) -> Trust:
    """Get trust score between two entities."""
    data = await service._repo.get_trust(source_id, target_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trust relationship not found",
        )
    return Trust.model_validate(data)


@mutations_router.get("/entities/{entity_id}/trust", response_model=TrustNetworkResult)
async def get_trust_network(
    entity_id: str,
    direction: str = Query("both", regex="^(incoming|outgoing|both)$"),
    service: BehaviorGraphService = Depends(get_service),
) -> TrustNetworkResult:
    """Get complete trust network for an entity."""
    try:
        return await service.get_trust_network(entity_id, direction=direction)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@mutations_router.post("/intents", response_model=Intent, status_code=status.HTTP_201_CREATED)
async def create_intent(
    request: IntentCreate,
    service: BehaviorGraphService = Depends(get_service),
) -> Intent:
    """Create an intent for an entity."""
    return await service.create_intent(
        entity_id=request.entity_id,
        intent_type=request.intent_type,
        description=request.description,
        confidence=request.confidence,
        related_entities=request.related_entities,
        expires_at=request.expires_at,
    )


@mutations_router.get("/intents/active", response_model=List[Intent])
async def get_active_intents(
    entity_id: Optional[str] = Query(None),
    intent_type: Optional[str] = Query(None),
    service: BehaviorGraphService = Depends(get_service),
) -> List[Intent]:
    """Get active intents."""
    data = await service._repo.get_active_intents(
        entity_id=entity_id,
        intent_type=intent_type,
    )
    return [Intent.model_validate(d) for d in data]


@mutations_router.patch("/intents/{intent_id}/status")
async def update_intent_status(
    intent_id: str,
    status: str = Query(..., regex="^(active|satisfied|abandoned|expired)$"),
    service: BehaviorGraphService = Depends(get_service),
) -> Dict[str, Any]:
    """Update intent status."""
    success = await service._repo.update_intent_status(intent_id, status)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Intent {intent_id} not found",
        )
    return {"id": intent_id, "status": status}


@mutations_router.post("/edges", response_model=Edge, status_code=status.HTTP_201_CREATED)
async def link_entities(
    request: LinkEntitiesRequest,
    service: BehaviorGraphService = Depends(get_service),
) -> Edge:
    """Create a directed relationship between entities."""
    return await service.link_entities(
        source_id=request.source_id,
        target_id=request.target_id,
        edge_type=request.edge_type,
        weight=request.weight,
        properties=request.properties,
    )
