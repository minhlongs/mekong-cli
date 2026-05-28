# Milestone M2 Analysis: Infrastructure & Inference for Anti-Gravity 2.0 Hybrid Runtime

## Executive Summary
This report defines the implementation plan, code structure, script wrappers, and library driver designs for **Milestone M2: Infrastructure & Inference** of the Anti-Gravity 2.0 Hybrid Runtime. 
Anti-Gravity 2.0 is a terminal-native, hybrid coding agent written in Rust. It utilizes a local llama.cpp server optimized for Apple Silicon (Qwen-35B model) and falls back to Anthropic's Claude API for complex reasoning or local token budget overflow (limit of 16,384 tokens).

Milestone M2 establishes the base environment:
1. **Rust Cargo Workspace** inside `antigravity/hybrid_runtime` with standard dependencies.
2. **Startup Bash Scripts** (`launch-llama.sh` and `run-claude-hybrid.sh`) optimized for low-latency inference on macOS Apple Silicon.
3. **Inference Drivers** (`src/inference.rs`) containing client logic for local llama.cpp `/v1/chat/completions` and cloud Anthropic Claude `/v1/messages`.
4. **CLI Entrypoint & Interactive TTY loop** (`src/main.rs`) providing a terminal interface, runtime state tracking, dynamic mode-switching, and stubbed agent loop hooks.

---

## 1. Rust Cargo Workspace Setup
The hybrid runtime is located inside `antigravity/hybrid_runtime/`. The workspace Cargo configuration will load all necessary libraries required for both local and cloud inference, SQLite persistence (M3), tree-sitter parsing (M3), regex routing (M4), and tools/agent-loop execution (M5).

### Proposed `Cargo.toml`
```toml
[package]
name = "antigravity-hybrid-runtime"
version = "2.0.0"
edition = "2021"
authors = ["OpenClaw Engine Team"]
description = "Terminal-native, local-first hybrid coding-agent runtime"

[dependencies]
# Async Runtime
tokio = { version = "1.35", features = ["full"] }
futures-util = "0.3"

# CLI Parsing & TTY Interaction
clap = { version = "4.4", features = ["derive"] }
crossterm = "0.27"
anyhow = "1.0"

# Logging and Instrumentation
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# Serialization & HTTP Requests
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
reqwest = { version = "0.11", features = ["json", "stream"] }
dotenvy = "0.15"

# Routing Engine & Context Compactor (Milestone M4)
regex = "1.10"

# AST Indexing & Database (Milestone M3)
rusqlite = { version = "0.29", features = ["bundled"] }
# tree-sitter bindings for symbol indexing
tree-sitter = "0.20"
tree-sitter-rust = "0.20"  # Co-located language parser examples
tree-sitter-python = "0.20"

# Helper for defining async traits
async-trait = "0.1"
```

---

## 2. Infrastructure Setup & Inference Drivers
To achieve low-latency local inference, `llama.cpp` must be configured specifically for macOS Apple Silicon unified memory architectures.

### Local Model Strategy (Qwen-35B)
- **Model Family**: Qwen-2.5-Coder-35B-Instruct.
- **Format**: GGUF format for CPU/GPU execution.
- **Quantization**: `q4_K_M` (4-bit Medium) which provides the best balance of VRAM consumption (~21GB) and logical reasoning accuracy.
- **Local Server**: We run `llama-server` (part of llama.cpp) to expose an OpenAI-compatible web API.

### Helper Scripts

