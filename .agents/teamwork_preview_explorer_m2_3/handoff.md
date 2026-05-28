# Handoff Report: Milestone M2: Infra & Inference Exploration

## 1. Observation
- The directory `/Users/macbook/mekong-cli/antigravity/` exists, but `/Users/macbook/mekong-cli/antigravity/hybrid_runtime` is currently absent. Listing the directory contents of `antigravity/` returned:
  ```json
  {"name":"__init__.py"}
  {"name":"core","isDir":true}
  {"name":"infrastructure","isDir":true}
  {"name":"mcp_server.py","sizeBytes":"13255"}
  {"name":"vibe_kanban","isDir":true}
  {"name":"vibe_kanban_bridge.py","sizeBytes":"6776"}
  ```
- The project specification `/Users/macbook/mekong-cli/PROJECT.md` on lines 46-58 defines the expected folder structure for the hybrid runtime:
  ```
  antigravity/hybrid_runtime/
  ├── Cargo.toml
  ├── launch-llama.sh
  ├── run-claude-hybrid.sh
  └── src/
      ├── main.rs            # CLI Entrypoint, Interactive TTY loops
      ├── router.rs          # Hybrid Routing & Context Compactor
      ├── loop.rs            # Agent Loop
      ├── db.rs              # SQLite Session
      ├── indexer.rs         # tree-sitter
      ├── tools.rs           # Tool runner
      └── inference.rs       # llama.cpp client & model interface
  ```
- The implementation scope document `/Users/macbook/mekong-cli/.agents/sub_orch_implementation/SCOPE.md` on line 21 defines the scope of Milestone M2:
  "Setup Rust workspace, local `llama.cpp` driver, scripts, connection verification"

## 2. Logic Chain
1. Because `antigravity/hybrid_runtime/` is currently missing, the first step of the implementation must be compiling a `Cargo.toml` configuration defining the binary package and its dependencies.
2. The runtime requires local inference drivers (llama.cpp) and cloud drivers (Anthropic Claude API). A unified `InferenceDriver` trait should be declared in `src/inference.rs` to abstract both.
3. Local model execution on macOS Apple Silicon is highly dependent on compiler optimizations and hardware access (Metal acceleration, performance thread alignment, flash-attn, and no-mmap to lock pages in memory). Writing a `launch-llama.sh` wrapper is necessary to ensure these parameters are run correctly.
4. The core loop of Anti-Gravity 2.0 requires an interactive TTY interface. Establishing a slash-command CLI loop in `src/main.rs` with simulation stubs enables verification of input/output and loop control flows before actual tools are integrated.

## 3. Caveats
- This investigation assumes that the operator running `launch-llama.sh` has a local installation of `llama-server` in their shell PATH. If `llama-server` is not installed, the script will output guidance rather than running.
- Model downloads for Qwen-35B instruct (~21 GB) are skipped if the GGUF file already exists in the designated directory path `$HOME/.cache/antigravity/models`.

## 4. Conclusion
Milestone M2 is fully scoped and designed. The proposed blueprints for `Cargo.toml`, `launch-llama.sh`, `run-claude-hybrid.sh`, `src/inference.rs`, and `src/main.rs` have been saved to `/Users/macbook/mekong-cli/.agents/teamwork_preview_explorer_m2_3/analysis.md`. The implementer can directly write and compile these files to successfully check off M2.

## 5. Verification Method
Verify implementation using the following commands:
1. **Compilation**:
   ```bash
   cargo build --manifest-path antigravity/hybrid_runtime/Cargo.toml
   ```
2. **Execution**:
   - Run in interactive mode:
     ```bash
     cargo run --manifest-path antigravity/hybrid_runtime/Cargo.toml -- --interactive
     ```
   - Test command `/status` and `/mode` inside the prompt shell.
   - Verify prompt exit command `/exit` yields successful return code.
3. **Permissions**:
   - Check if scripts are executable:
     ```bash
     test -x antigravity/hybrid_runtime/launch-llama.sh
     test -x antigravity/hybrid_runtime/run-claude-hybrid.sh
     ```
