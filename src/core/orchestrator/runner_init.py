# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Initialization and sub-engine setup for RecipeOrchestrator."""

from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING

from rich.console import Console

from ..execution_history import ExecutionHistory
from ..memory_canonical import MemoryStore
from ..nlu import IntentClassifier
from ..planner import RecipePlanner
from ..retry_policy import RetryPolicy
from ..telemetry import TelemetryCollector
from ..verifier import RecipeVerifier

if TYPE_CHECKING:
    from src.providers.llm.client import LLMClient
    from ..constitution import Constitution
    from .runner import RecipeOrchestrator


def init_orchestrator(
    orchestrator: RecipeOrchestrator,
    llm_client: Optional["LLMClient"] = None,
    strict_verification: bool = True,
    enable_rollback: bool = True,
    use_swarm: bool = False,
    retry_policy: Optional[RetryPolicy] = None,
    constitution: Optional["Constitution"] = None,
    constitutional_mode: str = "audit",
) -> None:
    """Initialize all subsystems, engines, and managers on the orchestrator instance."""
    orchestrator.planner = RecipePlanner(llm_client=llm_client)
    orchestrator.verifier = RecipeVerifier(strict_mode=strict_verification)
    orchestrator.console = Console()
    orchestrator.enable_rollback = enable_rollback
    orchestrator.telemetry = TelemetryCollector()
    orchestrator.memory = MemoryStore()
    orchestrator.nlu = IntentClassifier(llm_client=llm_client)
    orchestrator.retry_policy = retry_policy or RetryPolicy()
    orchestrator.history = ExecutionHistory()
    orchestrator.logger = logging.getLogger(orchestrator.__class__.__name__)

    from ..constitution import Constitution
    orchestrator.constitution = constitution or Constitution(llm_client=llm_client)
    orchestrator.constitutional_mode = constitutional_mode

    from .agi import AGIComponents as _AGIComponents

    orchestrator._agi = _AGIComponents(llm_client=llm_client)
    orchestrator._reflection = orchestrator._agi.reflection
    orchestrator._world_model = orchestrator._agi.world_model
    orchestrator._tool_registry = orchestrator._agi.tool_registry
    orchestrator._collaboration = orchestrator._agi.collaboration
    orchestrator._code_evolution = orchestrator._agi.code_evolution
    orchestrator._vector_memory = orchestrator._agi.vector_memory

    if use_swarm:
        from ..swarm import SwarmDispatcher, SwarmRegistry
        orchestrator.dispatcher = SwarmDispatcher(SwarmRegistry())
    else:
        orchestrator.dispatcher = None

    orchestrator.bmad_loader = None
    try:
        from packages.core.bmad.loader import BMADWorkflowLoader
        orchestrator.bmad_loader = BMADWorkflowLoader()
    except ImportError:
        orchestrator.console.print("[yellow]Warning: BMAD loader not available[/yellow]")


__all__ = ["init_orchestrator"]