#### A. Local inference script: `antigravity/hybrid_runtime/launch-llama.sh`
This script starts the local server with options optimized for Apple Silicon Metal.
```bash
#!/usr/bin/env zsh
set -euo pipefail

# Configuration
MODEL_DIR="${MODEL_DIR:-$HOME/.cache/antigravity/models}"
MODEL_NAME="qwen2.5-coder-35b-instruct-q4_k_m.gguf"
MODEL_PATH="${MODEL_DIR}/${MODEL_NAME}"
MODEL_URL="https://huggingface.co/Qwen/Qwen2.5-Coder-35B-Instruct-GGUF/resolve/main/${MODEL_NAME}"
PORT="${LLAMA_PORT:-8080}"
THREADS=8 # Target Performance cores on Apple Silicon

# Ensure directories exist
mkdir -p "${MODEL_DIR}"

# Download model if missing
if [[ ! -f "${MODEL_PATH}" ]]; then
  echo "[-] Local model Qwen-35B-GGUF is missing from ${MODEL_PATH}"
  echo "[-] Downloading model from Hugging Face (~21 GB)..."
  curl -L -o "${MODEL_PATH}" "${MODEL_URL}"
fi

# Check if port is in use
if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null; then
  echo "[!] Port ${PORT} is already in use. llama-server may already be running."
  exit 0
fi

echo "[*] Launching local llama.cpp server on port ${PORT}..."
echo "[*] Optimizations: Metal acceleration (Apple Silicon), ${THREADS} Performance threads, flash-attn, no-mmap"

# Launch llama-server
# Optimizations:
# -fa: Flash Attention (highly reduces memory usage / processing time for long contexts)
# --no-mmap: Locks file in VRAM to prevent system swap lags
# -c 16384: Context window of 16k tokens matching routing limits
exec llama-server \
  --model "${MODEL_PATH}" \
  --ctx-size 16384 \
  --threads ${THREADS} \
  --port ${PORT} \
  --host 127.0.0.1 \
  --flash-attn \
  --no-mmap
```

#### B. Cloud and Hybrid startup: `antigravity/hybrid_runtime/run-claude-hybrid.sh`
This script executes the built Rust executable, ensuring API keys and logging variables are initialized.
```bash
#!/usr/bin/env zsh
set -euo pipefail

# Locate workspace root
DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure ANTHROPIC_API_KEY is present
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  # Try loading from root .env
  if [[ -f "${DIR}/../../.env" ]]; then
    export $(grep -v '^#' "${DIR}/../../.env" | xargs)
  fi
fi

if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "[!] Error: ANTHROPIC_API_KEY environment variable is not set."
  echo "Please set it in your environment or write it in .env at root."
  exit 1
fi

# Build project
echo "[*] Building antigravity-hybrid-runtime in release mode..."
cargo build --release --manifest-path "${DIR}/Cargo.toml"

# Run binary
echo "[*] Executing runtime..."
exec "${DIR}/target/release/antigravity-hybrid-runtime" "$@"
```

---

## 3. Inference Driver Design (`src/inference.rs`)
The driver module manages communication with both the local `llama.cpp` server and Anthropic's Claude API.

