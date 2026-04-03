# Mekong IDE - Tech Stack

## Hardware Target
- Apple Silicon M1 Max, 64GB Unified Memory, 1TB SSD

## Architecture: 4 Layers

### Layer 1: Mekong Studio (Frontend)
- **VSCodium** (MIT) with MCP extension (Continue.dev or Roo Code)
- Connects to Orchestrator via HTTP MCP

### Layer 2: Mekong Orchestrator (Backend Router)
- **Language:** Rust
- **Framework:** Axum 0.8+ / Tokio 1.x
- **HTTP Client:** reqwest (async, multi-backend proxy)
- **Serialization:** serde + serde_json
- **MCP:** rmcp or manual JSON-RPC 2.0 implementation
- **Protocol:** OpenAI-compatible API proxying to 3 local LLM backends
- **License compliance:** cargo-deny for license audit

### Layer 3: Engine Farm (MLX Servers)
- **Runtime:** Python mlx-lm (pip install mlx-lm)
- **Serving:** Separate process per model (avoids KV cache bug)

| Port | Role | Model | HuggingFace ID | Size |
|------|------|-------|----------------|------|
| 4001 | Router/Architect | Gemma 4 26B A4B | mlx-community/gemma-4-26b-a4b-it-4bit | ~6GB |
| 4002 | Reasoning/Coding | DeepSeek R1 32B | mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit-MLX | ~16GB |
| 4003 | Code Review/Audit | Qwen2.5-Coder-7B | mlx-community/Qwen2.5-Coder-7B-Instruct-4bit | ~4GB |

**Total model memory:** ~26GB / 64GB available

### Layer 4: Tool Ecosystem (MCP Servers)
- **vnstock-oracle:** Python MCP server wrapping vnstock library
- **bash-executor:** Rust sandbox for safe file/shell operations

## Key Dependencies

### Rust (Cargo.toml)
- axum = "0.8"
- tokio = { version = "1", features = ["full"] }
- reqwest = { version = "0.12", features = ["json"] }
- serde = { version = "1", features = ["derive"] }
- serde_json = "1"
- tower = "0.5"
- tracing = "0.1"
- tracing-subscriber = "0.3"

### Python
- mlx-lm
- mcp (Python MCP SDK)
- vnstock3
- fastapi / uvicorn (for MCP server)

## Design Decisions

1. **Separate MLX processes** per model (not single multi-model server) — avoids KV cache cross-contamination
2. **Gemma 4 as router** — native function calling, only 3.8B active params = fast routing decisions
3. **DeepSeek R1 32B** over 14B — fits in memory budget, significantly better reasoning
4. **Qwen2.5-Coder-7B** replaces nonexistent "Nemotron 8B" — excellent code review, small footprint
5. **Context cap 8192** per model — prevents throughput collapse at longer contexts
6. **HTTP MCP** (not stdio) — enables VSCodium extension connection via TCP
