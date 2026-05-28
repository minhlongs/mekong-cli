# Milestone M2 Quality Review & Adversarial Challenge Report

## Review Summary

**Verdict**: REQUEST_CHANGES
**Status**: FAIL

## Findings

### [Critical] Finding 1: Facade Connection Check (Integrity Violation)
- **What**: The connection check for the Cloud driver (`ClaudeDriver::verify_connection`) is a facade implementation that performs no real connectivity verification.
- **Where**: `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/inference.rs` (lines 264-272)
- **Why**: The function only checks if the API key starts with `"sk-ant-"` and is not empty. It returns `Ok(())` without making any network requests or validating if the key is active and functional. This allows the system to erroneously report the Cloud route as `✅ READY` even when offline or when using a revoked API key.
- **Suggestion**: Make a minimal API call (e.g., to Anthropic's messages endpoint with a small max_tokens or an empty prompt) using a short timeout, or perform a TCP connection check to `api.anthropic.com` to verify actual reachability.

### [Major] Finding 2: Missing Downstream Interface Contract Stubs
- **What**: Stub functions for downstream milestones listed in `SCOPE.md` are completely missing.
- **Where**: `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/indexer.rs` and `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/tools.rs`
- **Why**: 
  - `src/indexer.rs` does not define `index_repo(repo_path: &Path) -> Result<()>` or `query_symbols(query: &str) -> Result<Vec<Symbol>>`.
  - `src/tools.rs` does not define `execute_tool(tool: ToolCall) -> Result<ToolOutput>`.
  - This violates the interface conformance requirements for downstream milestones.
- **Suggestion**: Add the required stub function signatures in their respective modules to satisfy the interface contracts.

### [Major] Finding 3: UTF-8 Stream Decoding Corruption
- **What**: Stream decoding of chunks directly using `String::from_utf8_lossy` will corrupt multi-byte characters.
- **Where**: `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/inference.rs` (lines 107 and 234)
- **Why**: Streaming responses arrive as arbitrary byte chunks. If a multi-byte UTF-8 character (e.g. Vietnamese text or emoji) is split across chunk boundaries, calling `from_utf8_lossy` on each chunk independently will fail to decode the split bytes correctly, leading to replacement characters `` in the output.
- **Suggestion**: Accumulate the incoming bytes in a buffer and only process complete SSE lines (which are separated by newlines and guaranteed to contain valid UTF-8 lines), or use a streaming UTF-8 decoder (such as using `tokio_util::codec::LinesCodec`).

### [Minor] Finding 4: Missing TTY Raw Mode Recovery on Errors
- **What**: If an error occurs during streaming generation, the terminal is left in raw mode.
- **Where**: `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/main.rs` (lines 207-290)
- **Why**: `crossterm::terminal::enable_raw_mode()?` is called. If any subsequent operations error out (e.g., polling fails, or reading events fails), the function returns early via the `?` operator. This bypasses `crossterm::terminal::disable_raw_mode()?`, leaving the user's terminal in raw mode, which breaks terminal input/output formatting.
- **Suggestion**: Wrap the raw mode management in a drop guard (custom struct implementing `Drop` that disables raw mode when dropped) or catch errors, disable raw mode, and then return the error.

### [Minor] Finding 5: Unused Dependency in Cargo.toml
- **What**: The `thiserror` dependency is declared in `Cargo.toml` but never imported or used.
- **Where**: `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/Cargo.toml` (line 30)
- **Why**: Keeping unused dependencies slows down build times and adds bloat to the workspace.
- **Suggestion**: Remove `thiserror = "2"` from `Cargo.toml`.

---

## Verified Claims

- **Helper drivers for inference startup exist**: verified via `view_file` → `launch-llama.sh` and `run-claude-hybrid.sh` exist and configure correct parameters.
- **Interactive TTY loop is implemented**: verified via `view_file` → `src/main.rs` contains interactive loop and slash commands.
- **Ctrl+C cancels streaming tokens**: verified via `view_file` → `src/main.rs` polls crossterm events for Ctrl+C and aborts tokio handle.

---

## Coverage Gaps

- **Database integration stub**: `src/db.rs` is an empty struct without the `.git/antigravity/session.db` schema definition or sqlite integration stub. Risk Level: Medium. Recommendation: Add db stub definition in M3.
- **Downstream tools execution stub**: `src/tools.rs` is missing `execute_tool`. Risk Level: Medium. Recommendation: Add the tool execution stub.

---

## Unverified Items

- **Cargo compilation success**: Cargo check/build was not executed because the user command execution permission prompt timed out. Verification of compilation must be run manually in the target shell.

---

# Adversarial Challenge Report

## Challenge Summary

**Overall risk assessment**: MEDIUM

## Challenges

### [High] Challenge 1: UTF-8 Stream Fragmentation
- **Assumption challenged**: Assumes bytes received from `bytes_stream()` map perfectly to whole UTF-8 characters.
- **Attack scenario**: Send response stream where multibyte character boundaries (like `ế` or `⚡`) fall exactly on chunk boundaries.
- **Blast radius**: Corrupted output text displayed to user.
- **Mitigation**: Buffer partial chunks or decode line-by-line using a line-oriented byte-to-string decoder.

### [Medium] Challenge 2: Terminal Raw Mode Hijack
- **Assumption challenged**: Assumes `stream_completion` always executes successfully to line 276.
- **Attack scenario**: Network error or tokio task panic occurs inside the loop before raw mode is disabled.
- **Blast radius**: User terminal is left in raw mode (character input is swallowed, newlines don't carriage return).
- **Mitigation**: Use a `Drop` guard to restore terminal raw mode state automatically.

### [Medium] Challenge 3: False Route Readyness
- **Assumption challenged**: Assumes `verify_connection()` actually validates cloud API availability.
- **Attack scenario**: Local computer has no internet access, or the API key format is correct but the key has been revoked.
- **Blast radius**: CLI reports cloud route as READY, but route fails immediately when executing tasks, leading to unhandled runtime errors.
- **Mitigation**: Execute a real HTTP check to Anthropic.