### Code Skeleton for `src/inference.rs`
```rust
use std::pin::Pin;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use futures_util::stream::BoxStream;
use reqwest::header::{HeaderMap, HeaderValue, CONTENT_TYPE};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatMessage {
    pub role: String, // "system", "user", "assistant"
    pub content: String,
}

#[async_trait]
pub trait InferenceDriver: Send + Sync {
    /// Send a synchronous complete call
    async fn complete(&self, system_prompt: Option<&str>, messages: &[ChatMessage]) -> Result<String>;
    
    /// Send a streaming complete call
    async fn complete_stream(&self, system_prompt: Option<&str>, messages: &[ChatMessage]) 
        -> Result<BoxStream<'static, Result<String>>>;

    /// Health check to verify driver is active
    async fn verify_connection(&self) -> Result<()>;
}

// ==========================================
// Local Llama.cpp Driver (OpenAI-compatible)
// ==========================================
pub struct LlamaDriver {
    client: reqwest::Client,
    base_url: String,
}

impl LlamaDriver {
    pub fn new(host: &str, port: u16) -> Self {
        Self {
            client: reqwest::Client::new(),
            base_url: format!("http://{}:{}/v1", host, port),
        }
    }
}

#[derive(Serialize)]
struct OpenAIRequest {
    model: String,
    messages: Vec<ChatMessage>,
    stream: bool,
    max_tokens: Option<usize>,
}

#[derive(Deserialize)]
struct OpenAIResponse {
    choices: Vec<OpenAIChoice>,
}

#[derive(Deserialize)]
struct OpenAIChoice {
    message: ChatMessage,
}

#[async_trait]
impl InferenceDriver for LlamaDriver {
    async fn complete(&self, system_prompt: Option<&str>, messages: &[ChatMessage]) -> Result<String> {
        let mut final_messages = Vec::new();
        if let Some(sys) = system_prompt {
            final_messages.push(ChatMessage {
                role: "system".to_string(),
                content: sys.to_string(),
            });
        }
        final_messages.extend_from_slice(messages);

        let req_body = OpenAIRequest {
            model: "qwen-35b".to_string(),
            messages: final_messages,
            stream: false,
            max_tokens: Some(4096),
        };

        let response = self.client.post(&format!("{}/chat/completions", self.base_url))
            .json(&req_body)
            .send()
            .await?;

        if !response.status().is_success() {
            return Err(anyhow!("llama.cpp server returned error status: {}", response.status()));
        }

        let resp_json: OpenAIResponse = response.json().await?;
        resp_json.choices.get(0)
            .map(|choice| choice.message.content.clone())
            .ok_or_else(|| anyhow!("Received empty completion choice list from llama.cpp"))
    }

    async fn complete_stream(&self, _system_prompt: Option<&str>, _messages: &[ChatMessage]) 
        -> Result<BoxStream<'static, Result<String>>> 
    {
        // To be completed by implementer (streams chunks using server-sent events)
        Err(anyhow!("Streaming completion not yet implemented for llama.cpp driver"))
    }

    async fn verify_connection(&self) -> Result<()> {
        let response = self.client.get(&format!("{}/models", self.base_url))
            .send()
            .await?;
        if response.status().is_success() {
            Ok(())
        } else {
            Err(anyhow!("Failed health check connection to local llama.cpp endpoint"))
        }
    }
}

// ==========================================
// Cloud Anthropic Claude 3.5 Sonnet Driver
// ==========================================
pub struct ClaudeDriver {
    client: reqwest::Client,
    api_key: String,
    model: String,
}

impl ClaudeDriver {
    pub fn new(api_key: String, model: Option<&str>) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key,
            model: model.unwrap_or("claude-3-5-sonnet-20241022").to_string(),
        }
    }
}

#[derive(Serialize)]
struct ClaudeRequest {
    model: String,
    messages: Vec<ChatMessage>,
    max_tokens: usize,
    system: Option<String>,
    stream: bool,
}

#[derive(Deserialize)]
struct ClaudeResponse {
    content: Vec<ClaudeContentBlock>,
}

#[derive(Deserialize)]
struct ClaudeContentBlock {
    text: String,
}

#[async_trait]
impl InferenceDriver for ClaudeDriver {
    async fn complete(&self, system_prompt: Option<&str>, messages: &[ChatMessage]) -> Result<String> {
        let mut headers = HeaderMap::new();
        headers.insert("x-api-key", HeaderValue::from_str(&self.api_key)?);
        headers.insert("anthropic-version", HeaderValue::from_static("2023-06-01"));
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));

        let req_body = ClaudeRequest {
            model: self.model.clone(),
            messages: messages.to_vec(),
            max_tokens: 4096,
            system: system_prompt.map(|s| s.to_string()),
            stream: false,
        };

        let response = self.client.post("https://api.anthropic.com/v1/messages")
            .headers(headers)
            .json(&req_body)
            .send()
            .await?;

        if !response.status().is_success() {
            let error_text = response.text().await.unwrap_or_default();
            return Err(anyhow!("Anthropic API returned error: {}", error_text));
        }

        let resp_json: ClaudeResponse = response.json().await?;
        resp_json.content.get(0)
            .map(|block| block.text.clone())
            .ok_or_else(|| anyhow!("Anthropic response content array was empty"))
    }

    async fn complete_stream(&self, _system_prompt: Option<&str>, _messages: &[ChatMessage]) 
        -> Result<BoxStream<'static, Result<String>>> 
    {
        // To be completed by implementer (streams chunks from Anthropic events stream)
        Err(anyhow!("Streaming completion not yet implemented for Claude driver"))
    }

    async fn verify_connection(&self) -> Result<()> {
        if self.api_key.trim().is_empty() {
            return Err(anyhow!("Anthropic API Key is empty"));
        }
        // Minimal lookup check (e.g. prompt check) or format check.
        // Anthropic key must start with "sk-ant-"
        if !self.api_key.starts_with("sk-ant-") {
            return Err(anyhow!("Invalid Anthropic API Key format (must start with sk-ant-)"));
        }
        Ok(())
    }
}
```

