"""Mekong CLI 7 — agent registry + dispatch.

Agents read from mekong-cli/agents/registry.yaml (kept from v6).
Each agent maps to a model role: sun-tzu -> strategist (qwen3.8-max),
ceo/ae/pm/eng/ops -> sonnet (claude-sonnet-5-0).
"""

from __future__ import annotations

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path

from .llm import LLMClient
from .models import resolve

AGENTS_FILE = Path(__file__).resolve().parents[3] / "agents" / "registry.yaml"


@dataclass
class Agent:
    id: str
    name: str
    role: str
    description: str
    model: str  # role key: fable/sonnet/opus/haiku/strategist
    tools: list[str] = field(default_factory=list)
    prompt: str = ""


def load_registry() -> list[Agent]:
    if not AGENTS_FILE.exists():
        return []
    data = yaml.safe_load(AGENTS_FILE.read_text()) or {}
    agents: list[Agent] = []
    for entry in data.get("agents", []):
        model_role = entry.get("model", "sonnet")
        if model_role == "fable":
            model_role = "fable"
        agents.append(
            Agent(
                id=entry.get("id", ""),
                name=entry.get("name", entry.get("id", "")),
                role=entry.get("role", ""),
                description=entry.get("description", ""),
                model=model_role,
                tools=entry.get("tools", []),
                prompt=entry.get("role_prompt") or entry.get("description") or "",
            )
        )
    return agents


def get_agent(agent_id: str) -> Agent | None:
    for a in load_registry():
        if a.id == agent_id:
            return a
    return None


def run_agent(
    agent_id: str,
    task: str,
    client: LLMClient | None = None,
    max_tokens: int = 4096,
    system_extra: str = "",
    execute_tools: bool = False,
) -> str:
    """Dispatch one agent to the LLM with its model role. Returns text.

    When execute_tools=True the agent is instructed to emit tool-call JSON
    ({tool, path, content|command}) and this runtime executes them locally
    (write / cat / bash) — the v7 tool-calling layer.
    """
    agent = get_agent(agent_id)
    if not agent:
        raise ValueError(f"Unknown agent: {agent_id}")
    client = client or LLMClient()
    entry = resolve(agent.model)
    system = agent.prompt
    if system_extra:
        system = f"{system}\n\n{system_extra}"
    if execute_tools:
        system = (
            f"{system}\n\n"
            "You have tools. To act, reply with ONE JSON object per action, no prose:\n"
            '{"tool": "write", "path": "rel/path", "content": "file contents"}\n'
            '{"tool": "cat", "path": "rel/path"}\n'
            '{"tool": "bash", "command": "typecheck command"}\n'
            "If multiple actions are needed, emit a JSON array of objects. "
            "Working directory is the operator's repo. Never use destructive commands "
            "(rm -rf, git push --force)."
        )
    reply = client.text(entry.id, task, system=system or None, max_tokens=max_tokens)
    if not execute_tools:
        return reply
    return _execute_tool_calls(reply)


def _parse_tool_calls(cleaned: str) -> list[dict] | None:
    """Parse tool-call JSON, tolerating concatenated objects/arrays/prose.

    LLMs often emit `{...}{...}` (no array). Returns a list of call dicts,
    or None when the text is not tool JSON (prose reply)."""
    import json

    if not cleaned or not cleaned.startswith(("{", "[")):
        return None

    calls: list[dict] = []
    decoder = json.JSONDecoder()
    idx = 0
    try:
        while idx < len(cleaned):
            while idx < len(cleaned) and cleaned[idx] in " \t\r\n":
                idx += 1
            if idx >= len(cleaned):
                break
            if cleaned[idx] not in "{[":
                if calls:
                    break  # trailing prose after parsed objects — ignore
                return None
            obj, end = decoder.raw_decode(cleaned, idx)
            if isinstance(obj, dict):
                calls.append(obj)
            elif isinstance(obj, list):
                calls.extend(o for o in obj if isinstance(o, dict))
            idx = end
    except Exception:
        return None
    return calls if calls else None


def _execute_tool_calls(reply: str) -> str:
    """Parse tool-call JSON from the agent reply and execute locally."""
    import re
    import subprocess
    from pathlib import Path

    cleaned = reply.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned)

    calls = _parse_tool_calls(cleaned)
    if calls is None:
        return reply  # not tool JSON — return as-is

    results: list[str] = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        tool = call.get("tool", "")
        try:
            if tool == "write":
                path = call.get("path", "")
                content = call.get("content", "")
                target = Path(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
                results.append(f"[write] {path} ({len(content)} bytes)")
            elif tool == "cat":
                path = call.get("path", "")
                data = Path(path).read_text()
                results.append(f"[cat] {path}:\n{data[:500]}")
            elif tool == "bash":
                command = call.get("command", "")
                proc = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
                tail = (proc.stdout + proc.stderr).strip()[-500:]
                results.append(f"[bash] $ {command}\n{tail}")
            else:
                results.append(f"[skip] unknown tool {tool}")
        except Exception as e:
            results.append(f"[error] {tool}: {str(e)[:200]}")
    return "\n".join(results) or reply


def run_strategist(task: str, client: LLMClient | None = None, max_tokens: int = 8192) -> str:
    """Sun Tzu / Kongming strategist counsel.

    qwen3.8-max is BANNED in mk pipeline (only @kongming/@suntzu in Claude
    Code may use it) — this resolves via fallback to claude-fable-5.
    """
    client = client or LLMClient()
    from .models import resolve_or_fallback

    entry = resolve_or_fallback("strategist")
    system = (
        "You are Sun Tzu — the strategist. Return honest, unfiltered strategic counsel "
        "in a single reply. Advisory only: never edit files, never run destructive commands. "
        "Structure: TL;DR, What to do, What to avoid, Alternatives & trade-offs, Assumptions."
    )
    return client.text(entry.id, task, system=system, max_tokens=max_tokens)
