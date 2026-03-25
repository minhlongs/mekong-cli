"""
Agent Loop — Minimal tool-use agent for local LLMs (MLX).

Sends task + tools to LLM via OpenAI-compatible API, parses tool_calls,
executes them, feeds results back. Repeats until LLM returns final answer.

Tools: read_file, write_file, http_get, list_dir, append_log
Sandboxed: all file ops restricted to MEKONG_ROOT/.mekong/

Usage:
    from src.daemon.agent_loop import run_agent
    result = await run_agent("Scan for leads in fintech", model_tier="fast")

CLI:
    python3 -m src.daemon.agent_loop "Scan for leads in fintech"
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger(__name__)

MEKONG_ROOT = Path(__file__).parent.parent.parent
SANDBOX_DIR = MEKONG_ROOT / ".mekong"

# LLM endpoints + model IDs by tier
TIER_CONFIG = {
    "fast": {
        "url": os.getenv("NEMOTRON_URL", "http://192.168.11.111:11436/v1"),
        "model": "mlx-community/NVIDIA-Nemotron-3-Nano-30B-A3B-4bit",
    },
    "deep": {
        "url": os.getenv("DEEPSEEK_URL", "http://192.168.11.111:11435/v1"),
        "model": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit",
    },
    "coding": {
        "url": os.getenv("DASHSCOPE_URL",
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
        "model": "qwen3.5-plus",
    },
}
# Legacy compat
TIER_URLS = {k: v["url"] for k, v in TIER_CONFIG.items()}

# Tool definitions (OpenAI function calling format)
TOOLS = [
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from .mekong/ sandbox directory",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative path inside .mekong/"}
        }, "required": ["path"]}
    }},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write content to a file in .mekong/ sandbox directory",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative path inside .mekong/"},
            "content": {"type": "string", "description": "File content"}
        }, "required": ["path", "content"]}
    }},
    {"type": "function", "function": {
        "name": "http_get",
        "description": "Make HTTP GET request to a URL and return response body",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
        }, "required": ["url"]}
    }},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List files in a .mekong/ subdirectory",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string", "description": "Relative dir path inside .mekong/"}
        }, "required": ["path"]}
    }},
    {"type": "function", "function": {
        "name": "append_log",
        "description": "Append a line to a log file in .mekong/logs/",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "Log filename"},
            "message": {"type": "string", "description": "Log message"}
        }, "required": ["filename", "message"]}
    }},
]


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
            with open(log_path, "a") as f:
                f.write(f"[{ts}] {args['message']}\n")
            return f"Logged to {fname}"

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error ({name}): {e}"


def _llm_call(
    messages: list, base_url: str, model: str = "default", api_key: str = "local"
) -> dict:
    """Call LLM via OpenAI-compatible API. Returns assistant message dict."""
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "tools": TOOLS,
        "max_tokens": 2048,
        "temperature": 0.3,
    }).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    if api_key != "local":
        headers["Authorization"] = f"Bearer {api_key}"

    req = Request(url, data=payload, headers=headers)
    with urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())

    return data["choices"][0]["message"]


def run_agent_sync(
    task: str,
    model_tier: str = "fast",
    max_steps: int = 5,
    system_prompt: str = "",
) -> str:
    """Run agent loop synchronously. Returns final text response."""
    tier = TIER_CONFIG.get(model_tier, TIER_CONFIG["fast"])
    base_url = tier["url"]
    model_id = tier["model"]
    api_key = os.getenv("DASHSCOPE_API_KEY", "local") if model_tier == "coding" else "local"

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": task})

    for step in range(max_steps):
        try:
            msg = _llm_call(messages, base_url, model_id, api_key)
        except (URLError, Exception) as e:
            logger.error(f"LLM call failed (step {step}): {e}")
            return f"Error: LLM call failed — {e}"

        messages.append(msg)

        # No tool calls = final answer
        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            return msg.get("content", "No response")

        # Execute each tool call
        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                fn_args = {}
            result = execute_tool(fn_name, fn_args)
            logger.info(f"[Step {step}] {fn_name}({fn_args}) → {result[:100]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })

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
    print(f"Agent Loop | Tier: {tier} | Task: {task}")
    print("---")
    result = run_agent_sync(task, model_tier=tier)
    print(result)