---

## 4. CLI & Interactive TTY loop (`src/main.rs`)
The command line entrypoint manages configurations, starts execution modes, and handles the interactive TTY interface.

### Code Skeleton for `src/main.rs`
```rust
use std::io::{self, Write};
use clap::{Parser, ValueEnum};
use anyhow::Result;
use dotenvy::dotenv;
use tracing::{info, warn, Level};
use tracing_subscriber::FmtSubscriber;

mod inference;
use inference::{ChatMessage, ClaudeDriver, InferenceDriver, LlamaDriver};

#[derive(ValueEnum, Clone, Copy, Debug, PartialEq, Eq)]
enum Mode {
    Local,
    Cloud,
    Hybrid,
}

#[derive(Parser, Debug)]
#[command(author, version, about = "Anti-Gravity 2.0 Hybrid CLI")]
struct Args {
    /// Runtime Execution Mode
    #[arg(short, long, value_enum, default_value_t = Mode::Hybrid)]
    mode: Mode,

    /// Run in interactive TTY shell mode
    #[arg(short, long)]
    interactive: bool,

    /// Specify a single task target instead of interactive loop
    #[arg(short, long)]
    task: Option<String>,

    /// Local llama.cpp server host
    #[arg(long, default_value = "127.0.0.1")]
    local_host: String,

    /// Local llama.cpp server port
    #[arg(long, default_value_t = 8080)]
    local_port: u16,

    /// Cloud Anthropic model name override
    #[arg(long)]
    cloud_model: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    // 1. Load env variables
    dotenv().ok();

    // 2. Setup instrumentation
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::INFO)
        .finish();
    tracing::subscriber::set_global_default(subscriber)?;

    // 3. Parse CLI args
    let args = Args::parse();
    info!("Starting Anti-Gravity 2.0 Runtime in {:?} mode...", args.mode);

    // 4. Initialize drivers
    let (llama, claude) = init_drivers(&args).await;

    // 5. Select execution flow
    if args.interactive {
        run_interactive_loop(args.mode, llama, claude).await?;
    } else if let Some(task) = args.task {
        run_single_task(&task, args.mode, llama, claude).await?;
    } else {
        warn!("Neither --interactive nor --task was provided. Use --help for usage details.");
    }

    Ok(())
}

async fn init_drivers(args: &Args) -> (Option<LlamaDriver>, Option<ClaudeDriver>) {
    let llama = Some(LlamaDriver::new(&args.local_host, args.local_port));
    
    let anthropic_key = std::env::var("ANTHROPIC_API_KEY").unwrap_or_default();
    let claude = if !anthropic_key.is_empty() {
        Some(ClaudeDriver::new(anthropic_key, args.cloud_model.as_deref()))
    } else {
        None
    };

    (llama, claude)
}

async fn run_single_task(
    task: &str,
    mode: Mode,
    llama: Option<LlamaDriver>,
    claude: Option<ClaudeDriver>
) -> Result<()> {
    info!("Executing single task: {}", task);
    let messages = vec![ChatMessage {
        role: "user".to_string(),
        content: task.to_string(),
    }];

    // Simple routing demo
    match mode {
        Mode::Local => {
            if let Some(drv) = llama {
                let res = drv.complete(None, &messages).await?;
                println!("--- Local Qwen-35B Response ---\n{}", res);
            } else {
                return Err(anyhow::anyhow!("Llama driver not loaded"));
            }
        }
        Mode::Cloud => {
            if let Some(drv) = claude {
                let res = drv.complete(None, &messages).await?;
                println!("--- Claude Response ---\n{}", res);
            } else {
                return Err(anyhow::anyhow!("Claude API driver not loaded (missing API Key)"));
            }
        }
        Mode::Hybrid => {
            // M4 routing will integrate here
            println!("[Router] Routed to Local Qwen-35B (heuristic fallback demo)");
            if let Some(drv) = llama {
                let res = drv.complete(None, &messages).await?;
                println!("{}", res);
            }
        }
    }
    Ok(())
}

async fn run_interactive_loop(
    mut active_mode: Mode,
    llama: Option<LlamaDriver>,
    claude: Option<ClaudeDriver>
) -> Result<()> {
    println!("========================================================");
    println!("   Anti-Gravity 2.0 Terminal Hybrid Engine (M2 Stage)   ");
    println!("   Type /help for commands, /exit to quit               ");
    println!("========================================================");

    let stdin = io::stdin();
    let mut input = String::new();

    loop {
        print!("antigravity ({:?})> ", active_mode);
        io::stdout().flush()?;
        
        input.clear();
        if stdin.read_line(&mut input)? == 0 {
            break; // EOF
        }

        let trimmed = input.trim();
        if trimmed.is_empty() {
            continue;
        }

        // Handle slash commands
        if trimmed.starts_with('/') {
            let parts: Vec<&str> = trimmed.split_whitespace().collect();
            match parts[0] {
                "/exit" | "/quit" => {
                    println!("Exiting Anti-Gravity 2.0 shell.");
                    break;
                }
                "/help" => {
                    println!("Available commands:");
                    println!("  /exit, /quit          - Exit the TTY loop");
                    println!("  /mode <local|cloud|hybrid> - Switch active execution route");
                    println!("  /status               - Test connection health to providers");
                    println!("  /clear                - Clear the terminal screen");
                }
                "/mode" => {
                    if parts.len() < 2 {
                        println!("Usage: /mode <local|cloud|hybrid>");
                        continue;
                    }
                    match parts[1] {
                        "local" => active_mode = Mode::Local,
                        "cloud" => active_mode = Mode::Cloud,
                        "hybrid" => active_mode = Mode::Hybrid,
                        _ => println!("Invalid mode. Choose local, cloud, or hybrid"),
                    }
                    println!("Switched runtime mode to {:?}", active_mode);
                }
                "/status" => {
                    println!("Testing model connections...");
                    if let Some(ref drv) = llama {
                        match drv.verify_connection().await {
                            Ok(_) => println!("[-] Local Llama.cpp (Qwen-35B): ONLINE"),
                            Err(e) => println!("[-] Local Llama.cpp (Qwen-35B): OFFLINE ({})", e),
                        }
                    } else {
                        println!("[-] Local Llama.cpp (Qwen-35B): DRIVER NOT CONFIGURED");
                    }

                    if let Some(ref drv) = claude {
                        match drv.verify_connection().await {
                            Ok(_) => println!("[-] Cloud Anthropic (Claude-3.5): KEY VALIDATED"),
                            Err(e) => println!("[-] Cloud Anthropic (Claude-3.5): KEY INVALID ({})", e),
                        }
                    } else {
                        println!("[-] Cloud Anthropic (Claude-3.5): KEY MISSING OR DRIVER NOT LOADED");
                    }
                }
                "/clear" => {
                    print!("{}[2J{}[1;1H", 27 as char, 27 as char);
                    io::stdout().flush()?;
                }
                _ => println!("Unknown command. Type /help for assistance."),
            }
            continue;
        }

        // Standard prompt execution
        println!("[Core Loop] Simulating Observe-Retrieve-Reason-Patch-Execute-Verify loop...");
        let messages = vec![ChatMessage {
            role: "user".to_string(),
            content: trimmed.to_string(),
        }];

        match active_mode {
            Mode::Local => {
                if let Some(ref drv) = llama {
                    match drv.complete(None, &messages).await {
                        Ok(res) => println!("\nQwen-35B:\n{}", res),
                        Err(e) => println!("\n[Error] Local generation failed: {}", e),
                    }
                }
            }
            Mode::Cloud => {
                if let Some(ref drv) = claude {
                    match drv.complete(None, &messages).await {
                        Ok(res) => println!("\nClaude:\n{}", res),
                        Err(e) => println!("\n[Error] Claude generation failed: {}", e),
                    }
                }
            }
            Mode::Hybrid => {
                println!("[Router] Routing decision (Local vs Cloud) will process here in M4.");
                println!("[Router] Fallback to Local Llama Driver...");
                if let Some(ref drv) = llama {
                    match drv.complete(None, &messages).await {
                        Ok(res) => println!("\nQwen-35B:\n{}", res),
                        Err(e) => println!("\n[Error] Local generation failed: {}", e),
                    }
                }
            }
        }

        // Mock interaction step (approvals simulation for M5)
        println!("\n--- Tool Run Sandbox Approval (Simulation) ---");
        println!("Goal requested path manipulation: write dummy output file.");
        if confirm_action("Approve tool execution? (y/N): ") {
            println!("[System] Action executed successfully.");
        } else {
            println!("[System] Action aborted by operator.");
        }
        println!("-----------------------------------------------\n");
    }

    Ok(())
}

fn confirm_action(prompt: &str) -> bool {
    print!("{}", prompt);
    let _ = io::stdout().flush();
    let mut response = String::new();
    if io::stdin().read_line(&mut response).is_ok() {
        let trimmed = response.trim().to_lowercase();
        trimmed == "y" || trimmed == "yes"
    } else {
        false
    }
}
```

