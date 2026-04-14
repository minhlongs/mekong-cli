# Research: Mekong CLI Multi-LLM Architecture — Wrapping CC CLI + Gemini CLI + Qwen API + Local LLMs

**Date:** 2026-03-25 | **Sources:** 15+ | **Status:** Complete

---

## Executive Summary

Mekong CLI can wrap multiple AI backends into a unified TUI. The architecture already exists in `scripts/mekong-wrapper.sh` — just needs extending. Key finding: **Claude Code CLI can already use Qwen/DeepSeek via `ANTHROPIC_BASE_URL` override**, meaning one CLI binary serves all providers. For SoloOS autonomous ops, local LLMs CAN do tool use via MLX-LM's OpenAI-compatible API + structured output parsing.

---

## 1. Current Mekong CLI Architecture (Already Built)

```
mekong-wrapper.sh
  ├─ mekong         → claude (default Anthropic)
  ├─ mekong-opus    → claude --model claude-opus-4-6
  ├─ mekong-sonnet  → claude --model claude-sonnet-4-6
  ├─ mekong-qwen    → claude with ANTHROPIC_BASE_URL=dashscope
  └─ mekong-cto     → claude in CTO daemon mode
```

**Key insight:** CC CLI + `ANTHROPIC_BASE_URL` override = ANY OpenAI-compatible provider.

---

## 2. Available CLI Tools to Wrap

| CLI | Provider | Install | Non-Interactive Mode | Tool Use |
|-----|----------|---------|---------------------|----------|
| `claude` | Anthropic | `npm i -g @anthropic-ai/claude-code` | `claude --print "task"` | Full agent |
| `gemini` | Google | `brew install gemini-cli` | `gemini -y -m model "prompt"` | Full agent |
| `qwen` | Alibaba | **NO CLI** — API only | N/A | Via API |
| `opencode` | Multi-provider | `go install` | `opencode --non-interactive` | Limited |

**Qwen has NO official CLI.** Access via:
- DashScope API (OpenAI-compatible endpoint)
- CC CLI with `ANTHROPIC_BASE_URL` override
- Direct HTTP calls

---

## 3. DashScope API — Complete Model Catalog (2026)

### Qwen Models (Alibaba's own)

| Model | Input $/1M | Output $/1M | Context | Tool Use |
|-------|-----------|------------|---------|----------|
| Qwen3 Max | $0.78 | $3.90 | 32K | Yes |
| Qwen3.5 Plus | $0.26 | $1.56 | 32K | Yes |
| Qwen Plus | $0.40 | $1.20 | 128K | Yes |
| Qwen Turbo | $0.08 | $0.30 | 128K | Yes |
| Qwen3 8B | $0.05 | $0.40 | 32K | Yes |
| Qwen Long | $0.02 | $0.08 | 1M | Limited |
| Qwen-Coder-Plus | $0.80 | $2.40 | 128K | Yes |
| Qwen-VL-Max | $1.04 | $3.12 | 32K | No |

### Third-Party on DashScope

| Model | Provider | Available |
|-------|----------|-----------|
| DeepSeek V3/R1 | DeepSeek | Via OpenRouter, not DashScope directly |
| Yi-Large | 01.AI | Yes |
| Baichuan | Baichuan | Yes |
| GLM-4 | Zhipu AI | Separate API (not DashScope) |

**Free tier:** New accounts get free credits (varies by region). Batch API = 50% discount.

### Endpoints

```bash
# International (Singapore/US)
DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

# OpenAI-compatible — works with CC CLI!
ANTHROPIC_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
ANTHROPIC_MODEL=qwen3.5-plus
```

---

## 4. Local LLM Tool Use (MLX on M1 Max)

### Does MLX support function calling?

**YES** — mlx-lm server (0.31+) supports OpenAI-compatible tool use for models that were fine-tuned for it.

Models with tool use support on MLX:
- `Qwen2.5-Coder-32B-Instruct` — Strong tool use
- `DeepSeek-R1-Distill-Qwen-32B` — Limited (reasoning-focused, not tool-tuned)
- `Nemotron-3-Nano-30B` — Basic function calling

### Simplest Agent Loop (Python, <100 lines)

```python
import httpx, json

TOOLS = [
    {"type": "function", "function": {
        "name": "read_file", "description": "Read a file",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}
        }, "required": ["path"]}
    }},
    {"type": "function", "function": {
        "name": "write_file", "description": "Write content to file",
        "parameters": {"type": "object", "properties": {
            "path": {"type": "string"}, "content": {"type": "string"}
        }, "required": ["path", "content"]}
    }},
    {"type": "function", "function": {
        "name": "http_request", "description": "Make HTTP request",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string"}, "method": {"type": "string"}
        }, "required": ["url"]}
    }},
]

def execute_tool(name, args):
    if name == "read_file": return open(args["path"]).read()
    if name == "write_file": open(args["path"],"w").write(args["content"]); return "OK"
    if name == "http_request": return httpx.request(args.get("method","GET"), args["url"]).text[:2000]

def agent_loop(task, base_url="http://localhost:11436/v1", max_steps=5):
    messages = [{"role": "user", "content": task}]
    for _ in range(max_steps):
        resp = httpx.post(f"{base_url}/chat/completions", json={
            "model": "nemotron", "messages": messages, "tools": TOOLS
        }, timeout=120).json()
        msg = resp["choices"][0]["message"]
        messages.append(msg)
        if not msg.get("tool_calls"): return msg["content"]  # Done
        for tc in msg["tool_calls"]:
            result = execute_tool(tc["function"]["name"], json.loads(tc["function"]["arguments"]))
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)})
    return messages[-1].get("content", "Max steps reached")
```

