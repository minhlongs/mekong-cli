"""Mekong CLI 7 — Agent dispatch for graph nodes.

Each graph node is one LLM call (node-level subagent) using the agent's
model role (all resolve to 1M-capable models via core/models.py). The node
prompt may request tool calls; results are executed through core/tools.py
with the whitelist enforced.
"""

from __future__ import annotations

from typing import Any

from .agents import get_agent
from .graph import Node
from .llm import LLMClient
from .models import resolve_or_fallback
from .tools import run_tool


def build_node_prompt(node: Node, shared: dict[str, object], skills_context: str = "", compact_context: str = "") -> str:
    ctx = []
    for key, val in shared.items():
        if key != node.id:
            ctx.append(f"<context-{key}>{str(val)[:800]}</context-{key}>")
    skills = f"\nSkill context to follow:\n{skills_context}\n" if skills_context else ""
    compact = f"\n[Compacted prior context]\n{compact_context}\n[/Compacted]\n" if compact_context else ""
    return (
        f"You are the {node.agent} agent. Execute this node task precisely:\n\n"
        f"TASK: {node.task}\n\n"
        f"{skills}"
        f"{compact}"
        + ("\n".join(ctx) if ctx else "(no upstream context)")
        + "\n\n"
        "You may request tool calls by replying with JSON tool-call objects: "
        '{"tool": "bash-test", "command": "..."} or {"tool": "write", "path": "...", "content": "..."} '
        "or plain text if no tools are needed. Return your final result as the last line, "
        'prefixed with "RESULT:".'
    )


def dispatch_node(
    node: Node,
    shared: dict[str, object],
    client: LLMClient | None = None,
    max_tokens: int = 4096,
    max_steps: int = 0,
    compact_context: str = "",
) -> dict[str, object]:
    """Run one graph node: one LLM call through the agent's model role.

    Returns {"llm": str, "tools": [tool results], "result": str}.
    max_steps > 0 caps agentic tool-iteration rounds (opencode `steps`):
    after the cap the model is forced to reply with text only.
    compact_context replaces raw prior context when compaction fired.
    """
    client = client or LLMClient()
    agent = get_agent(node.agent)
    entry = resolve_or_fallback(agent.model if agent else node.agent)

    prompt = build_node_prompt(node, shared, compact_context=compact_context)
    if max_steps > 0:
        prompt += (
            f"\n\nYou have at most {max_steps} tool-call rounds for this node. "
            "Use tools sparingly; after the limit you must answer with text only."
        )
    raw = client.text(entry.id, prompt, max_tokens=max_tokens)

    tool_results: list[dict[str, Any]] = []
    result_text = raw

    # Execute any tool-call JSON embedded in the reply (tolerate concat/array).
    from .agents import _parse_tool_calls
    from .gates import AgentPermissionResolver

    perm = AgentPermissionResolver()

    calls = _parse_tool_calls(raw.strip())
    if calls:
        for round_idx, call in enumerate(calls[: max_steps if max_steps > 0 else len(calls)]):
            tool = str(call.get("tool", ""))
            command = str(call.get("command", "") or call.get("path", ""))
            try:
                # Plugin before-hooks (tool.execute.before)
                from .plugins import HookRegistry, PluginBlocked, PluginLoader

                hooks = HookRegistry()
                PluginLoader().load_all()
                try:
                    call_args = dict(call)
                    modified = hooks.run_before(tool, call_args)
                    if isinstance(modified, dict):
                        call = modified
                        tool = str(call.get("tool", tool))
                        command = str(call.get("command", "") or call.get("path", "") or command)
                except PluginBlocked as pb:
                    tool_results.append({"tool": tool, "ok": False, "output": "", "error": f"plugin blocked: {pb.reason}"})
                    continue

                perm.check(node.agent, tool, command)
                if tool in ("write", "bash-test", "bash", "cat", "read", "grep", "glob", "edit", "apply-patch", "apply_patch", "webfetch", "question", "lsp"):
                    cmd = command
                    if tool == "write":
                        cmd = f'write {call.get("path", "")} {call.get("content", "")}'
                    elif tool in ("cat", "read"):
                        cmd = f"{tool} {call.get('path', '')}"
                    elif tool in ("grep", "glob", "edit", "webfetch", "question", "lsp"):
                        if call.get("path"):
                            cmd = f"{tool} {call.get('path', '')}"
                        elif call.get("pattern"):
                            cmd = f"{tool} {call.get('pattern', '')}"
                        elif call.get("url"):
                            cmd = f"{tool} {call.get('url', '')}"
                        elif call.get("command"):
                            cmd = command
                    res = run_tool(cmd)
                else:
                    res = {"tool": tool, "ok": False, "output": "", "error": f"unsupported tool {tool}"}
                # Plugin after-hooks (tool.execute.after)
                hooks.run_after(tool, call, res)
            except Exception as e:
                res = {"tool": tool, "ok": False, "output": "", "error": str(e)[:300]}
            tool_results.append(res)

        # Prefer RESULT: line for final text; fall back to raw.
        for line in reversed(raw.splitlines()):
            if line.startswith("RESULT:"):
                result_text = line[len("RESULT:") :].strip()
                break

    return {"llm": raw, "tools": tool_results, "result": result_text}
