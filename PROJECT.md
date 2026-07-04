# Project: Anti-Gravity 2.0 Hybrid Runtime

## Architecture
Anti-Gravity 2.0 is a terminal-native, hybrid local-first coding-agent runtime written in Rust. It integrates local Apple Silicon Metal-accelerated inference (Qwen-35B) with Anthropic's Claude 3.5 Sonnet/Opus API for escalation.

```
                  ┌──────────────────────┐
                  │      Terminal UI     │
                  └──────────┬───────────┘
                             │
                  ┌──────────▼───────────┐
                  │    Routing Engine    │
                  └────┬───────────┬─────┘
                       │           │
           (Local Route)           (Cloud Route)
                       │           │
     ┌─────────────────▼──┐     ┌──▼──────────────────┐
     │   Local Qwen-35B   │     │    Claude API       │
     │   (via llama.cpp)  │     │ (Anthropic Backend) │
     └─────────┬──────────┘     └──────────┬──────────┘
               │                           │
               └─────────────┬─────────────┘
                             │
               ┌─────────────▼─────────────┐
               │      Core Agent Loop      │
               │  (Observe-Retrieve-Reason │
               │   -Patch-Execute-Verify)  │
               └─────────────┬─────────────┘
                             │
               ┌─────────────▼─────────────┐
               │    AST Indexer & DB       │
               │   (tree-sitter/SQLite)    │
               └───────────────────────────┘
```

### Components
1. **CLI / UI Entrypoint**: Startup < 2s, interactive approval TTY, streaming status.
2. **Inference Driver**: Local `llama.cpp` integration optimized for Apple Silicon (Metal, 8 Performance threads, flash-attn, no-mmap) via launch/run scripts.
3. **Routing Engine**: Heuristic classifier based on regex, token budget (16k limit for local), and latency limits. Implements context compaction using AST headers.
4. **AST Indexer & Persistence**: tree-sitter or ast-grep based symbol extraction, SQLite persistence at `.git/antigravity/session.db` (file paths, hash, class, method, kind, line numbers). Under 5ms symbol query latency.
5. **Agent Loop & Tools**: Tool orchestrator (local shell, git, ripgrep, tree-sitter, ast-grep) with stdout streaming, timeouts, and interactive confirmation for write/delete/execute.

## Code Layout
The project is built as a Rust workspace or binary inside `antigravity/hybrid_runtime`:
```
antigravity/hybrid_runtime/
├── Cargo.toml
├── launch-llama.sh
├── run-claude-hybrid.sh
└── src/
    ├── main.rs            # CLI Entrypoint, Interactive TTY loops
    ├── router.rs          # Hybrid Routing & Context Compactor
    ├── loop.rs            # Agent Loop (observe -> retrieve -> reason -> patch -> execute -> diff -> validate)
    ├── db.rs              # SQLite Session & State Persistence
    ├── indexer.rs         # tree-sitter/ast-grep symbol indexer
    ├── tools.rs           # Tool runner (shell, git, rg, ast-grep) with cancellation & timeouts
    └── inference.rs       # llama.cpp client & model interface
```

## Milestones

| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | E2E Test Suite | Build test infrastructure and Tiers 1-4 tests (Dual Track) | None | DONE (TEST_READY.md published) |
| M2 | Infra & Inference | Setup Rust workspace, `launch-llama.sh`, `run-claude-hybrid.sh`, local llama.cpp driver | None | DONE |
| M3 | SQLite & AST | SQLite schema at `.git/antigravity/session.db`, tree-sitter indexer, query latency < 5ms | M2 | IN_PROGRESS (Conv: 43e9a79e-50e7-4530-9e79-62ba7076968a) |
| M4 | Routing Engine | Regex heuristics, context compactor, token budget router | M3 | PLANNED |
| M5 | Agent Loop & Tools | Core loop, tools (shell, git, rg), interactive TTY blocks, streaming output | M4 | PLANNED |
| M6 | E2E & Verification | Run Tiers 1-4 tests, fix failures, run forensic audit | M1, M5 | PLANNED |
| M7 | Adversarial Hardening | Phase 2 coverage hardening (Tier 5) using Challenger | M6 | PLANNED |

## Interface Contracts

### Router ↔ Inference / Cloud API
- `fn route_task(task: &str, context_tokens: usize) -> RouteDecision`
- `enum RouteDecision { Local, Cloud }`
- `fn compact_context(source_code: &str) -> String` (replaces full source with class/method headers to keep tokens < 16,384)

### AST Indexer ↔ SQLite DB
- `fn index_repo(repo_path: &Path) -> Result<()>`
- `fn query_symbols(query: &str) -> Result<Vec<Symbol>>`
- `struct Symbol { path: String, hash: String, name: String, kind: String, start_line: usize, end_line: usize }`

### Agent Loop ↔ Tools
- `fn execute_tool(tool: ToolCall) -> Result<ToolOutput>`
- `struct ToolCall { command: String, args: Vec<String>, require_approval: bool }`
- Output must stream stdout and support cancellation/timeouts.