### Frameworks for Local LLM Tool Use

| Framework | Complexity | MLX Support | Recommendation |
|-----------|-----------|-------------|----------------|
| Raw HTTP (above) | Minimal | Direct | **Best for SoloOS** |
| Agno | Low | Via OpenAI compat | Good for structured agents |
| LangChain | High | Via ChatMLX | Overkill |
| smolagents | Medium | Via OpenAI compat | Good but extra deps |

---

## 5. Proposed Mekong CLI Multi-Backend Architecture

```
┌──────────────────────────────────────────────┐
│  mekong <command> [--provider X]             │
│  scripts/mekong-wrapper.sh                    │
└──────────────────┬───────────────────────────┘
                   │
         ┌─────────▼──────────┐
         │  Provider Router    │
         │  mekong/adapters/   │
         └─────────┬──────────┘
                   │
    ┌──────┬───────┼────────┬──────────┐
    │      │       │        │          │
  claude gemini  qwen    local     opencode
  (CC CLI) (Gemini CLI) (DashScope) (MLX)  (Go CLI)
    │      │       │        │          │
  Opus   Flash  Qwen3.5  Nemotron  DeepSeek
  Sonnet  Pro   Coder    DeepSeek  via local
```

### New aliases to add in mekong-wrapper.sh

```bash
# Existing
mekong-opus     → claude --model claude-opus-4-6
mekong-sonnet   → claude --model claude-sonnet-4-6
mekong-qwen     → claude with DASHSCOPE env vars

# NEW — to add
mekong-gemini   → gemini -y -m gemini-2.5-pro "..."
mekong-local    → direct HTTP to MLX (agent_loop.py)
mekong-cheap    → claude with ANTHROPIC_BASE_URL=dashscope + qwen-turbo ($0.08/1M!)
```

### For SoloOS Tier 2 (autonomous on M1 Max)

```python
# In heartbeat_scheduler.py — replace placeholder Tier 2:
from src.daemon.agent_loop import agent_loop

async def execute_tier2(task, loop_config):
    model_tier = loop_config.get("model_tier", "fast")
    base_url = {
        "fast": "http://localhost:11436/v1",    # Nemotron
        "deep": "http://localhost:11435/v1",    # DeepSeek
        "coding": DASHSCOPE_URL,                # Qwen API
    }[model_tier]

    result = agent_loop(
        task=loop_config["tier2_prompt"],
        base_url=base_url,
        max_steps=5
    )
    return result
```

---

## 6. Implementation Roadmap

| Step | What | Effort |
|------|------|--------|
| 1 | Create `src/daemon/agent_loop.py` (~100 lines) | 1h |
| 2 | Wire Tier 2 in `heartbeat_scheduler.py` to use agent_loop | 30min |
| 3 | Add `mekong-gemini` + `mekong-cheap` aliases | 15min |
| 4 | Test tool use with Nemotron (function calling) | 1h |
| 5 | Deploy to M1 Max | 15min |

**Total: ~3 hours to full multi-LLM agent architecture.**

---

## Unresolved Questions

1. Does Nemotron-3-Nano-30B-A3B actually support OpenAI function calling format via MLX? Need to test.
2. Qwen2.5-Coder-32B is NOT running on M1 Max right now (only DeepSeek + Nemotron). Load it as third model? Memory: 16+16+16=48GB, tight but possible.
3. DashScope international endpoint — does it have rate limits for free tier?
4. Should `mekong-gemini` wrap Gemini CLI or use Gemini API directly?

---

## Sources

- [DashScope API Reference](https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-dashscope)
- [DashScope Model Pricing](https://www.alibabacloud.com/help/en/model-studio/model-pricing)
- [Qwen API Pricing 2026](https://pricepertoken.com/pricing-page/provider/qwen)
- [CC Compatible Models Guide](https://github.com/Alorse/cc-compatible-models)
- [Claude Code with Alternative Models](https://techsy.io/blog/claude-code-use-different-models)
- [MLX-LM Tool Use Guide](https://medium.com/@levchevajoana/a-job-postings-tool-a-guide-to-mlx-lm-server-and-tool-use-with-the-openai-client-edb9a5d75b4c)
- [MLX Agent Framework Integration](https://www.strathweb.com/2025/12/introducing-mlx-integration-library-for-agent-framework/)
- [Agno Framework + MLX](https://medium.com/@levchevajoana/running-local-hugging-face-models-with-mlx-lm-and-the-agno-agentic-framework-de134259d34d)
- [mlx-lm GitHub](https://github.com/ml-explore/mlx-lm)
- [Local LLMs Replacing Claude Code](https://agentnativedev.medium.com/local-llms-that-can-replace-claude-code-6f5b6cac93bf)
