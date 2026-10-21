# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - Agent Registry."""
from __future__ import annotations

import logging
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .agent_base import AgentBase, Result, Task, TaskStatus
from .registry.loader import load_descriptions

logger = logging.getLogger(__name__)


@dataclass
class AgentMeta:
    name: str
    description: str
    cls: type[AgentBase]
    allowed_tools: list[str] = field(default_factory=list)
    spawnable_agents: list[str] = field(default_factory=list)
    risk_level: str = "LOW"
    max_budget: float | None = None
    max_iterations: int | None = None
    approval_policy: str = "AUTO"
    model_preference: str | None = None

    def __post_init__(self) -> None:
        valid_risk, valid_approval = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}, {"AUTO", "MANUAL", "DENY"}
        if self.risk_level not in valid_risk:
            raise ValueError(f"Invalid risk_level: {self.risk_level}. Must be one of {valid_risk}")
        if self.approval_policy not in valid_approval:
            raise ValueError(f"Invalid approval_policy: {self.approval_policy}. Must be one of {valid_approval}")
        if self.risk_level == "CRITICAL" and self.approval_policy == "AUTO":
            raise ValueError("CRITICAL risk agents cannot have approval_policy=AUTO")


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, type[AgentBase]] = {}
        self._meta: dict[str, AgentMeta] = {}

    def register(self, name: str, cls: type, *, description: str = "", allowed_tools: list[str] | None = None, spawnable_agents: list[str] | None = None, risk_level: str = "LOW", max_budget: float | None = None, max_iterations: int | None = None, approval_policy: str = "AUTO", model_preference: str | None = None) -> None:
        if not isinstance(cls, type) or not issubclass(cls, AgentBase):
            logger.warning("%r is not an AgentBase subclass — registering under '%s'", cls, name)
        if allowed_tools:
            from .tool_names import ALL_TOOL_NAMES, resolve_tool_name
            unknown = [t for t in allowed_tools if resolve_tool_name(t) not in ALL_TOOL_NAMES and t != "*"]
            if unknown:
                logger.warning("Unknown tool(s) in allowed_tools for '%s': %s", name, unknown)
        self._agents[name] = cls
        self._meta[name] = AgentMeta(name=name, description=description or cls.__doc__ or name, cls=cls, allowed_tools=list(allowed_tools or []), spawnable_agents=list(spawnable_agents or []), risk_level=risk_level, max_budget=max_budget, max_iterations=max_iterations, approval_policy=approval_policy, model_preference=model_preference)

    def get(self, name: str) -> type[AgentBase]:
        if name not in self._agents:
            raise KeyError(f"Unknown agent: '{name}'. Available agents: {list(self._agents.keys())}")
        return self._agents[name]
    def get_meta(self, name: str) -> dict[str, Any]:
        meta = self._meta.get(name)
        return {"allowed_tools": list(meta.allowed_tools) if meta else [], "spawnable_agents": list(meta.spawnable_agents) if meta else []}
    def get_meta_obj(self, name: str) -> AgentMeta | None:
        return self._meta.get(name)
    def list_agents(self) -> list[str]:
        return sorted(self._agents.keys())
    def list(self) -> list[str]:
        return self.list_agents()
    def discover(self) -> list[AgentMeta]:
        return [self._meta[name] for name in self.list_agents()]
    def register_decorator(self, name: str) -> Any:
        def wrapper(cls: type) -> type:
            self.register(name, cls)
            return cls
        return wrapper
    def __contains__(self, name: object) -> bool:
        return name in self._agents
    def __len__(self) -> int:
        return len(self._agents)
    def __repr__(self) -> str:
        return f"<AgentRegistry agents={self.list_agents()}>"


_SINGLETON: AgentRegistry | None = None
AGENTS_DIR = Path(__file__).resolve().parents[2] / ".claude" / "agents"
_DEFAULT_DESCRIPTIONS: dict[str, str] = load_descriptions()
_AGENT_ROLE_HINTS: dict[str, str] = {"cto": "code", "cmo": "marketing", "coo": "operations", "cfo": "finance", "cso": "analysis", "planner": "plan"}


