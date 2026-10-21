# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Hybrid LLM Router — Main Orchestrator."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field

from src.core.agent_dispatcher import build_message_chain
from src.core.command_loader import build_system_prompt, find_best_command
from src.core.context_flow import ContextFlow
from src.core.cost_estimator import CostEstimate, estimate_cost
from src.core.fallback_chain import execute_with_fallback
from src.core.mcu_gate import MCUGate
from src.core.model_selector import SystemState, select_model_with_tier
from src.core.subagent_reviewer import SubagentReviewer
from src.core.task_classifier import TaskProfile, classify_multi_agent, classify_task
from src.providers.llm.client import get_client

logger = logging.getLogger(__name__)


@dataclass
class MissionResult:
    success: bool
    mission_id: str = ""
    model_used: str | None = None
    mcu_charged: int = 0
    output: str = ""
    error: str = ""
    profile: TaskProfile | None = None
    cost_estimate: CostEstimate | None = None
    attempts: list[str] = field(default_factory=list)


def _get_system_state() -> SystemState:
    local_available, local_models = False, []
    try:
        from src.core.local_adapter import OllamaAdapter
        adapter = OllamaAdapter()
        local_available = adapter.health_check()
        if local_available:
            local_models = adapter.list_models()
    except Exception as e:
        logger.debug("Hybrid router init error: %s", e)

    api_keys = {k: bool(os.getenv(v)) for k, v in [("anthropic", "ANTHROPIC_API_KEY"), ("google", "GOOGLE_API_KEY"), ("openai", "OPENAI_API_KEY")]}
    return SystemState(local_available=local_available, local_models=local_models, api_keys=api_keys, tenant_tier="growth")


async def route_and_execute(
    goal: str, tenant_id: str, mission_id: str | None = None, mcu_gate: MCUGate | None = None,
    system_state: SystemState | None = None, on_token: asyncio.coroutines = None,
) -> MissionResult:
    mission_id = mission_id or str(uuid.uuid4())
    profile = classify_task(goal, context={"tenant_id": tenant_id})
    agent_roles = classify_multi_agent(goal)
    is_multi_agent = len(agent_roles) > 1

    matched_command = find_best_command(goal, agent_role=profile.agent_role, domain=profile.domain)
    command_system_prompt = build_system_prompt(matched_command, goal) if matched_command else None

    gate = mcu_gate or MCUGate(":memory:")
    lock_result = gate.check_and_lock(tenant_id, mission_id, profile.mcu_cost)
    if not lock_result.success:
        return MissionResult(success=False, mission_id=mission_id, error=lock_result.error, profile=profile, mcu_charged=0)

    lock_id = lock_result.lock_id
    state = system_state or _get_system_state()
    task_tier = "mechanical" if profile.complexity == "simple" and not profile.requires_reasoning else "integration"
    model_config = select_model_with_tier(profile, state, task_tier=task_tier)
    cost_est = estimate_cost(profile, model_config.model_id)

    if is_multi_agent:
        flow = ContextFlow(task_id=mission_id)
        final_output_parts = []
        for agent_role in agent_roles:
            prior_context = flow.get_context_for(agent_role)
            enriched_goal = f"{prior_context}\n{goal}" if prior_context else goal
            messages, system_prompt, _ = build_message_chain(goal=enriched_goal, agent_role=agent_role, domain=profile.domain, tenant_id=tenant_id)
            try:
                exec_result = await execute_with_fallback(
                    model_config=model_config, messages=messages, system_prompt=command_system_prompt or system_prompt,
                    on_token_cb=on_token, data_sensitivity=profile.data_sensitivity,
                )
            except Exception as e:
                flow.add(agent_role, "", status="BLOCKED", concerns=str(e))
                continue

            if exec_result.success:
                flow.add(agent_role, exec_result.output, status="DONE")
                final_output_parts.append(f"[{agent_role.upper()}]\n{exec_result.output}")
            else:
                flow.add(agent_role, exec_result.error, status="BLOCKED", concerns=exec_result.error)
            if flow.has_blocker():
                break

        if flow.has_blocker():
            gate.refund_full(lock_id, reason="multi_agent_blocked")
            return MissionResult(success=False, mission_id=mission_id, error=f"multi_agent_blocked: {flow.get_summary()}", profile=profile)

        class _MultiAgentResult:
            success = True
            output = "\n\n".join(final_output_parts)
            model_used = model_config.model_id
            error = ""
            attempts = list(agent_roles)

        exec_result = _MultiAgentResult()
    else:
        messages, system_prompt, _ = build_message_chain(goal=goal, agent_role=profile.agent_role, domain=profile.domain, tenant_id=tenant_id)
        try:
            exec_result = await execute_with_fallback(
                model_config=model_config, messages=messages, system_prompt=command_system_prompt or system_prompt,
                on_token_cb=on_token, data_sensitivity=profile.data_sensitivity,
            )
        except Exception as e:
            gate.refund_full(lock_id, reason=str(e))
            return MissionResult(success=False, mission_id=mission_id, error=f"execution_failed: {e}", profile=profile)

    if not exec_result.success:
        gate.refund_full(lock_id, reason=exec_result.error)
        return MissionResult(success=False, mission_id=mission_id, error=exec_result.error, profile=profile, attempts=getattr(exec_result, "attempts", []))

    try:
        SubagentReviewer(get_client()).full_review(goal, exec_result.output)
    except Exception as e:
        logger.debug("Stage 7 — Review skipped: %s", e)

    gate.confirm(lock_id)
    final_output = exec_result.output
    watermark_enabled = True
    try:
        from src.raas.credits import CreditStore
        if CreditStore().get_balance(tenant_id) > 200:
            watermark_enabled = False
    except Exception:
        pass
    if watermark_enabled and final_output and not final_output.endswith("www.mekongmind.com"):
        final_output += "\n\n---\n*Generated by [MekongMind](https://www.mekongmind.com) — 290 commands, runs locally via Ollama*"

    return MissionResult(
        success=True, mission_id=mission_id, model_used=exec_result.model_used, mcu_charged=profile.mcu_cost,
        output=final_output, profile=profile, cost_estimate=cost_est, attempts=exec_result.attempts,
    )


def route_sync(
    goal: str, tenant_id: str, mission_id: str | None = None, mcu_gate: MCUGate | None = None, system_state: SystemState | None = None,
) -> MissionResult:
    return asyncio.run(route_and_execute(goal=goal, tenant_id=tenant_id, mission_id=mission_id, mcu_gate=mcu_gate, system_state=system_state))
