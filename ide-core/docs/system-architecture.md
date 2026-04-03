# System Architecture — Mekong IDE Core

## Design Philosophy

- **Zero Telemetry**: All inference local, no data leaves the machine
- **Clean IP**: Only MIT/Apache 2.0 dependencies, no reverse-engineered code
- **MoE Efficiency**: Gemma 4 routes with 3.8B active params at 26B quality

## 4-Layer Architecture

### Layer 1: Mekong Studio (Frontend)
- VSCodium (MIT) with MCP extension (Continue.dev / Roo Code)
- Connects to Orchestrator via HTTP on port 8080
- Extension sends chat messages as OpenAI-compatible requests

### Layer 2: Mekong Orchestrator (Rust)
- **Framework**: Axum 0.8 + Tokio async runtime
- **Protocol**: OpenAI-compatible API (POST /v1/chat/completions)
- **MCP**: JSON-RPC 2.0 server for tool discovery and execution

#### Routing Pipeline
```
User Prompt
    │
    ▼
[Gemma 4 - Architect] ─── decides tools, structure
    │
    ├─ tool_calls? ──► [MCP Tool Execution]
    │                      │
    ▼                      ▼
[DeepSeek R1 - Reasoning] ◄── accumulated context
    │
    ├─ code blocks? ──► [Qwen Coder - Audit]
    │                      │
    ▼                      ▼
[Final Response] ◄──── aggregated + audited
```

### Layer 3: Engine Farm (MLX)
Each model runs as independent process via `python -m mlx_lm.server`.

| Port | Model | Active Params | Role | Memory |
|------|-------|--------------|------|--------|
| 4001 | Gemma 4 26B A4B (4-bit) | 3.8B | Router, tool calling | ~6GB |
| 4002 | DeepSeek R1 32B (4-bit) | 32B | Reasoning, coding | ~16GB |
| 4003 | Qwen2.5-Coder 7B (4-bit) | 7B | Code review, audit | ~4GB |

Separate processes avoid KV cache cross-contamination bug in mlx-lm.

### Layer 4: Tool Ecosystem (MCP Servers)
- **vnstock-oracle**: Python MCP server wrapping vnstock3 library
  - `get_financial_report(ticker, year, quarter)`
  - `get_credit_score_data(ticker)`
  - `get_stock_price(ticker, start_date, end_date)`
- **bash-executor**: Rust sandboxed shell execution (planned)

## Memory Budget (64GB M1 Max)

| Component | Allocation |
|-----------|-----------|
| macOS + VSCodium | ~8GB |
| Gemma 4 26B A4B | ~6GB |
| DeepSeek R1 32B | ~16GB |
| Qwen2.5-Coder 7B | ~4GB |
| KV Cache (3 models) | ~3-6GB |
| **Total Used** | **~37-40GB** |
| **Headroom** | **~24-27GB** |

## Data Flow

1. IDE sends user prompt to Orchestrator (port 8080)
2. Orchestrator enriches with system prompt + tool definitions
3. Gemma 4 receives prompt, returns structured plan + optional tool calls
4. If tools needed: Orchestrator calls MCP servers, appends results
5. If complex logic: forwards to DeepSeek R1 for reasoning
6. If code generated: forwards to Qwen Coder for security audit
7. Aggregated response returned to IDE

## Key Design Decisions

1. **Separate MLX processes** — KV cache isolation
2. **Context cap 8192** — prevents throughput collapse at longer windows
3. **Gemma 4 as router** — only model with native function calling
4. **Audit step is non-fatal** — if audit server is down, code still returns (degraded mode)
5. **All HTTP, no stdio** — simpler debugging, health checks, and IDE integration