def get_registry() -> AgentRegistry:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = AgentRegistry()
        _register_known_agents(_SINGLETON)
        _discover_markdown_agents(_SINGLETON)
    return _SINGLETON


def _register_known_agents(registry: AgentRegistry) -> None:
    if "cli" not in registry._agents:
        registry.register("cli", _CliShellAgent, description="Default CLI runtime agent — runs local shell goals through CommandSanitizer", allowed_tools=["shell:run"], risk_level="MEDIUM", approval_policy="AUTO")
    for name, description in _DEFAULT_DESCRIPTIONS.items():
        if name not in registry._agents:
            registry.register(name, _make_markdown_agent_class(name, f"You are the {name} agent."), description=description)


def _description_from_frontmatter(text: str, fallback: str) -> str:
    parts = text.split("---", 2) if text.startswith("---") else []
    for raw_line in (parts[1].splitlines() if len(parts) >= 3 else []):
        if raw_line.strip().startswith("description:"):
            val = raw_line.strip()[len("description:"):].strip()
            return val.strip("\"'") if val and val[0] in "\"'" else val
    return fallback


class _CliShellAgent(AgentBase):
    def __init__(self, name: str = "cli", **kwargs: object) -> None:
        super().__init__(name=name)
    def plan(self, input_data: str) -> list[Any]:
        return [Task(id=f"{self.name}-1", description=input_data, input={"command": input_data}, status=TaskStatus.PENDING)]
    def execute(self, task: Any) -> Any:
        command, task.status = str(task.input.get("command") or task.description or ""), TaskStatus.RUNNING
        try:
            from .command_sanitizer import CommandSanitizer
            san = CommandSanitizer(strict_mode=True).sanitize(command)
            if not san.is_safe:
                return Result(task_id=task.id, success=False, error=f"shell:run blocked by CommandSanitizer: {'; '.join(san.blocked_patterns) or san.blocked_reason or 'unknown'}")
            command = san.sanitized_command or command
        except ImportError:
            return Result(task_id=task.id, success=False, error="CommandSanitizer module missing — shell:run blocked (fail-closed)")
        try:
            proc = subprocess.run(shlex.split(command), capture_output=True, text=True, timeout=30)
            output, task.status = proc.stdout or proc.stderr, (TaskStatus.FAILED if proc.returncode != 0 else TaskStatus.SUCCESS)
            return Result(task_id=task.id, success=proc.returncode == 0, output=output.strip(), error=f"Exit code {proc.returncode}: {output}" if proc.returncode != 0 else None)
        except Exception as exc:
            task.status = TaskStatus.FAILED
            return Result(task_id=task.id, success=False, error=str(exc))


def _make_markdown_agent_class(role: str, prompt: str) -> type[AgentBase]:
    def execute(self: Any, task: Any) -> Any:
        task.status = TaskStatus.SUCCESS
        return Result(task_id=task.id, success=True, output=f"[{role.upper()}] {prompt[:240] + ('...' if len(prompt) > 240 else '')}")
    return type(f"Markdown{role.capitalize()}Agent", (AgentBase,), {"__doc__": _DEFAULT_DESCRIPTIONS.get(role, role), "plan": lambda self, data: [Task(id=f"{role}-1", description=f"Run {role} agent", input={"text": data})], "execute": execute})


def _discover_markdown_agents(registry: AgentRegistry) -> None:
    from .agent_dispatcher import DEFAULT_PROMPTS, load_agent_prompt
    for md_path in (sorted(AGENTS_DIR.glob("*.md")) if AGENTS_DIR.is_dir() else []):
        name = md_path.stem
        try:
            content = md_path.read_text(encoding="utf-8")
            prompt = DEFAULT_PROMPTS.get(name) or load_agent_prompt(name, include_hub=False)
        except OSError:
            continue
        except Exception:
            prompt = f"You are the {name} agent."
        registry.register(name, _make_markdown_agent_class(name, prompt), description=_description_from_frontmatter(content, _DEFAULT_DESCRIPTIONS.get(name, f"{name} agent")))


__all__ = ["AgentRegistry", "AgentMeta", "get_registry", "AGENTS_DIR"]
