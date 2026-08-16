"""PEV structured types — Prompt tokens, Engine params, and Validation conditions.

These dataclasses define the triangle of every PEV run:

  PromptToken  → what the LLM receives (system, user, guard, etc.)
  EngineParams  → how the request is sent (model, temperature, retries)
  ValidationConditions → what "done" means (soft reqs vs hard gates)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class TokenRole(str, Enum):
    """Role of a PromptToken in the LLM context."""

    SYSTEM = "system"       # System prompt / persona
    USER = "user"           # User goal or input
    ASSISTANT = "assistant" # Prior assistant reply (context)
    CONTEXT = "context"     # Background state (repo, env, prior runs)
    EXAMPLE = "example"     # Few-shot example
    GUARD = "guard"         # Hard constraint / safety rule
    PLAN = "plan"           # Decomposed plan steps


class ValidationKind(str, Enum):
    """Soft vs hard verification."""

    SOFT = "soft"   # Advisory — observed but does not block success
    HARD = "hard"   # Gate — fail if not satisfied


@dataclass
class PromptToken:
    """One structured token in the LLM context.

    Attributes:
        role: TokenRole describing where this token sits in the prompt.
        content: The actual text fed (or injectable text for the LLM).
        context: Short label for what this token represents
                 (e.g. "goal", "deployment target").
    """

    role: TokenRole
    content: str
    context: str = ""


@dataclass
class EngineParams:
    """Parameters controlling LLM execution for a PEV run.

    Attributes:
        model: Model identifier (e.g. "claude-opus-4-8", "qwen3.5-plus").
        temperature: LLM temperature 0.0–1.0.
        max_tokens: Max completion tokens.
        retries: Number of retry attempts on transient failure.
        retry_delay_s: Seconds between retries.
        timeout_s: Overall timeout for the run in seconds.
    """

    model: str = "claude-sonnet-4"
    temperature: float = 0.3
    max_tokens: int = 4096
    retries: int = 2
    retry_delay_s: float = 2.0
    timeout_s: float = 120.0


@dataclass
class ValidationConditions:
    """Verification conditions for a PEV step.

    Uses two layers:
    - Soft: advisory observations (log probes, token counts). Failure
            does NOT fail the step.
    - Hard: binary gates (file exists, exit code, output contains/has-not).
            Failure DOES fail the step.

    Attributes:
        soft: List of freeform soft-condition strings.
        hard: List of hard-gate condition strings.
    """

    soft: List[str] = field(default_factory=list)
    hard: List[str] = field(default_factory=list)


@dataclass
class PEVRecipe:
    """Full PEV recipe — composed by the parser from Markdown + YAML frontmatter.

    Attributes:
        name: Recipe filename stem (slug).
        title: Human-readable title from ## Goal heading.
        intent: Detected IntentType (fully-qualified string).
        prompt_tokens: Ordered list of structured prompt tokens.
        engine_params: LLM execution parameters.
        validation: Verification conditions per step.
        steps: Executable steps from ## Steps section.
        metadata: Extra key/value pairs from YAML frontmatter.
    """

    name: str = ""
    title: str = ""
    intent: str = ""
    prompt_tokens: List[PromptToken] = field(default_factory=list)
    engine_params: EngineParams = field(default_factory=EngineParams)
    validation: ValidationConditions = field(default_factory=ValidationConditions)
    verification: List[str] = field(default_factory=list)
    steps: List = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


__all__ = [
    "PEVRecipe",
    "PromptToken",
    "TokenRole",
    "EngineParams",
    "ValidationConditions",
    "ValidationKind",
]
