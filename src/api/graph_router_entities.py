# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Entity CRUD, graph traversal, similarity, and metrics endpoints."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.graph_router_models import (
    BehaviorGraphService, Entity, EntityCreate, EntityUpdate,
    FindSimilarRequest, GraphNode, NeighborhoodResult, SimilarEntity, get_service,
)

entity_router = APIRouter()


@entity_router.post("/entities", response_model=Entity, status_code=status.HTTP_201_CREATED)
async def create_entity(
    request: EntityCreate, service: BehaviorGraphService = Depends(get_service)
) -> Entity:
    """Create a new graph entity."""
    try:
        return await service.upsert_entity(
            entity_type=request.type, name=request.name,
            description=request.description, properties=request.properties,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create entity: {str(e)}",
        )


@entity_router.get("/entities/{entity_id}", response_model=Entity)
async def get_entity(
    entity_id: str, service: BehaviorGraphService = Depends(get_service)
) -> Entity:
    """Get entity by ID."""
    entity = await service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")
    return entity


@entity_router.put("/entities/{entity_id}", response_model=Entity)
async def update_entity(
    entity_id: str, request: EntityUpdate, service: BehaviorGraphService = Depends(get_service)
) -> Entity:
    """Update an entity."""
    existing = await service.get_entity(entity_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")

    updates = request.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No updates provided")

    await service._repo.update_entity(entity_id, updates)
    return await service.get_entity(entity_id)


@entity_router.delete("/entities/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: str, service: BehaviorGraphService = Depends(get_service)
) -> None:
    """Delete an entity and all its relationships."""
    if not await service.delete_entity(entity_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")


@entity_router.get("/entities", response_model=List[Entity])
async def list_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    name_contains: Optional[str] = Query(None, description="Filter by name substring"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    service: BehaviorGraphService = Depends(get_service),
) -> List[Entity]:
    """List entities with optional filters."""
    data = await service._repo.list_entities(
        entity_type=entity_type, name_contains=name_contains, limit=limit, offset=offset
    )
    return [Entity.model_validate(d) for d in data]


@entity_router.get("/entities/{entity_id}/graph", response_model=GraphNode)
async def get_entity_graph(
    entity_id: str,
    depth: int = Query(1, ge=1, le=5),
    edge_types: Optional[List[str]] = Query(None),
    service: BehaviorGraphService = Depends(get_service),
) -> GraphNode:
    """Get entity with its connected graph neighbors."""
    result = await service.get_entity_with_graph(entity_id=entity_id, depth=depth, edge_types=edge_types)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Entity {entity_id} not found")
    return result


@entity_router.get("/entities/{entity_id}/neighborhood", response_model=NeighborhoodResult)
async def get_neighborhood(
    entity_id: str,
    depth: int = Query(1, ge=1, le=5),
    edge_types: Optional[List[str]] = Query(None),
    service: BehaviorGraphService = Depends(get_service),
) -> NeighborhoodResult:
    """Get neighborhood around an entity."""
    try:
        return await service.get_neighborhood(entity_id=entity_id, max_depth=depth, edge_types=edge_types)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@entity_router.post("/entities/similar", response_model=List[SimilarEntity])
async def find_similar_entities(
    request: FindSimilarRequest, service: BehaviorGraphService = Depends(get_service)
) -> List[SimilarEntity]:
    """Find entities with similar behavior patterns."""
    try:
        return await service.find_similar_entities(
            entity_id=request.entity_id, min_similarity=request.min_similarity, limit=request.limit
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@entity_router.get("/entities/{entity_id}/metrics", response_model=Dict[str, Any])
async def get_entity_metrics(
    entity_id: str, service: BehaviorGraphService = Depends(get_service)
) -> Dict[str, Any]:
    """Calculate comprehensive metrics for an entity."""
    try:
        return await service.calculate_entity_metrics(entity_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

