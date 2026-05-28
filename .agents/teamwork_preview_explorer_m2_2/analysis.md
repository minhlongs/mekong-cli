# Milestone M2: Infra & Inference Analysis & Strategy

This document outlines the design, dependencies, code structures, and implementation plan for Milestone M2 of the Anti-Gravity 2.0 Hybrid Runtime.

---

## 1. Directory and Existing Code Status

We conducted a complete search of the `/Users/macbook/mekong-cli/antigravity` workspace:
- **`antigravity/` exists** as a Python package containing `core/` and `infrastructure/` subfolders (e.g., `ab_testing_engine.py`, `agent_swarm.py`, `mcp_server.py`).
- **`antigravity/hybrid_runtime` does NOT exist**. There is no Rust code, no `Cargo.toml`, and no inference drivers currently present in this path.
- Therefore, the implementation of Milestone M2 will be a completely greenfield Rust project in `/Users/macbook/mekong-cli/antigravity/hybrid_runtime`.

---

## 2. Dependencies and Cargo.toml Setup

We propose a standalone Cargo package structure for `hybrid_runtime` rather than nested workspace member configuration to ensure simplicity and self-contained execution.

### Proposed `antigravity/hybrid_runtime/Cargo.toml`
```toml
[package]
name = "antigravity"
version = "2.0.0"
edition = "2021"
authors = ["OpenClaw CTO"]
description = "Anti-Gravity 2.0 Hybrid Local-First Agent Runtime"

[dependencies]
# Async Runtime
tokio = { version = "1.40", features = ["full"] }
futures = "0.3"
tokio-stream = "0.1"

# HTTP Client for LLM Inference Backends
reqwest = { version = "0.12", features = ["json", "stream"] }

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# CLI & Configuration
clap = { version = "4.5", features = ["derive"] }
dotenvy = "0.15"

# Database & Parsing (For downstream Milestones M3-M5, included now for compile check)
rusqlite = { version = "0.32", features = ["bundled"] }
tree-sitter = "0.24"

# Logic & Tool Execution Helper
regex = "1.10"
anyhow = "1.0"
thiserror = "2.0"
crossterm = "0.28" # Clean TTY checking and screen output
```

---

## 3. Inference Driver & Helper Scripts

Two scripts are required under `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/`:
1. `launch-llama.sh`: Launches a local llama.cpp server optimized for Apple Silicon (Metal).
2. `run-claude-hybrid.sh`: Validates connection health and starts the hybrid agent CLI.

### launch-llama.sh
```bash
#!/bin/bash
# launch-llama.sh
# Configure and launch a local llama.cpp server optimized for Apple Silicon (M1/M2/M3 Max)

set -euo pipefail

# Configurable defaults
MODEL_PATH=${1:-"./models/qwen2.5-coder-32b-instruct-q4_k_m.gguf"}
LLAMA_SERVER=${LLAMA_SERVER_BIN:-"llama-server"}
PORT=${PORT:-8080}
THREADS=${THREADS:-8} # Optimized for 8 Performance cores on M-series chips

echo "=========================================================="
echo "Starting local llama.cpp server for Anti-Gravity 2.0"
echo "Model: $MODEL_PATH"
echo "Port: $PORT"
echo "Threads: $THREADS (Performance Cores)"
echo "Optimizations: Metal Offload, Flash Attention, no-mmap"
echo "=========================================================="

# Run llama-server with strict RAM allocation and Metal acceleration
# --n-gpu-layers 99 forces all layers to Metal GPU
# --flash-attn enables Flash Attention
# --no-mmap loads weights directly to RAM, preventing UMA thrashing
# --ctx-size 16384 matches local token routing constraints
exec "$LLAMA_SERVER" \
  --model "$MODEL_PATH" \
  --port "$PORT" \
  --threads "$THREADS" \
  --n-gpu-layers 99 \
  --flash-attn \
  --no-mmap \
  --ctx-size 16384 \
  --host 127.0.0.1
```

