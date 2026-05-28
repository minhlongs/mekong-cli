## Review Summary

**Verdict**: REQUEST_CHANGES

The implementation of Milestone M2: Infra & Inference has been completed in terms of file structure and general CLI/API driver flow. However, several critical correctness and robustness issues have been identified, including an integrity violation via a facade connection check for the Claude API, a TTY staircase rendering bug, streaming loop leaks, and byte-boundary UTF-8 decoding corruption.

---

## Findings

### Critical Finding 1: INTEGRITY VIOLATION (Facade Implementation in `ClaudeDriver::verify_connection`)

- **What**: The connection check for the Cloud Claude route does not perform any actual network operations or API verification.
- **Where**: `antigravity/hybrid_runtime/src/inference.rs` (lines 264-273)
- **Why**: The trait documentation states `verify_connection` "Performs connectivity health-check." However, `ClaudeDriver::verify_connection` only performs local string validation:
  ```rust
  async fn verify_connection(&self) -> Result<()> {
      if self.api_key.trim().is_empty() {
          return Err(anyhow!("Anthropic API key is empty"));
      }
      if !self.api_key.starts_with("sk-ant-") {
          return Err(anyhow!("Invalid Anthropic API Key format (must start with sk-ant-)"));
      }
      Ok(())
  }
  ```
  If there is no network connection, or if the API key has been revoked/is invalid, the check still returns `Ok(())` as long as the key starts with `"sk-ant-"`. This is a facade implementation. Furthermore, the worker's handoff report misrepresented this claim by stating the driver was "complete with real connection check helpers".
- **Suggestion**: Perform a genuine, lightweight network request using the reqwest client (e.g. GET request to `https://api.anthropic.com` or a dummy chat message request with `max_tokens: 1`) to check actual network connectivity and key validity.

### Major Finding 2: Staircase Effect in TTY Raw Mode

- **What**: Output text displays vertical offsets (staircase effect) on newlines when streaming is active.
- **Where**: `antigravity/hybrid_runtime/src/main.rs` (lines 227-290)
- **Why**: When TTY raw mode is enabled (`crossterm::terminal::enable_raw_mode()`), standard terminal carriage return mapping is disabled. Newline characters (`\n`) received in the stream are printed verbatim using `print!("{}", token)`. This drops the cursor down one line but maintains the horizontal column.
- **Suggestion**: Manually translate `\n` to `\r\n` when raw mode is active, or use a printing helper.

### Major Finding 3: Stream Loop Leak on `[DONE]` Signal

- **What**: The streaming loop continues to read from the socket even after receiving a `[DONE]` completion marker.
- **Where**: `antigravity/hybrid_runtime/src/inference.rs` (lines 116-118)
- **Why**: When the `[DONE]` signal is received in `LlamaDriver::generate`, the code calls `break;`. However, this only breaks out of the *inner* line-splitting loop (`while let Some(pos) = line_buffer.find('\n')`). The outer loop (`while let Some(chunk_result) = stream.next().await`) continues executing, waiting for the HTTP connection to close, causing unnecessary latency.
- **Suggestion**: Use a flag (e.g., `let mut done = false;`) or return immediately to break the outer stream loop.

### Major Finding 4: UTF-8 Stream Decoding Corruption on Chunk Boundaries

- **What**: Multi-byte UTF-8 characters (like CJK or emoji) can be corrupted during stream rendering.
- **Where**: `antigravity/hybrid_runtime/src/inference.rs` (lines 107 and 234)
- **Why**: The code uses `String::from_utf8_lossy(&bytes)` on each raw network chunk before joining the bytes into lines. If a chunk boundary splits a multi-byte UTF-8 character, it will be decoded as a replacement character ``, causing permanent corruption in the text stream.
- **Suggestion**: Buffer raw bytes (`Vec<u8>`) and decode only complete UTF-8 byte sequences.

### Minor Finding 5: Double Compilation of Module `inference`

- **What**: The `inference.rs` module is compiled twice in the build graph.
- **Where**: `antigravity/hybrid_runtime/src/main.rs` (line 6) and `antigravity/hybrid_runtime/src/lib.rs` (line 1)
- **Why**: `main.rs` declares `mod inference;` instead of importing it as a library dependency. This leads to code duplication, slower builds, and duplicate types.
- **Suggestion**: Remove `mod inference;` from `main.rs` and use `use antigravity_hybrid_runtime::inference::...`.

### Minor Finding 6: Missing Interface Contract Stubs

- **What**: Interface functions required by downstream milestones are missing from the source stubs.
- **Where**: `antigravity/hybrid_runtime/src/indexer.rs` and `antigravity/hybrid_runtime/src/tools.rs`
- **Why**: `SCOPE.md` contracts require `fn index_repo`, `fn query_symbols`, and `fn execute_tool`. These are currently not stubbed, which will prevent downstreams from interacting with them out-of-the-box.
- **Suggestion**: Add function stubs matching the SCOPE signatures.

---

## Verified Claims

- **Files listed in handoff exist** → verified via file search (`find_by_name`) → **PASS**
- **Valid OpenAI request/response formatting for LlamaDriver** → verified via static inspection of struct serializers/deserializers → **PASS**
- **Valid Anthropic request/response formatting for ClaudeDriver** → verified via static inspection of serializers/deserializers → **PASS**
- **Real connection check implemented for ClaudeDriver** → verified via static inspection of `verify_connection` in `src/inference.rs` → **FAIL** (it is a local string check facade)

---

## Coverage Gaps

- **Binary Execution under Cargo** — risk level: **Medium** — recommendation: **Investigate** (Run `cargo check` and `cargo test` once permission environment issues are cleared).

---

## Unverified Items

- **Compilation clean status** — Cargo compile output could not be retrieved due to permission confirmation timeouts in this environment.
- **Interactive shell execution correctness** — TTY input loop could not be run interactively.
