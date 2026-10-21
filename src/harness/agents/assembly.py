# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Agent Assembly Pipeline (B6).

Assembles configured agent instances from user intent by chaining:
  NLU (B3) -> PEV params (B5) -> Memory context (B4) -> Agent config -> Instance
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.harness.agents.assembly_models import (
    INTENT_MODEL_MAP, INTENT_TEMP_MAP, AssembledAgent, AssemblyConfig,
    compose_system_prompt, derive_engine_params, search_memory_context,
)
from src.harness.agents.classifier import TaskProfile, classify_task
from src.harness.agents.factory import AgentFactory

if TYPE_CHECKING:
    from src.core.memory_bridge import MemoryBridge, MemoryRecord
    from src.harness.pev.pev_types import EngineParams

logger = logging.getLogger(__name__)


class AgentAssembler:
    """Builds configured agents from raw user goals."""

    _INTENT_MODEL_MAP: Dict[str, str] = INTENT_MODEL_MAP
    _INTENT_TEMP_MAP: Dict[str, float] = INTENT_TEMP_MAP
    _config_override_model: Optional[str] = None
    _config_override_temp: Optional[float] = None

    def __init__(self, config: Optional[AssemblyConfig] = None) -> None:
        self.config = config or AssemblyConfig()
        self._factory = AgentFactory(
            config_path=self.config.factory_config  # type: ignore[arg-type]
            if self.config.factory_config else AgentFactory._CONFIG_PATH
        )
        self._memory: Optional[Any] = None

    def assemble(self, goal: str, *, llm: Any = None, memory: Any = None) -> AssembledAgent:
        """Full assembly pipeline: intent -> params -> memory -> agent."""
        trace: Dict[str, Any] = {"goal": goal}
        profile = self._classify(goal, trace)
        engine_params = self._engine_params(profile, trace)
        mem_ctx = self._memory_context(goal, profile, trace)
        agent_id = self._select_agent(profile)
        instance = self._instantiate(agent_id, llm, memory, trace)
        defn = self._factory.get_definition(agent_id)
        logger.info("Assembled agent %r for goal=%r", agent_id, goal[:60])
        return AssembledAgent(
            agent_id=agent_id, instance=instance,
            intent=profile.agent_role if profile else "unknown",
            confidence=1.0 if profile else 0.0,
            engine_params=engine_params, memory_context=mem_ctx,
            task_profile=profile, role=defn.get("role", agent_id),
            tools=defn.get("tools", []), assembly_trace=trace,
        )

    def reset(self) -> None:
        self._factory._cache.clear()
        self._memory = None

    def _classify(self, goal: str, trace: Dict[str, Any]) -> Optional[TaskProfile]:
        if not self.config.use_nlu:
            trace["nlu"] = {"skipped": True}
            return None
        try:
            profile = classify_task(goal, context=self.config.nlu_context)
            trace["nlu"] = {
                "intent": profile.agent_role,
                "domain": profile.domain,
                "complexity": profile.complexity,
                "confidence": 1.0,
                "mcu_cost": profile.mcu_cost,
                "preferred_tier": profile.preferred_tier,
            }
            return profile
        except Exception as exc:
            logger.debug("NLU classification failed: %s", exc)
            trace["nlu"] = {"error": str(exc)}
            return None

    @staticmethod
    def _engine_params(
        profile: Optional[TaskProfile], trace: Dict[str, Any]
    ) -> "EngineParams":
        return derive_engine_params(
            profile,
            trace,
            AgentAssembler._INTENT_MODEL_MAP,
            AgentAssembler._INTENT_TEMP_MAP,
            AgentAssembler._config_override_model,
            AgentAssembler._config_override_temp,
        )

    def _memory_context(
        self, goal: str, profile: Optional[TaskProfile], trace: Dict[str, Any]
    ) -> List["MemoryRecord"]:
        return search_memory_context(
            self._get_memory_bridge(), goal, profile, self.config.memory_limit, trace
        )

    def _get_memory_bridge(self) -> Optional["MemoryBridge"]:
        if self._memory is not None:
            return self._memory
        try:
            from src.core.memory_bridge import get_bridge

            self._memory = get_bridge("seed")
            return self._memory
        except Exception as exc:
            logger.debug("MemoryBridge init failed: %s", exc)
            return None

    @staticmethod
    def _select_agent(profile: Optional[TaskProfile]) -> str:
        if profile is None:
            return "ceo"
        try:
            if profile.agent_role in AgentFactory().list_available():
                return profile.agent_role
        except Exception:
            pass
        return "ceo"

    def _instantiate(
        self, agent_id: str, llm: Any, memory: Any, trace: Dict[str, Any]
    ) -> Any:
        try:
            instance = self._factory.create(agent_id, llm=llm, memory=memory)
            trace["factory"] = {"agent_id": agent_id, "type": type(instance).__name__}
            return instance
        except Exception as exc:
            logger.error("Agent instantiation failed for %r: %s", agent_id, exc)
            trace["factory"] = {"error": str(exc)}
            raise ValueError(f"Failed to create agent '{agent_id}': {exc}") from exc

    @staticmethod
    def build_system_prompt(assembled: AssembledAgent) -> str:
        defn: Dict[str, Any] = {}
        try:
            defn = AgentFactory().get_definition(assembled.agent_id)
        except Exception:
            pass
        return compose_system_prompt(assembled, defn)


_assembler: Optional[AgentAssembler] = None


def get_assembler(config: Optional[AssemblyConfig] = None) -> AgentAssembler:
    global _assembler
    if _assembler is None:
        _assembler = AgentAssembler(config)
    return _assembler


def assemble_agent(
    goal: str, llm: Any = None, memory: Any = None, config: Optional[AssemblyConfig] = None
) -> AssembledAgent:
    return get_assembler(config).assemble(goal, llm=llm, memory=memory)


__all__ = ["AgentAssembler", "AssembledAgent", "AssemblyConfig", "assemble_agent", "get_assembler"]
