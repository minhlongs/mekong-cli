# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""NLU, recipe generation, validation, and AGI proxy router for Mekong Gateway."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter

from src.core.gateway.models import (
    AutoRecipeInfo,
    NLUParseRequest,
    NLUParseResponse,
    RecipeGenerateRequest,
    RecipeGenerateResponse,
    RecipeValidateRequest,
    RecipeValidateResponse,
)

router = APIRouter()


@router.post("/nlu/parse")
def nlu_parse(req: NLUParseRequest) -> NLUParseResponse:
    from src.core.nlu import IntentClassifier
    res = IntentClassifier().classify(req.goal)
    return NLUParseResponse(
        intent=res.intent.value, confidence=res.confidence,
        entities=res.entities, suggested_recipe=res.suggested_recipe,
    )


@router.post("/recipes/generate")
def recipes_generate(req: RecipeGenerateRequest) -> RecipeGenerateResponse:
    from src.core.recipe_gen import RecipeGenerator
    gen = RecipeGenerator()
    recipe = gen.from_goal_pattern(req.goal, req.steps or None)
    path = gen.save_recipe(recipe) if recipe.valid else ""
    return RecipeGenerateResponse(
        name=recipe.name, content=recipe.content,
        source=recipe.source, valid=recipe.valid, path=path,
    )


@router.get("/recipes/auto")
def recipes_auto_list() -> list[AutoRecipeInfo]:
    from src.core.recipe_gen import RecipeGenerator
    return [AutoRecipeInfo(**r) for r in RecipeGenerator().list_auto_recipes()]


@router.post("/recipes/validate")
def recipes_validate(req: RecipeValidateRequest) -> RecipeValidateResponse:
    from src.core.recipe_gen import RecipeGenerator
    valid, errors = RecipeGenerator().validate_recipe(req.content)
    return RecipeValidateResponse(valid=valid, errors=errors)


@router.get("/api/agi/health")
async def agi_health() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:9090/health", timeout=5.0)
            result: dict[str, Any] = resp.json()
            return result
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": "AGI daemon not reachable", "status": "offline"}


@router.get("/api/agi/metrics")
async def agi_metrics() -> dict[str, Any]:
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://127.0.0.1:9090/metrics", timeout=5.0)
            result: dict[str, Any] = resp.json()
            return result
    except (httpx.ConnectError, httpx.TimeoutException):
        return {"error": "AGI daemon not reachable", "status": "offline"}


__all__ = ["router"]
