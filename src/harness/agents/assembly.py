"""Mekong CLI - Agent Assembly Pipeline (B6).

Assembles configured agent instances from user intent by chaining:
  NLU (B3) -> PEV params (B5) -> Memory context (B4) -> Agent config -> Instance

Public API:
    assemble_agent(goal, llm=None, memory=None) -> AssembledAgent
    AgentAssembler — reusable builder (initialise once, call .assemble() per goal)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from src.harness.agents.classifier import classify_task, TaskProfile
from src.harness.agents.factory import AgentFactory, AgentMetadata

if TYPE_CHECKING:
    from src.harness.pev.pev_types import EngineParams
    from src.core.memory_bridge import MemoryBridge, MemoryRecord

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Public data contracts                                                         #
# --------------------------------------------------------------------------- #

@dataclass
class AssembledAgent:
    """Fully configured agent ready for execution.

    Attributes:
        agent_id:     Registry key (e.g. "ceo", "eng").
        instance:     Configured AgentBase subclass or AgentMetadata stub.
        intent:       B3 NLU result — classified intent string.
        confidence:   NLU confidence 0.0–1.0.
        engine_params: B5-derived engine params (model, temperature, etc.).
        memory_context: Relevant past entries from Memory Bridge (B4).
        task_profile:  B3 TaskProfile with domain / complexity / tier hints.
    """

    agent_id: str
    instance: Any  # AgentBase
    intent: str = "unknown"
    confidence: float = 0.0
    engine_params: "EngineParams" = field(default=None)  # type: ignore[assignment]
    memory_context: List["MemoryRecord"] = field(default_factory=list)
    task_profile: Optional[TaskProfile] = None

    # Metadata derived during assembly
    role: str = ""
    tools: List[str] = field(default_factory=list)
    assembly_trace: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssemblyConfig:
    """Tunable knobs for the assembly pipeline."""

    # NLU
    use_nlu: bool = True
    nlu_context: Optional[Dict[str, Any]] = None

    # Memory — how many past entries to surface
    memory_limit: int = 5
    memory_kinds: Optional[List[str]] = None  # None = all kinds

    # PEV — intent-to-model mapping overrides
    model_override: Optional[str] = None
    temperature_override: Optional[float] = None

    # Factory
    factory_config: Optional[str] = None  # YAML path; None = default
    cache: bool = True  # cache assembled instances in factory


# --------------------------------------------------------------------------- #
# Agent assembler                                                                #
# --------------------------------------------------------------------------- #

class AgentAssembler:
    """Builds configured agents from raw user goals.

    Pipeline:
        1. Classify goal with B3 NLU → intent, TaskProfile
        2. Map intent/entities → PEV EngineParams (model, temperature)
        3. Query Memory Bridge for relevant past entries
        4. Instantiate agent via AgentFactory
        5. Package everything into AssembledAgent

    Usage::

        assembler = AgentAssembler()
        result = assembler.assemble("deploy my-app to production")
        agent = result.instance
        agent.run(result.intent)
    """

    # Intent → preferred model (quality/cost trade-off)
    _INTENT_MODEL_MAP: Dict[str, str] = {
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

    # Intent → preferred temperature (lower = more deterministic)
    _INTENT_TEMP_MAP: Dict[str, float] = {
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

    def __init__(self, config: Optional[AssemblyConfig] = None) -> None:
        self.config = config or AssemblyConfig()
        self._factory = AgentFactory(
            config_path=self.config.factory_config  # type: ignore[arg-type]
            if self.config.factory_config
            else AgentFactory._CONFIG_PATH
        )
        self._memory: Optional[Any] = None  # MemoryBridge, lazy-loaded

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble(
        self,
        goal: str,
        *,
        llm: Any = None,
        memory: Any = None,
    ) -> AssembledAgent:
        """Full assembly pipeline: intent → params → memory → agent.

        Args:
            goal:   Raw user goal string.
            llm:    Optional LLM client (passed to agent constructor).
            memory: Optional MemoryBridge instance (overrides lazy init).

        Returns:
            AssembledAgent ready for execution.
        """
        trace: Dict[str, Any] = {"goal": goal}

        # Step 1: NLU classification (B3)
        profile = self._classify(goal, trace)

        # Step 2: PEV engine params (B5)
        engine_params = self._engine_params(profile, trace)

        # Step 3: Memory context (B4)
        mem_ctx = self._memory_context(goal, profile, trace)

        # Step 4: Agent selection & instantiation
        agent_id = self._select_agent(profile)
        instance = self._instantiate(agent_id, llm, memory, trace)

        # Step 5: Role/tools metadata
        defn = self._factory.get_definition(agent_id)

        assembled = AssembledAgent(
            agent_id=agent_id,
            instance=instance,
            intent=profile.agent_role if profile else "unknown",
            confidence=1.0 if profile else 0.0,
            engine_params=engine_params,
            memory_context=mem_ctx,
            task_profile=profile,
            role=defn.get("role", agent_id),
            tools=defn.get("tools", []),
            assembly_trace=trace,
        )
        logger.info("Assembled agent %r for goal=%r", agent_id, goal[:60])
        return assembled

    def reset(self) -> None:
        """Clear factory cache and memory reference."""
        self._factory._cache.clear()
        self._memory = None

    # ------------------------------------------------------------------
    # Step 1: NLU
    # ------------------------------------------------------------------

    def _classify(
        self, goal: str, trace: Dict[str, Any]
    ) -> Optional[TaskProfile]:
        """Classify goal with B3 NLU. Returns None on failure."""
        if not self.config.use_nlu:
            trace["nlu"] = {"skipped": True}
            return None

        try:
            profile = classify_task(goal, context=self.config.nlu_context)
            trace["nlu"] = {
                "intent": profile.agent_role,
                "domain": profile.domain,
                "complexity": profile.complexity,
                "confidence": 1.0,  # classify_task uses keyword heuristics
                "mcu_cost": profile.mcu_cost,
                "preferred_tier": profile.preferred_tier,
            }
            return profile
        except Exception as exc:
            logger.debug("NLU classification failed: %s", exc)
            trace["nlu"] = {"error": str(exc)}
            return None

    # ------------------------------------------------------------------
    # Step 2: PEV engine params
    # ------------------------------------------------------------------

    @staticmethod
    def _engine_params(
        profile: Optional[TaskProfile], trace: Dict[str, Any]
    ) -> "EngineParams":
        """Derive EngineParams from TaskProfile + config overrides."""
        from src.harness.pev.pev_types import EngineParams

        intent = profile.agent_role if profile else "unknown"
        intent_lower = intent.lower()

        model = AgentAssembler._INTENT_MODEL_MAP.get(intent_lower, "claude-sonnet-4")
        temperature = AgentAssembler._INTENT_TEMP_MAP.get(intent_lower, 0.3)

        # Apply overrides from config
        if AgentAssembler._config_override_model:
            model = AgentAssembler._config_override_model
        if AgentAssembler._config_override_temp is not None:
            temperature = AgentAssembler._config_override_temp

        # Simpler tasks = fewer tokens, lower temperature
        max_tokens = 4096
        if profile:
            if profile.complexity == "simple":
                max_tokens = 2048
                temperature = min(temperature, 0.2)
            elif profile.complexity == "complex":
                max_tokens = 8192

        params = EngineParams(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            retries=2,
            retry_delay_s=2.0,
            timeout_s=120.0,
        )
        trace["pev"] = {
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "intent_used": intent_lower,
        }
        return params

    # Per-instance overrides (set via class-level mechanism to avoid shared state)
    _config_override_model: Optional[str] = None
    _config_override_temp: Optional[float] = None

    # ------------------------------------------------------------------
    # Step 3: Memory context
    # ------------------------------------------------------------------

    def _memory_context(
        self,
        goal: str,
        profile: Optional[TaskProfile],
        trace: Dict[str, Any],
    ) -> List["MemoryRecord"]:
        """Query Memory Bridge for relevant past entries."""
        bridge = self._get_memory_bridge()
        if bridge is None:
            trace["memory"] = {"skipped": "no bridge available"}
            return []

        try:
            agent_id = profile.agent_role if profile else None
            records = bridge.search(
                goal,
                limit=self.config.memory_limit,
                agent_id=agent_id,
            )
            trace["memory"] = {
                "entries_found": len(records),
                "agent_filter": agent_id,
            }
            return records[: self.config.memory_limit]
        except Exception as exc:
            logger.debug("Memory search failed: %s", exc)
            trace["memory"] = {"error": str(exc)}
            return []

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

    # ------------------------------------------------------------------
    # Step 4: Agent selection & instantiation
    # ------------------------------------------------------------------

    @staticmethod
    def _select_agent(profile: Optional[TaskProfile]) -> str:
        """Map NLU profile to registry agent ID."""
        if profile is None:
            return "ceo"  # default fallback
        # classifier.py already maps domain → agent_role (cto, cmo, etc.)
        role = profile.agent_role
        # Validate against factory registry
        try:
            factory = AgentFactory()
            available = factory.list_available()
            if role in available:
                return role
        except Exception:
            pass
        return "ceo"

    def _instantiate(
        self,
        agent_id: str,
        llm: Any,
        memory: Any,
        trace: Dict[str, Any],
    ) -> Any:
        """Create agent via factory, injecting PEV (via role_prompt) and memory."""
        try:
            instance = self._factory.create(
                agent_id,
                llm=llm,
                memory=memory,
            )
            trace["factory"] = {
                "agent_id": agent_id,
                "type": type(instance).__name__,
            }
            return instance
        except Exception as exc:
            logger.error("Agent instantiation failed for %r: %s", agent_id, exc)
            trace["factory"] = {"error": str(exc)}
            raise ValueError(
                f"Failed to create agent '{agent_id}': {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Convenience: build system prompt enriched with memory context
    # ------------------------------------------------------------------

    @staticmethod
    def build_system_prompt(assembled: AssembledAgent) -> str:
        """Compose enriched system prompt from assembled agent + memory.

        Combines:
            - Base role prompt from registry config
            - Memory snippets (past experiences relevant to this goal)
            - PEV constraints (verification conditions, if any)
        """
        parts: List[str] = []

        # Base role prompt
        defn = {}
        try:
            factory = AgentFactory()
            defn = factory.get_definition(assembled.agent_id)
        except Exception:
            pass
        role_prompt = defn.get("role_prompt") or defn.get("role", assembled.agent_id)
        parts.append(role_prompt)

        # Memory context injection
        if assembled.memory_context:
            mem_lines = ["[Relevant Past Experiences]"]
            for rec in assembled.memory_context[:3]:
                snippet = rec.content[:200]
                mem_lines.append(f"- {snippet}")
            mem_lines.append("[End memories]")
            parts.append("\n".join(mem_lines))

        # Task profile hints
        if assembled.task_profile:
            tp = assembled.task_profile
            hints = (
                f"[Context: domain={tp.domain}, "
                f"complexity={tp.complexity}, "
                f"model_tier={tp.preferred_tier}]"
            )
            parts.append(hints)

        return "\n\n".join(parts)


# --------------------------------------------------------------------------- #
# Module-level convenience — single-call assembly                               #
# --------------------------------------------------------------------------- #

_assembler: Optional[AgentAssembler] = None


def get_assembler(config: Optional[AssemblyConfig] = None) -> AgentAssembler:
    """Return process-wide AgentAssembler (singleton)."""
    global _assembler
    if _assembler is None:
        _assembler = AgentAssembler(config)
    return _assembler


def assemble_agent(
    goal: str,
    llm: Any = None,
    memory: Any = None,
    config: Optional[AssemblyConfig] = None,
) -> AssembledAgent:
    """One-shot: classify → parametrize → recall → instantiate.

    Args:
        goal:    User goal string.
        llm:     Optional LLM client.
        memory:  Optional MemoryBridge instance.
        config:  Optional AssemblyConfig overrides.

    Returns:
        AssembledAgent ready for .instance.run(goal).
    """
    assembler = get_assembler(config)
    return assembler.assemble(goal, llm=llm, memory=memory)


# --------------------------------------------------------------------------- #
# Exports                                                                      #
# --------------------------------------------------------------------------- #

__all__ = [
    "AgentAssembler",
    "AssembledAgent",
    "AssemblyConfig",
    "assemble_agent",
    "get_assembler",
]
