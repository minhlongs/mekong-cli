# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Agent Loop — Minimal tool-use agent for local LLMs (MLX).

Sends task + tools to LLM via OpenAI-compatible API, parses tool_calls,
executes them, feeds results back. Repeats until LLM returns final answer.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .agent_loop_config import TIER_CONFIG, TIER_URLS as TIER_URLS, TOOLS

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
SANDBOX_DIR = MEKONG_ROOT / ".mekong"


def _safe_path(relative: str) -> Path:
    """Resolve path inside sandbox. Prevents directory traversal."""
    resolved = (SANDBOX_DIR / relative).resolve()
    if not str(resolved).startswith(str(SANDBOX_DIR.resolve())):
        raise ValueError(f"Path traversal blocked: {relative}")
    return resolved


def execute_tool(name: str, args: dict[str, Any]) -> str:
    """Execute a tool call. Returns result string."""
    try:
        if name == "read_file":
            p = _safe_path(args["path"])
            return p.read_text()[:4000] if p.exists() else f"File not found: {args['path']}"

        if name == "write_file":
            p = _safe_path(args["path"])
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"])
            return f"Written {len(args['content'])} bytes to {args['path']}"

        if name == "http_get":
            url = args["url"]
            if not url.startswith("http"):
                return "Error: URL must start with http"
            host = urlparse(url).hostname or ""
            if host in ("localhost", "127.0.0.1", "0.0.0.0") or host.startswith(
                ("10.", "172.16.", "192.168.", "169.254.")
            ):
                return "Error: internal/private URLs blocked"
            req = Request(url, headers={"User-Agent": "MekongAgent/1.0"})
            with urlopen(req, timeout=10) as resp:
                return resp.read().decode("utf-8", errors="replace")[:4000]

        if name == "list_dir":
            p = _safe_path(args["path"])
            if not p.is_dir():
                return f"Not a directory: {args['path']}"
            return "\n".join(f.name for f in sorted(p.iterdir()))

        if name == "append_log":
            log_dir = SANDBOX_DIR / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            fname = args["filename"].replace("/", "_").replace("..", "")
            log_path = log_dir / fname
            ts = datetime.now().isoformat()
            from src.core.file_lock import locked_append

            with locked_append(log_path) as f:
                f.write(f"[{ts}] {args['message']}\n")
            return f"Logged to {fname}"

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error ({name}): {e}"


def _llm_call(
    messages: list, base_url: str, model: str = "default",
    api_key: str = "local", max_tokens: int = 512, timeout: int = 120,
) -> dict:
    """Call LLM via OpenAI-compatible API. Returns assistant message dict."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model, "messages": messages, "tools": TOOLS,
        "max_tokens": max_tokens, "temperature": 0.3,
    }).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key != "local":
        headers["Authorization"] = f"Bearer {api_key}"
    req = Request(url, data=payload, headers=headers)
    with urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]


def run_agent_sync(
    task: str, model_tier: str = "fast", max_steps: int = 5, system_prompt: str = "",
) -> str:
    """Run agent loop synchronously. Returns final text response."""
    tier = TIER_CONFIG.get(model_tier, TIER_CONFIG["fast"])
    base_url, model_id = tier["url"], tier["model"]
    max_tok, timeout = tier.get("max_tokens", 512), tier.get("timeout", 120)

    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    messages.append({"role": "user", "content": task})

    for step in range(max_steps):
        try:
            msg = _llm_call(messages, base_url, model_id, "local", max_tokens=max_tok, timeout=timeout)
        except (URLError, Exception) as e:
            logger.error(f"LLM call failed (step {step}): {e}")
            return f"Error: LLM call failed — {e}"

        messages.append(msg)
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return msg.get("content", "No response")

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                fn_args = {}
            result = execute_tool(fn_name, fn_args)
            logger.info(f"[Step {step}] {fn_name}({fn_args}) → {result[:100]}")
            tool_id = tc.get("id") or f"call_{uuid.uuid4().hex[:12]}"
            tc["id"] = tool_id
            messages.append({"role": "tool", "tool_call_id": tool_id, "content": result})

    return messages[-1].get("content", "Max steps reached")


async def run_agent(task: str, **kwargs) -> str:
    """Async wrapper for run_agent_sync (runs in thread to avoid blocking)."""
    import asyncio

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: run_agent_sync(task, **kwargs))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [AGENT] %(message)s")
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What files are in the logs directory?"
    tier = os.getenv("MODEL_TIER", "fast")
    print(f"Agent Loop | Tier: {tier} | Task: {task}\n---")
    print(run_agent_sync(task, model_tier=tier))
