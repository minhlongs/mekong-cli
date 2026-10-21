# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Data contracts and prompt/parameter helpers for Agent Assembly (B6)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.harness.agents.classifier import TaskProfile

if TYPE_CHECKING:
    from src.core.memory_bridge import MemoryBridge, MemoryRecord
    from src.harness.pev.pev_types import EngineParams

logger = logging.getLogger(__name__)

INTENT_MODEL_MAP: Dict[str, str] = {
    "deploy": "claude-sonnet-4",
    "audit": "claude-opus-4-8",
    "create": "claude-sonnet-4",
    "fix": "claude-sonnet-4",
    "status": "claude-sonnet-4",
    "schedule": "claude-sonnet-4",
    "refactor": "claude-opus-4-8",
    "optimize": "claude-opus-4-8",
    "migrate": "claude-sonnet-4",
    "report": "claude-sonnet-4",
}

INTENT_TEMP_MAP: Dict[str, float] = {
    "audit": 0.1,
    "fix": 0.2,
    "refactor": 0.15,
    "migrate": 0.1,
    "deploy": 0.2,
    "create": 0.3,
    "report": 0.2,
    "optimize": 0.3,
    "status": 0.3,
    "schedule": 0.3,
    "unknown": 0.3,
}


@dataclass
class AssembledAgent:
    """Fully configured agent ready for execution."""

    agent_id: str
    instance: Any
    intent: str = "unknown"
    confidence: float = 0.0
    engine_params: "EngineParams" = field(default=None)  # type: ignore[assignment]
    memory_context: List["MemoryRecord"] = field(default_factory=list)
    task_profile: Optional[TaskProfile] = None

    role: str = ""
    tools: List[str] = field(default_factory=list)
    assembly_trace: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssemblyConfig:
    """Tunable knobs for the assembly pipeline."""

    use_nlu: bool = True
    nlu_context: Optional[Dict[str, Any]] = None
    memory_limit: int = 5
    memory_kinds: Optional[List[str]] = None
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None
    factory_config: Optional[str] = None
    cache: bool = True


def derive_engine_params(
    profile: Optional[TaskProfile],
    trace: Dict[str, Any],
    model_map: Dict[str, str],
    temp_map: Dict[str, float],
    override_model: Optional[str] = None,
    override_temp: Optional[float] = None,
) -> "EngineParams":
    """Derive EngineParams from TaskProfile and overrides."""
    from src.harness.pev.pev_types import EngineParams

    intent_lower = (profile.agent_role if profile else "unknown").lower()
    model = override_model or model_map.get(intent_lower, "claude-sonnet-4")
    temperature = (
        override_temp
        if override_temp is not None
        else temp_map.get(intent_lower, 0.3)
    )
    max_tokens = 4096
    if profile:
        if profile.complexity == "simple":
            max_tokens = 2048
            temperature = min(temperature, 0.2)
        elif profile.complexity == "complex":
            max_tokens = 8192

    trace["pev"] = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "intent_used": intent_lower,
    }
    return EngineParams(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        retries=2,
        retry_delay_s=2.0,
        timeout_s=120.0,
    )


def search_memory_context(
    bridge: Optional["MemoryBridge"],
    goal: str,
    profile: Optional[TaskProfile],
    memory_limit: int,
    trace: Dict[str, Any],
) -> List["MemoryRecord"]:
    """Query Memory Bridge for relevant past entries."""
    if bridge is None:
        trace["memory"] = {"skipped": "no bridge available"}
        return []
    try:
        agent_id = profile.agent_role if profile else None
        records = bridge.search(goal, limit=memory_limit, agent_id=agent_id)
        trace["memory"] = {"entries_found": len(records), "agent_filter": agent_id}
        return records[:memory_limit]
    except Exception as exc:
        logger.debug("Memory search failed: %s", exc)
        trace["memory"] = {"error": str(exc)}
        return []


def compose_system_prompt(assembled: AssembledAgent, defn: Dict[str, Any]) -> str:
    """Compose enriched system prompt from assembled agent + memory."""
    role_prompt = (
        defn.get("role_prompt")
        or defn.get("role")
        or assembled.role
        or assembled.agent_id
    )
    parts: List[str] = [role_prompt]
    if assembled.memory_context:
        mem_lines = ["[Relevant Past Experiences]"]
        for rec in assembled.memory_context[:3]:
            mem_lines.append(f"- {rec.content[:200]}")
        mem_lines.append("[End memories]")
        parts.append("\n".join(mem_lines))
    if assembled.task_profile:
        tp = assembled.task_profile
        parts.append(
            f"[Context: domain={tp.domain}, "
            f"complexity={tp.complexity}, "
            f"model_tier={tp.preferred_tier}]"
        )
    return "\n\n".join(parts)