---

## 5. Step-by-Step Implementation Guide
For the implementing agent, follow these sequential steps to establish and verify Milestone M2:

1. **Workspace Setup**:
   - Create directories: `antigravity/hybrid_runtime` and `antigravity/hybrid_runtime/src`.
   - Write the `Cargo.toml` workspace manifest in the `hybrid_runtime` root.
   - Create the source files: `src/main.rs` and `src/inference.rs`. Let `src/main.rs` link `mod inference;`.

2. **Driver Implementation**:
   - Implement the `InferenceDriver` trait.
   - Write `/v1/chat/completions` payload construction for `LlamaDriver`.
   - Write `/v1/messages` payload construction for `ClaudeDriver`. Add the headers required by Anthropic.
   - Implement the connection check helpers (`verify_connection`).

3. **CLI & TTY shell**:
   - Implement parameter options using `clap` in `src/main.rs`.
   - Set up standard interactive TTY prompt handling.
   - Implement slash commands `/quit`, `/exit`, `/help`, `/status`, and `/mode`.
   - Add a simulation workflow inside the loop to verify how streaming messages and TTY keyboard/approval responses will behave.

4. **Script Scaffolding**:
   - Write `launch-llama.sh` in `antigravity/hybrid_runtime/` and mark it executable (`chmod +x launch-llama.sh`).
   - Write `run-claude-hybrid.sh` in `antigravity/hybrid_runtime/` and mark it executable (`chmod +x run-claude-hybrid.sh`).

