# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data models, intent detection, and prompt token helpers for RecipeParser."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .pev_types import (
    EngineParams,
    PromptToken,
    TokenRole,
    ValidationConditions,
)


@dataclass
class RecipeStep:
    """Single executable step in a PEV recipe."""

    order: int
    title: str
    description: str = ""
    params: dict = field(default_factory=dict)
    agent: str | None = None
    validation: ValidationConditions = field(default_factory=ValidationConditions)
    dependencies: list[int] = field(default_factory=list)


@dataclass
class Recipe:
    """Full PEV recipe — backward-compatible superset of the original Recipe."""

    name: str = ""
    title: str = ""
    steps: List[RecipeStep] = field(default_factory=list)
    verification: List[str] = field(default_factory=list)

    intent: str = ""
    prompt_tokens: List[PromptToken] = field(default_factory=list)
    engine_params: EngineParams = field(default_factory=EngineParams)
    validation: ValidationConditions = field(default_factory=ValidationConditions)
    metadata: dict = field(default_factory=dict)


def detect_recipe_intent(recipe: Recipe) -> str:
    """Detect recipe intent from title, frontmatter, or step keywords."""
    if recipe.intent:
        return recipe.intent.upper()

    try:
        from src.core.nlu import classify_intent  # type: ignore[attr-defined]

        result = classify_intent(recipe.title)
        if hasattr(result, "intent") and hasattr(result.intent, "value"):
            return result.intent.value.upper()
    except Exception:
        pass

    fallback: dict[str, list[str]] = {
        "DEPLOY": ["deploy", "ship", "publish", "triển khai", "trien khai"],
        "FIX": ["fix", "repair", "debug", "patch", "sửa", "sua", "khắc phục"],
        "CREATE": ["create", "build", "generate", "init", "tạo", "tao", "xây"],
        "AUDIT": ["audit", "scan", "review", "kiểm tra", "kiem tra"],
        "REFACTOR": ["refactor", "clean", "restructure", "tái cấu trúc"],
        "OPTIMIZE": ["optimize", "performance", "tối ưu"],
    }
    title_lower = recipe.title.lower()
    for intent, keywords in fallback.items():
        if any(kw in title_lower for kw in keywords):
            return intent
    return "UNKNOWN"


def build_prompt_tokens(recipe: Recipe) -> List[PromptToken]:
    """Compose structured prompt tokens from goal + step context."""
    tokens: List[PromptToken] = [
        PromptToken(
            role=TokenRole.SYSTEM,
            content=(
                "You are the Mekong CLI execution engine. "
                "Follow each step precisely, report results verbatim."
            ),
            context="persona",
        ),
        PromptToken(
            role=TokenRole.USER,
            content=recipe.title or recipe.name or "execute the plan",
            context="goal",
        ),
    ]

    if recipe.metadata:
        ctx_parts = [f"{k}={v}" for k, v in recipe.metadata.items()]
        tokens.append(
            PromptToken(
                role=TokenRole.CONTEXT,
                content="Recipe metadata: " + ", ".join(ctx_parts),
                context="metadata",
            )
        )

    for step in recipe.steps:
        tokens.append(
            PromptToken(
                role=TokenRole.PLAN,
                content=f"Step {step.order}: {step.title}\n{step.description}",
                context=f"step-{step.order}",
            )
        )

    hard_checks = recipe.validation.hard
    if hard_checks:
        tokens.append(
            PromptToken(
                role=TokenRole.GUARD,
                content="Hard requirements (must pass):\n  - "
                + "\n  - ".join(hard_checks),
                context="verification",
            )
        )

    if recipe.steps:
        first = recipe.steps[0]
        tokens.append(
            PromptToken(
                role=TokenRole.EXAMPLE,
                content=f"Example: {first.title} → {first.description}",
                context="step-1",
            )
        )

    return tokens
