# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Behavior Graph Service API Router facade."""

from fastapi import APIRouter

from src.api.graph_router_models import (  # noqa: F401
    Action,
    ActionCreate,
    ActionRecommendation,
    Behavior,
    BehaviorCreate,
    BehaviorGraphService,
    BehaviorHistory,
    Edge,
    Entity,
    EntityCreate,
    EntitySearchRequest,
    EntityUpdate,
    FindSimilarRequest,
    GraphNode,
    GraphQueryRequest,
    GraphRAGContext,
    Intent,
    IntentCreate,
    LinkEntitiesRequest,
    NeighborhoodResult,
    Prediction,
    PredictionCreate,
    PredictionResult,
    PredictionValidate,
    SimilarEntity,
    Trust,
    TrustCreate,
    TrustNetworkResult,
    get_graph_service,
    get_service,
)
from src.api.graph_router_entities import (  # noqa: F401
    create_entity,
    delete_entity,
    entity_router,
    find_similar_entities,
    get_entity,
    get_entity_graph,
    get_entity_metrics,
    get_neighborhood,
    list_entities,
    update_entity,
)
from src.api.graph_router_mutations import (  # noqa: F401
    create_intent,
    get_active_intents,
    get_behaviors,
    get_entity_behaviors,
    get_trust,
    get_trust_network,
    link_entities,
    mutations_router,
    record_behavior,
    set_trust,
    update_intent_status,
)
from src.api.graph_router_queries import (  # noqa: F401
    create_action,
    create_prediction,
    enrich_query_with_graph,
    get_entity_rag_context,
    get_graph_stats,
    get_llm_context,
    get_pending_actions,
    get_predictions,
    queries_router,
    recommend_actions,
    update_action_status,
    validate_prediction,
)

graph_router = APIRouter(prefix="/api/v1/graph", tags=["Behavior Graph"])
graph_router.include_router(entity_router)
graph_router.include_router(mutations_router)
graph_router.include_router(queries_router)

__all__ = ["graph_router"]