### run-claude-hybrid.sh
```bash
#!/bin/bash
# run-claude-hybrid.sh
# Run the hybrid runtime with env configuration and pre-flight health checks

set -e

# Load .env file if it exists in the hybrid_runtime directory or project root
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
elif [ -f ../../.env ]; then
  export $(grep -v '^#' ../../.env | xargs)
fi

# Pre-flight check: llama.cpp server
echo "Performing pre-flight health checks..."
LLAMA_URL=${LLAMA_API_URL:-"http://localhost:8080"}
set +e
LLAMA_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$LLAMA_URL/health" --max-time 2 || echo "offline")
set -e

if [ "$LLAMA_STATUS" = "200" ] || [ "$LLAMA_STATUS" = "ok" ]; then
  echo "✅ Local llama.cpp server detected on $LLAMA_URL"
else
  echo "⚠️ Warning: Local llama.cpp server is not responding on $LLAMA_URL."
  echo "   If you route tasks locally, they will fail. Start it with './launch-llama.sh'."
fi

# Pre-flight check: Anthropic Claude Key
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "❌ Error: ANTHROPIC_API_KEY is not set in environment or .env."
  echo "   Cloud routing will fail."
  exit 1
else
  echo "✅ ANTHROPIC_API_KEY environment variable detected."
fi

# Build and run target
echo "Building binary..."
cargo build

echo "Executing hybrid runtime..."
exec ./target/debug/antigravity "$@"
```

---

## 4. Proposed Code Structure for `src/`

For compile checks to pass in M2, we must establish the modules in `src/` with stub signatures.

### `src/inference.rs`
This file implements client drivers for local `llama.cpp` and Anthropic `Claude API` using `reqwest` with support for streaming tokens.

```rust
use anyhow::{anyhow, Result};
use futures::Stream;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::pin::Pin;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ChatMessage {
    pub role: String,
    pub content: String,
}

pub struct LlamaClient {
    base_url: String,
    client: Client,
}

impl LlamaClient {
    pub fn new(base_url: String) -> Self {
        Self {
            base_url,
            client: Client::new(),
        }
    }

    pub async fn ping(&self) -> bool {
        let url = format!("{}/health", self.base_url);
        match self.client.get(&url).send().await {
            Ok(resp) => resp.status().is_success(),
            Err(_) => false,
        }
    }

    pub async fn generate_completion(&self, messages: Vec<ChatMessage>) -> Result<String> {
        let url = format!("{}/v1/chat/completions", self.base_url);
        
        #[derive(Serialize)]
        struct LlamaRequest {
            messages: Vec<ChatMessage>,
            temperature: f32,
            stream: bool,
        }

        #[derive(Deserialize)]
        struct Choice {
            message: ChatMessage,
        }

        #[derive(Deserialize)]
        struct LlamaResponse {
            choices: Vec<Choice>,
        }

        let payload = LlamaRequest {
            messages,
            temperature: 0.2,
            stream: false,
        };

        let response = self.client.post(&url)
            .json(&payload)
            .send()
            .await?
            .json::<LlamaResponse>()
            .await?;

        response.choices.first()
            .map(|c| c.message.content.clone())
            .ok_or_else(|| anyhow!("No choices returned from llama.cpp server"))
    }
}

pub struct ClaudeClient {
    api_key: String,
    client: Client,
}

impl ClaudeClient {
    pub fn new(api_key: String) -> Self {
        Self {
            api_key,
            client: Client::new(),
        }
    }

    pub async fn generate_completion(&self, messages: Vec<ChatMessage>, system: Option<String>) -> Result<String> {
        let url = "https://api.anthropic.com/v1/messages";
        
        #[derive(Serialize)]
        struct ClaudeRequest {
            model: String,
            messages: Vec<ChatMessage>,
            system: Option<String>,
            max_tokens: usize,
            temperature: f32,
        }

        #[derive(Deserialize)]
        struct Content {
            text: String,
        }

        #[derive(Deserialize)]
        struct ClaudeResponse {
            content: Vec<Content>,
        }

        let payload = ClaudeRequest {
            model: "claude-3-5-sonnet-20241022".to_string(),
            messages,
            system,
            max_tokens: 4096,
            temperature: 0.2,
        };

        let response = self.client.post(url)
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&payload)
            .send()
            .await?
            .json::<ClaudeResponse>()
            .await?;

        response.content.first()
            .map(|c| c.text.clone())
            .ok_or_else(|| anyhow!("No content returned from Claude API"))
    }
}
```