---

## 6. Verification and Testing Method
To verify that Milestone M2 has been completed correctly, run these manual validation commands:

1. **Compilation Check**:
   ```bash
   cargo check --manifest-path antigravity/hybrid_runtime/Cargo.toml
   cargo build --manifest-path antigravity/hybrid_runtime/Cargo.toml
   ```
2. **Help Arguments & Initialization Verification**:
   ```bash
   cargo run --manifest-path antigravity/hybrid_runtime/Cargo.toml -- --help
   ```
3. **Verify Slash Commands (Local Mode / Offline test)**:
   - Run in interactive mode:
     ```bash
     cargo run --manifest-path antigravity/hybrid_runtime/Cargo.toml -- --interactive --mode local
     ```
   - Test command `/status` (Llama should print OFFLINE, Claude should print KEY MISSING or KEY VALIDATED depending on environment variables).
   - Test command `/mode cloud` and observe active prompt mode changing to `(Cloud)`.
   - Test command `/exit` and verify loop terminates immediately with zero exit code.
4. **Shell script permissions check**:
   ```bash
   test -x antigravity/hybrid_runtime/launch-llama.sh && echo "launch-llama.sh is executable"
   test -x antigravity/hybrid_runtime/run-claude-hybrid.sh && echo "run-claude-hybrid.sh is executable"
   ```
5. **Driver Connection tests**:
   - Start a mock HTTP server or use a real llama-server to verify `verify_connection()` parses `/models` response correctly.
