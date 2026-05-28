## 2026-05-26T16:20:14Z
Milestone M2: Infra & Inference for the Anti-Gravity 2.0 Hybrid Runtime.
All implementation code must be written to `/Users/macbook/mekong-cli/antigravity/hybrid_runtime`.

Key implementation items:
1. Initialize the Rust project in `antigravity/hybrid_runtime/` and write `Cargo.toml` with the required dependencies (tokio, reqwest, serde, serde_json, anyhow, clap, crossterm, rusqlite, tree-sitter, etc.).
2. Write launcher scripts in `antigravity/hybrid_runtime/`:
   - `launch-llama.sh`: Launch local llama.cpp server optimized for Apple Silicon (Metal, 8 threads, ctx-size 16384, flash-attn, no-mmap).
   - `run-claude-hybrid.sh`: Pre-flight check and build/run binary. Make both scripts executable.
3. Write `src/lib.rs` exporting: `pub mod inference;`, `pub mod router;`, `pub mod db;`, `pub mod indexer;`, `pub mod tools;`, `pub mod r#loop;`.
4. Write stub modules: `src/router.rs`, `src/db.rs`, `src/indexer.rs`, `src/tools.rs`, `src/loop.rs` as designed in the reports.
5. Write `src/inference.rs` implementing `InferenceDriver` trait, `LlamaDriver` (OpenAI chat compatible client), and `ClaudeDriver` (Anthropic Claude API client). Include connection check helper (`verify_connection`).
6. Write `src/main.rs` with `clap` arguments parsing, checking connection readiness for local/cloud, slash commands, interactive TTY loop (using crossterm raw mode) supporting Ctrl+C cancellation and streaming tokens.

Please read the design reports:
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m2_1/analysis.md`
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m2_2/analysis.md`
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m2_3/analysis.md`

Verify your work:
- Run `cargo check` and `cargo build` in `antigravity/hybrid_runtime` to ensure complete compilation.
- Document the commands and build/test verification results in your handoff report at `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_m2/handoff.md`.