### `src/main.rs`
The entrypoint parses CLI flags, checks connection readiness for local/cloud routes, and implements the TTY approval loops.

```rust
use clap::Parser;
use std::io::{self, Write};
use antigravity::inference::{ChatMessage, LlamaClient, ClaudeClient};

#[derive(Parser, Debug)]
#[command(name = "antigravity", version = "2.0.0", about = "Anti-Gravity 2.0 Hybrid Agent Loop CLI")]
struct Args {
    /// Task description or prompt
    #[arg(short, long)]
    task: Option<String>,

    /// Bypass router and force a route (local or cloud)
    #[arg(short, long)]
    route: Option<String>,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // 1. Startup latency benchmark start
    let start_time = std::time::Instant::now();
    dotenvy::dotenv().ok();

    let args = Args::parse();
    println!("🚀 Starting Anti-Gravity 2.0 Runtime...");

    // 2. Load API Configurations
    let llama_url = std::env::var("LLAMA_API_URL").unwrap_or_else(|_| "http://localhost:8080".to_string());
    let anthropic_key = std::env::var("ANTHROPIC_API_KEY");

    let llama_client = LlamaClient::new(llama_url.clone());
    let claude_client = anthropic_key.map(ClaudeClient::new);

    // 3. Ping local llama server
    let local_ready = llama_client.ping().await;
    let cloud_ready = claude_client.is_some();

    println!("- Local Route (llama.cpp @ {}): {}", llama_url, if local_ready { "✅ READY" } else { "❌ OFFLINE" });
    println!("- Cloud Route (Claude API): {}", if cloud_ready { "✅ READY" } else { "❌ NO API KEY" });

    let init_duration = start_time.elapsed();
    println!("- Initialization completed in: {:?}", init_duration);
    if init_duration.as_secs_f64() > 2.0 {
        println!("⚠️ Warning: Initialization took longer than the 2.0s requirement!");
    }

    // 4. Interactive loop or single command evaluation
    if let Some(task) = args.task {
        println!("\nExecuting Task: {}", task);
        
        // Mock classification decision
        let route = args.route.unwrap_or_else(|| "local".to_string());
        println!("Classification decision: [{}]", route);

        if route == "cloud" {
            if let Some(ref client) = claude_client {
                let msg = vec![ChatMessage { role: "user".to_string(), content: task }];
                println!("Streaming response from Claude...");
                match client.generate_completion(msg, None).await {
                    Ok(resp) => println!("Response: {}", resp),
                    Err(e) => println!("Error running cloud inference: {}", e),
                }
            } else {
                println!("Error: Cloud route chosen but ANTHROPIC_API_KEY is missing");
            }
        } else {
            let msg = vec![ChatMessage { role: "user".to_string(), content: task }];
            println!("Streaming response from Local Qwen...");
            match llama_client.generate_completion(msg).await {
                Ok(resp) => println!("Response: {}", resp),
                Err(e) => println!("Error running local inference: {}", e),
            }
        }

        // TTY Approval Loop demonstration for destructive tool execution
        let mock_tool_call = "rm -rf target/debug/build";
        let approved = prompt_approval(mock_tool_call)?;
        if approved {
            println!("Action approved. Simulating execution...");
        } else {
            println!("Action denied. Aborting execution.");
        }

    } else {
        // TTY interactive mode
        println!("\nInteractive prompt mode enabled. Enter 'exit' to quit.");
        loop {
            print!("antigravity> ");
            io::stdout().flush()?;

            let mut input = String::new();
            io::stdin().read_line(&mut input)?;
            let input = input.trim();

            if input == "exit" || input == "quit" {
                break;
            }

            if input.is_empty() {
                continue;
            }

            println!("Processing input: {}", input);
        }
    }

    Ok(())
}

/// Helper function to request user approval in interactive TTY loop
fn prompt_approval(action: &str) -> io::Result<bool> {
    // Check if stdin is a terminal (tty)
    use std::io::IsTerminal;
    if !io::stdin().is_terminal() {
        println!("Non-interactive TTY detected. Denying destructive operation: '{}'", action);
        return Ok(false);
    }

    loop {
        print!("⚠️ [Approval Required] Run command: '{}'? (y/yes/n/no): ", action);
        io::stdout().flush()?;

        let mut input = String::new();
        io::stdin().read_line(&mut input)?;
        let trimmed = input.trim().to_lowercase();

        if trimmed == "y" || trimmed == "yes" {
            return Ok(true);
        } else if trimmed == "n" || trimmed == "no" {
            return Ok(false);
        }
    }
}
```

