# Handoff Report: Milestone M2 Analysis & Design

This report summarizes the findings, reasoning, and proposed design for **Milestone M2 (Infra & Inference)** of the **Anti-Gravity 2.0 Hybrid Runtime**.

## 1. Observation
- **PROJECT.md** at `/Users/macbook/mekong-cli/PROJECT.md` specifies the layout and files for `antigravity/hybrid_runtime/` (lines 46-58), listing the target files: `Cargo.toml`, `launch-llama.sh`, `run-claude-hybrid.sh`, `src/main.rs`, and `src/inference.rs`.
- **SCOPE.md** at `/Users/macbook/mekong-cli/.agents/sub_orch_implementation/SCOPE.md` specifies the scope of Milestone M2 (lines 17-21) as: "Setup Rust workspace, local `llama.cpp` driver, scripts, connection verification".
- **Directory Check**: Running `list_dir` on `/Users/macbook/mekong-cli/antigravity` confirmed that `hybrid_runtime/` does not exist yet.
- **Reference Script**: Checked `/Users/macbook/mekong-cli/scripts/run-claude-hybrid.sh` which uses heuristic routing checks (e.g. matching `(refactor|architecture|design|rewrite|migrate|security)`) and falls back to `http://localhost:8080/v1` for local routing.
- **Reference Dockerfile**: Checked `/Users/macbook/mekong-cli/docker/Dockerfile.antigravity` which builds `llama.cpp` with `cmake` AVX2 flag and targets the `llama-server` binary.

## 2. Logic Chain
1. Since the `antigravity/hybrid_runtime` directory does not exist, the first implementation step is creating this folder and initializing a cargo binary project (via `cargo init`).
2. According to `PROJECT.md` and `SCOPE.md`, the hybrid runtime is built in Rust and requires tree-sitter, rusqlite, tokio, reqwest, crossterm, serde, etc. Therefore, a list of dependencies has been defined in `Cargo.toml`.
3. To support the local inference server on Apple Silicon, `launch-llama.sh` needs flags optimization such as CPU threads (Metal bound), flash attention, no-mmap, and port binding.
4. For remote escalation, Anthropic Claude API requires standard endpoints (`https://api.anthropic.com/v1/messages`), headers (`x-api-key`, `anthropic-version`), and message payload formatting.
5. In Rust, defining a trait `InferenceDriver` with async generation and connectivity checks allows dynamic dispatch (`Box<dyn InferenceDriver>`) or generic parameters, matching both `LlamaDriver` (local endpoint wrapper) and `ClaudeDriver` (Anthropic SDK/HTTP wrapper).
6. In `src/main.rs`, interactive raw TTY loop is requested to handle Observe-Retrieve-Reason-Patch-Execute-Verify phases and prompt confirmations. Crossterm's event poll combined with non-blocking stdin keypress checking enables this flow.

## 3. Caveats
- Since this is a read-only investigation, the files were not actually compiled or tested with a live model server. Correctness of GGUF command line options for `llama-server` is based on standard llama.cpp repository standards (built-in `--flash-attn`, `--threads`, `--n-gpu-layers`, and `--no-mmap` flags).
- Real Anthropic API calls could not be verified due to the CODE_ONLY network restriction constraint.

## 4. Conclusion
The infrastructure setup, dependency mapping, script structure, and Rust codebase layout are thoroughly designed. The implementation can proceed by initializing the `antigravity/hybrid_runtime/` directory, adding `Cargo.toml`, setting up launchers, and writing the structured Rust driver and CLI template.

## 5. Verification Method
1. **Directory Verification**: Confirm the creation of `antigravity/hybrid_runtime/` containing `Cargo.toml` and `src/`.
2. **Compilation**: Run `cargo check` and `cargo build` inside the runtime folder.
3. **Connectivity/Verify Action**: Start a mock local endpoint (or llama.cpp server) and run `cargo run -- verify` to ensure the connection checker returns `[OK]`.
