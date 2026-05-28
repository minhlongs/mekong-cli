# Scope: Anti-Gravity 2.0 Hybrid Runtime Implementation

## Architecture
The hybrid runtime is a terminal-native agent loop in Rust. It utilizes local llama.cpp inference driver on Apple Silicon (via Qwen-35B) or escalates to Claude via API.

The code is laid out under `antigravity/hybrid_runtime`:
- `Cargo.toml`: Cargo configuration with tree-sitter, rusqlite, tokio, reqwest, etc.
- `launch-llama.sh` & `run-claude-hybrid.sh`: Helper drivers for inference startup.
- `src/main.rs`: CLI Entrypoint and Interactive TTY loops.
- `src/inference.rs`: Client/Driver interface for llama.cpp server and Anthropic Claude.
- `src/indexer.rs`: tree-sitter/ast-grep symbol parser.
- `src/db.rs`: SQLite persistence layer.
- `src/router.rs`: Classification & compacting logic.
- `src/tools.rs`: Tool runner (shell execution, git control, ripgrep) with timeouts.
- `src/loop.rs`: Core Observe-Retrieve-Reason-Patch-Execute-Verify agent loop.

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M2 | Infra & Inference | Setup Rust workspace, local `llama.cpp` driver, scripts, connection verification | None | DONE |
| M3 | SQLite & AST | SQLite persistence schema, tree-sitter repository symbol indexing, symbol search | M2 | DONE |
| M4 | Routing Engine | Task classifier (regex + heuristics + token budget), context compactor (AST head extraction) | M3 | IN_PROGRESS |
| M5 | Agent Loop & Tools | Observe-Retrieve-Reason-Patch-Execute-Verify core loop, tools (shell, git, rg), approvals | M4 | PLANNED |
| M6 | E2E & Verification | Run Tier 1-4 tests, resolve failures, verification gate | M5 | PLANNED |
| M7 | Adversarial Hardening | Tier 5 adversarial testing using Challenger, code coverage hardening | M6 | PLANNED |

## Interface Contracts

### Router ↔ Inference / Cloud API
- `fn route_task(task: &str, context_tokens: usize) -> RouteDecision`
- `enum RouteDecision { Local, Cloud }`
- `fn compact_context(source_code: &str) -> String`
  - Replaces full function/class bodies with signatures to fit in local token budget (< 16,384 tokens).

### AST Indexer ↔ SQLite DB
- `fn index_repo(repo_path: &Path) -> Result<()>`
- `fn query_symbols(query: &str) -> Result<Vec<Symbol>>`
- SQLite DB file location: `.git/antigravity/session.db`
- `struct Symbol { path: String, hash: String, name: String, kind: String, start_line: usize, end_line: usize }`

### Agent Loop ↔ Tools
- `fn execute_tool(tool: ToolCall) -> Result<ToolOutput>`
- `struct ToolCall { command: String, args: Vec<String>, require_approval: bool }`
- Tool output must stream stdout, and support cancellation and timeouts.