### Supporting Module Stubs
To allow compile testing in Milestone M2, the following stub files should be created:

#### `src/lib.rs`
```rust
pub mod inference;
pub mod router;
pub mod db;
pub mod indexer;
pub mod tools;
pub mod r#loop; // named r#loop because loop is a keyword
```

#### `src/router.rs`
```rust
pub enum RouteDecision {
    Local,
    Cloud,
}

pub fn route_task(_task: &str, _context_tokens: usize) -> RouteDecision {
    RouteDecision::Local
}

pub fn compact_context(source_code: &str) -> String {
    source_code.to_string() // mock compaction
}
```

#### `src/db.rs`
```rust
pub struct SessionDb;

impl SessionDb {
    pub fn new() -> Self {
        Self
    }
}
```

#### `src/indexer.rs`
```rust
pub struct Symbol {
    pub path: String,
    pub hash: String,
    pub name: String,
    pub kind: String,
    pub start_line: usize,
    pub end_line: usize,
}
```

#### `src/tools.rs`
```rust
pub struct ToolCall {
    pub command: String,
    pub args: Vec<String>,
    pub require_approval: bool,
}

pub struct ToolOutput {
    pub stdout: String,
    pub exit_code: i32,
}
```

#### `src/loop.rs`
```rust
pub struct AgentLoop;
```

---

## 5. Precise Implementation Strategy & Steps

The implementer agent can run through the following steps to complete Milestone M2:

1. **Workspace Initialization**:
   - Create directories: `mkdir -p antigravity/hybrid_runtime/src`
   - Write `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/Cargo.toml` as defined.
   - Create empty stub files inside `src/`: `lib.rs`, `router.rs`, `db.rs`, `indexer.rs`, `tools.rs`, `loop.rs`.

2. **Inference Client Drivers**:
   - Write `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/inference.rs`.
   - Ensure the JSON serializers match llama.cpp's OpenAI-compatible router specs and Anthropic message specifications.

3. **Entrypoint & Loop Control**:
   - Write `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/src/main.rs`.
   - Implement the `prompt_approval` interactive verification utility using `std::io::IsTerminal` for safe TTY check.

4. **Inference Scripts**:
   - Write `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/launch-llama.sh` and make it executable (`chmod +x launch-llama.sh`).
   - Write `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/run-claude-hybrid.sh` and make it executable (`chmod +x run-claude-hybrid.sh`).

5. **Verification**:
   - Run `cargo check` and `cargo build` in `antigravity/hybrid_runtime` to ensure complete code compilation.
   - Execute `./run-claude-hybrid.sh --help` to verify the wrapper launch script operates correctly.
