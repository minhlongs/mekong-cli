# Mekong IDE Core

Multi-Agent IDE Orchestrator for Apple Silicon. Routes prompts through 3 local LLMs via a 4-step pipeline: **Architect → Tools → Reasoning → Audit**.

## Architecture

```
┌──────────────────────────────────────────────────┐
│ Layer 1: VSCodium + MCP Extension (Continue.dev) │
└──────────────┬───────────────────────────────────┘
               │ HTTP (port 8080)
┌──────────────▼───────────────────────────────────┐
│ Layer 2: Mekong Orchestrator (Rust/Axum)         │
│   POST /v1/chat/completions → 4-step pipeline    │
│   POST /mcp → JSON-RPC 2.0 tool interface        │
└──┬──────────┬──────────┬─────────────────────────┘
   │          │          │
   │ :4001    │ :4002    │ :4003
┌──▼──┐  ┌───▼───┐  ┌───▼──────┐
│Gemma│  │DeepSk │  │Qwen2.5   │
│ 4   │  │ R1    │  │Coder     │
│26B  │  │ 32B   │  │ 7B       │
└─────┘  └───────┘  └──────────┘
 Router   Reasoning   Audit

Layer 4: MCP Tool Servers
├── vnstock-oracle (Python) — Vietnamese stock data
└── bash-executor (Rust) — Sandboxed shell [planned]
```

## 4-Step Pipeline

1. **Architect** (Gemma 4 26B A4B, port 4001): Analyzes prompt, plans structure, decides if tools needed. Native function calling.
2. **Tool Execution**: If architect requests tools, dispatches to MCP servers (vnstock, bash).
3. **Reasoning** (DeepSeek R1 32B, port 4002): Complex logic, code generation, Chain-of-Thought. Skipped for simple queries.
4. **Audit** (Qwen2.5-Coder 7B, port 4003): Security review, clean code validation. Skipped if no code generated.

## Hardware Requirements

- Apple Silicon M1 Max+ with 64GB+ Unified Memory
- ~26GB for 3 models (4-bit quantized)
- ~36GB headroom for OS, IDE, KV cache

## Quick Start

```bash
# 1. Setup environment (first time only)
./scripts/setup-m1max.sh

# 2. Start Engine Farm (3 MLX servers)
./engine-farm/start-farm.sh

# 3. Build & start Orchestrator
cd orchestrator && cargo build --release
RUST_LOG=info ./target/release/mekong-orchestrator

# 4. Test
curl http://localhost:8080/health
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'
```

## Project Structure

```
mekong-ide-core/
├── orchestrator/          # Rust — core routing engine
│   ├── src/main.rs        # Axum server + routes
│   ├── src/mcp_router.rs  # 4-step pipeline (CORE)
│   ├── src/llm_client.rs  # OpenAI-compatible HTTP client
│   ├── src/mcp_handler.rs # MCP JSON-RPC 2.0 server
│   ├── src/types.rs       # Shared types
│   ├── src/config.rs      # Env-based configuration
│   └── src/context_manager.rs
├── engine-farm/           # Bash — MLX model management
│   ├── config.env         # Model IDs, ports, params
│   ├── start-farm.sh      # Start 3 servers
│   ├── stop-farm.sh       # Graceful shutdown
│   └── health-check.sh    # Health checks
├── tools/                 # Python — MCP tool servers
│   ├── vnstock-mcp/       # Vietnamese stock data
│   └── bash-executor/     # Sandboxed shell [planned]
├── scripts/               # Environment setup
└── docs/                  # Technical documentation
```

## Configuration

All via environment variables (see `engine-farm/config.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| ORCHESTRATOR_PORT | 8080 | Orchestrator HTTP port |
| ROUTER_PORT | 4001 | Gemma 4 MLX server |
| REASONING_PORT | 4002 | DeepSeek R1 MLX server |
| AUDIT_PORT | 4003 | Qwen Coder MLX server |
| MAX_CONTEXT_TOKENS | 8192 | Context window limit |
| LLM_HOST | 127.0.0.1 | MLX server host |

## License

Apache 2.0 — Clean IP, all dependencies MIT or Apache 2.0.
