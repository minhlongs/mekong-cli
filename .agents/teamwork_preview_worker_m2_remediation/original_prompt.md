## 2026-05-26T16:27:33Z

You are a versatile worker (teamwork_preview_worker_m2_remediation).
Your working directory is /Users/macbook/mekong-cli/.agents/teamwork_preview_worker_m2_remediation.
Your parent is 43e9a79e-50e7-4530-9e79-62ba7076968a (the implementation orchestrator).

Your task:
Modify the implementation of Milestone M2 in `/Users/macbook/mekong-cli/antigravity/hybrid_runtime` to fix the critical bugs and compliance issues reported by the reviewers.

Address the following items:
1. **Critical Finding (Integrity Violation)**:
   - Fix the facade implementation of `ClaudeDriver::verify_connection` in `src/inference.rs`. It must perform a genuine network call to Anthropic API (e.g. a POST request to `https://api.anthropic.com/v1/messages` with a tiny message containing content "Ping", `max_tokens: 1`, using Claude 3.5 Haiku or Sonnet model). Ensure that if the API key is incorrect/revoked or if offline, the method returns an `Err`.
2. **Major Finding - Staircase Effect**:
   - In `src/main.rs` streaming rendering, replace newlines `\n` in streamed tokens with `\r\n` when printing inside TTY raw mode to prevent the vertical offset staircase effect.
3. **Major Finding - Stream Loop Leak**:
   - In `src/inference.rs` (Llama and Claude drivers), when the `[DONE]` signal is received, break out of both the inner and outer loops immediately (e.g., return `Ok(collected)` or break both loops) so the connection is not held waiting for close.
4. **Major Finding - UTF-8 Chunk Boundaries**:
   - In `src/inference.rs`, accumulate streaming bytes in a `Vec<u8>` buffer and only convert complete segments/lines to String to prevent multibyte UTF-8 characters (like emojis or Vietnamese accents) from getting corrupted if split across chunk boundaries.
5. **Minor Finding - Double Compilation**:
   - In `src/main.rs`, remove `mod inference;` and import it from the library crate: `use antigravity_hybrid_runtime::inference::{...};`.
   - Setup `Cargo.toml` to build both a library target and a binary target.
6. **Minor Finding - Missing Downstream Stubs**:
   - Add `index_repo(repo_path: &Path) -> Result<()>` and `query_symbols(query: &str) -> Result<Vec<Symbol>>` to `src/indexer.rs`.
   - Add `execute_tool(tool: ToolCall) -> Result<ToolOutput>` to `src/tools.rs`.
7. **Minor Finding - TTY Raw Mode Recovery on Errors**:
   - In `src/main.rs`, wrap crossterm raw-mode enabling/disabling in a custom struct implementing `Drop` (a RawModeGuard) so that if any error or early return (using `?`) occurs, the guard goes out of scope and automatically disables raw mode and restores terminal TTY settings.
8. **Unused Dependency**:
   - Remove the unused `thiserror` dependency from `Cargo.toml`.

Please read the reviewer reports:
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_reviewer_m2_1/review.md`
- `/Users/macbook/mekong-cli/.agents/teamwork_preview_reviewer_m2_2/review.md`

Verify that the code compiles cleanly by running `cargo check` and `cargo build` in `antigravity/hybrid_runtime` and document the results in `/Users/macbook/mekong-cli/.agents/teamwork_preview_worker_m2_remediation/handoff.md`.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
