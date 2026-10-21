# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Recipe Registry for RaaS — publish, search, and clone public recipes."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.raas.auth import TenantContext, get_tenant_context
from src.raas.registry_store import (
    _DB_PATH,
    _DDL,
    RECIPE_CATEGORIES,
    PublishRecipeRequest,
    RecipeEntry,
    RecipeRegistry,
)

# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_registry: Optional[RecipeRegistry] = None


def _get_registry() -> RecipeRegistry:
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = RecipeRegistry()
    return _registry


# ---------------------------------------------------------------------------
# FastAPI Router
# ---------------------------------------------------------------------------

raas_registry_router = APIRouter(tags=["recipes"])


@raas_registry_router.get("/recipes")
def browse_recipes(
    query: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[dict]:
    """GET /recipes — browse public recipes (query, category, limit, offset)."""
    try:
        entries = _get_registry().search(query=query, category=category, limit=limit, offset=offset)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [vars(e) for e in entries]


@raas_registry_router.get("/recipes/{recipe_id}")
def get_recipe(recipe_id: str) -> dict:
    """GET /recipes/{recipe_id} — return full recipe detail."""
    try:
        entry = _get_registry().get(recipe_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Recipe '{recipe_id}' not found.")
    return vars(entry)


@raas_registry_router.post("/recipes", status_code=201)
def publish_recipe(
    body: PublishRecipeRequest,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    """POST /recipes — publish a recipe (auth required)."""
    try:
        entry = _get_registry().publish(
            tenant_id=tenant.tenant_id,
            name=body.name,
            description=body.description,
            category=body.category,
            content=body.content,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return vars(entry)


@raas_registry_router.post("/recipes/{recipe_id}/clone", status_code=201)
def clone_recipe(
    recipe_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
) -> dict:
    """POST /recipes/{recipe_id}/clone — clone a public recipe (auth required)."""
    try:
        entry = _get_registry().clone(recipe_id=recipe_id, tenant_id=tenant.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return vars(entry)


__all__ = [
    "RECIPE_CATEGORIES",
    "_DB_PATH",
    "_DDL",
    "RecipeEntry",
    "PublishRecipeRequest",
    "RecipeRegistry",
    "_registry",
    "_get_registry",
    "raas_registry_router",
    "browse_recipes",
    "get_recipe",
    "publish_recipe",
    "clone_recipe",
]
