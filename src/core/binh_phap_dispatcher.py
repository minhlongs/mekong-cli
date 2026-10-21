# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Binh Phap Dispatcher — Bridges 3D Topology Engine to PEV Orchestrator."""

from __future__ import annotations

import importlib
import logging
import os
from pathlib import Path
from typing import Any, Optional

from src.core.binh_phap.reactions import Event, EventSource, ReactionEngine
from src.core.binh_phap.topology import CommandResult, CycleLesson, TopologyEngine
from src.core.binh_phap_escalation import FABLE_MODEL, OPUS_MODEL, create_provider_for_level, resolve_llm_provider

logger = logging.getLogger(__name__)


def _find_recipe_path(command: str) -> Optional[Path]:
    return next((p for p in (Path(f"factory/contracts/commands/{command}.json"), Path(f"recipes/{command}.md")) if p.exists()), None)


def _find_skill_path(command: str) -> Optional[Path]:
    parts = command.split(":")
    if len(parts) == 2 and (sp := Path(f".claude/skills/{parts[0]}-{parts[1]}/SKILL.md")).exists():
        return sp
    sp = Path(f".claude/skills/{command}/SKILL.md")
    return sp if sp.exists() else None


class BinhPhapDispatcher:
    """Translates Binh Phap topology decisions into PEV orchestrator actions."""

    _DOMAIN_MAP: dict[str, tuple[str, str, str]] = {
        "budget": ("src.commercial.finance", "FinanceEngine", "budget_review"),
        "pricing": ("src.commercial.finance", "FinanceEngine", "pricing_analysis"),
        "finance": ("src.commercial.finance", "FinanceEngine", "budget_review"),
        "campaign": ("src.commercial.marketing", "MarketingEngine", "plan_campaign"),
        "outreach": ("src.commercial.marketing", "MarketingEngine", "outreach"),
        "growth:experiment": ("src.commercial.growth", "GrowthEngine", "experiment"),
        "growth:channel-optimize": ("src.commercial.growth", "GrowthEngine", "optimize_channel"),
        "terrain": ("src.commercial.terrain", "TerrainAnalyzer", "analyze"),
        "positioning": ("src.commercial.terrain", "TerrainAnalyzer", "positioning"),
        "venture:terrain": ("src.commercial.terrain", "TerrainAnalyzer", "analyze"),
        "venture:void-substance": ("src.commercial.situation", "SituationAssessor", "assess"),
        "competitive": ("src.research.competitive", "CompetitiveScanner", "scan"),
        "scout": ("src.research.scout", "Scout", "find"),
        "research": ("src.research.competitive", "CompetitiveScanner", "scan"),
        "health": ("src.observability.health", "HealthMonitor", "check"),
    }

    def __init__(self, company_json: str = ".mekong/company.json") -> None:
        self.topology = TopologyEngine(company_json)
        self.reactions = ReactionEngine(self.topology)

    def next_action(self) -> dict[str, Any]:
        raw = self.topology.dispatch_next()
        action = raw.get("action", "unknown")
        if action == "execute":
            cmd = raw["command"]
            return {"action": "execute", "command": cmd, "recipe_path": _find_recipe_path(cmd), "skill_path": _find_skill_path(cmd), "llm": raw.get("llm", "local_mlx"), "needs_approval": raw.get("needs_approval", False), "chapter": raw.get("chapter", 0), "dimension": raw.get("dimension", "vertical")}
        if action == "execute_parallel":
            cmds = raw.get("commands", [])
            return {"action": "execute_parallel", "commands": cmds, "recipes": {c: _find_recipe_path(c) for c in cmds}, "skills": {c: _find_skill_path(c) for c in cmds}, "group": raw.get("group", ""), "llm": raw.get("llm", []), "needs_approval": raw.get("needs_approval", False), "dimension": "horizontal"}
        if action == "execute_loop":
            return {"action": "execute_loop", "commands": raw.get("commands", []), "cycle": raw.get("cycle", 0), "previous_lessons": raw.get("previous_lessons", []), "dimension": "diagonal"}
        return raw

    def report_result(self, command: str, success: bool, output: dict | None = None, error: str = "", duration_ms: int = 0) -> None:
        result = CommandResult(command=command, chapter=self.topology._command_to_chapter(command), success=success, output_key=f"{command}_output", output_data=output or {}, error=error, duration_ms=duration_ms)
        dimension = self.topology.state.get("current_dimension", "vertical")
        if dimension == "vertical":
            self.topology.advance_vertical(result)
            self.topology.consecutive_failures = 0 if success else self.topology.consecutive_failures + 1
        elif dimension == "horizontal":
            for name, group in self.topology.groups.items():
                if command in group.commands:
                    group.results.append(result)
                    if len(group.results) == len(group.commands):
                        self.topology.complete_group(name, group.results)
                    break

    def report_cycle_lesson(self, mrr: float, customers: int, lessons: list[str], adaptations: list[str] | None = None) -> None:
        self.topology.record_cycle_lesson(CycleLesson(cycle=self.topology.state.get("cycle_number", 1), mrr=mrr, customers=customers, lessons=lessons, adaptations=adaptations or []))

    def handle_event(self, event_type: str, source: str = "manual", data: dict | None = None) -> list[dict]:
        try:
            src = EventSource(source)
        except ValueError:
            src = EventSource.MANUAL
        return self.reactions.react(Event(type=event_type, source=src, data=data or {}))

    def get_llm_for_command(self, command: str) -> dict[str, Any]:
        llm_level = self.topology.get_llm_provider(command)
        return {**resolve_llm_provider(llm_level), "escalation_level": llm_level}

    def create_llm_client_for_command(self, command: str) -> Any:
        try:
            from src.providers.llm.client import LLMClient
        except ImportError:
            return None
        action = self.topology.dispatch_next()
        llm_level = action.get("llm") or self.topology.get_llm_provider(command)
        config = resolve_llm_provider(llm_level)
        base_url = config.get("base_url", "")

        if "zunef.com" in base_url.lower():
            try:
                from .providers import OpenAICompatibleProvider
                zb = next((base_url[: -len(sfx)] for sfx in ("/v1/ai", "/v1") if base_url.lower().endswith(sfx)), base_url)
                return LLMClient(providers=[OpenAICompatibleProvider(base_url=zb, api_key="-", model=config.get("model", FABLE_MODEL), provider_name=config.get("provider_name", "zunef"), timeout=120, extra_headers={"X-ZUNEF-CLIENT": "claude-code", "X-Device-Id": os.getenv("ZUNEF_DEVICE_ID", "")})])
            except Exception:
                pass
        if provider := create_provider_for_level(llm_level):
            try:
                return LLMClient(providers=[provider])
            except Exception:
                pass
        if llm_level == "local_mlx":
            try:
                from .providers import OpenAICompatibleProvider
                return LLMClient(providers=[OpenAICompatibleProvider(base_url=config.get("fallback_url", "http://localhost:11434/v1"), api_key="local", model=config.get("fallback_model", "qwen3.5-9b"), provider_name=config.get("fallback_name", "ollama-fallback"), timeout=120)])
            except Exception:
                pass
        return LLMClient()

    def get_status(self) -> dict[str, Any]:
        state = self.topology.state
        return {"dimension": state.get("current_dimension", "vertical"), "cycle": state.get("cycle_number", 0), "next_command": state.get("next_command", "swot"), "auto_dispatch": state.get("auto_dispatch", False), "target_mrr": state.get("target_mrr", 1000), "consecutive_failures": self.topology.consecutive_failures, "groups": {name: g.status.value for name, g in self.topology.groups.items()}, "cycles_completed": len(state.get("cycle_history", []))}

    def _get_domain_meta(self, domain_topic: str) -> tuple | None:
        return self._DOMAIN_MAP.get(domain_topic) or next((val for key, val in self._DOMAIN_MAP.items() if domain_topic.startswith(key)), None)

    def _execute_domain(self, domain_topic: str, prompt: str, context: dict | None = None) -> dict:
        if not (meta := self._get_domain_meta(domain_topic)):
            return {"domain": domain_topic, "error": f"No domain module registered for topic '{domain_topic}'", "available": list(self._DOMAIN_MAP.keys())}
        module_path, class_name, method_name = meta
        try:
            mod = importlib.import_module(module_path)
            kwargs = {**(context or {})}
            kwargs.setdefault("prompt", prompt)
            res = getattr(getattr(mod, class_name)(), method_name)(**kwargs)
            result = res if isinstance(res, dict) else {"result": res}
            for k, v in (("domain", domain_topic), ("module", module_path), ("method", method_name)):
                result.setdefault(k, v)
            return result
        except Exception as exc:
            logger.exception("Domain execution failed: %s.%s.%s", module_path, class_name, method_name)
            return {"domain": domain_topic, "module": module_path, "method": method_name, "error": str(exc)}

    def execute_for_topic(self, domain_topic: str, prompt: str, context: dict | None = None) -> dict:
        action = self.topology.dispatch_next()
        res = self._execute_domain(domain_topic, prompt, context)
        res.setdefault("meta", {}).update({"action": action.get("action", "unknown"), "dimension": action.get("dimension", "?"), "chapter": action.get("chapter", 0), "llm": action.get("llm", "?"), "needs_approval": action.get("needs_approval", False), "commands": action.get("commands", action.get("command", ""))})
        res.setdefault("topology", self.get_status())
        return res

    def execute_llm(self, prompt: str, domain: str | None = None) -> dict:
        command = domain or self.topology.state.get("next_command", "swot")
        pi = self.get_llm_for_command(command)
        return {"domain": domain or command, "llm": {"model": pi.get("model", OPUS_MODEL), "provider": pi.get("provider_name", "unknown"), "base_url": pi.get("base_url", ""), "escalation": pi.get("escalation_level", "AUTONOMOUS")}, "prompt": prompt, "note": "LLM execution delegated to PEV orchestrator / cook pipeline"}
