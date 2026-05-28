# Milestone M2: Infra & Inference — Implementation Analysis & Design

This document details the architecture, code layouts, helper scripts, and implementation roadmap for **Milestone M2 (Infra & Inference)** of the **Anti-Gravity 2.0 Hybrid Runtime**.

---

## 1. Executive Summary

Milestone M2 establishes the base execution infrastructure for the hybrid agent. It targets:
- Creating the Rust binary project under `antigravity/hybrid_runtime`.
- Establishing helper scripts to launch a local Metal-accelerated inference server (llama.cpp) and start the hybrid agent.
- Defining and implementing the `InferenceDriver` abstraction in Rust, wrapping both the local `llama.cpp` endpoint (using Qwen-35B) and the remote Anthropic Claude API.
- Implementing connection verification logic to test connectivity to both inference backends.
- Structuring the CLI CLI/TTY loop skeleton in `src/main.rs` to support terminal interactions, raw-mode inputs, and streaming outputs.

---

## 2. Workspace Layout & Cargo Configuration

The runtime will be initialized as a standalone Rust project within the workspace folder `antigravity/hybrid_runtime`.

### 2.1 File Structure
```text
antigravity/hybrid_runtime/
├── Cargo.toml
├── launch-llama.sh
├── run-claude-hybrid.sh
└── src/
    ├── main.rs
    └── inference.rs
```

### 2.2 Cargo.toml Specification
The `Cargo.toml` file will pull standard dependencies aligned with other crates in the Mekong CLI repository. It includes `tokio` for async orchestration, `reqwest` for HTTP clients, `crossterm` for TTY raw mode, and serializing libraries.

```toml
[package]
name = "antigravity-hybrid-runtime"
version = "0.1.0"
edition = "2021"
authors = ["OpenClaw Engine Team"]
description = "Anti-Gravity 2.0 Hybrid Local-First Coding-Agent Runtime"

[dependencies]
# Async Runtime
tokio = { version = "1", features = ["full"] }
tokio-stream = "0.1"
futures = "0.3"

# Network & Web APIs
reqwest = { version = "0.12", features = ["json", "stream"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# Database & Parsing (Preloaded for M3)
rusqlite = { version = "0.31", features = ["bundled"] }
tree-sitter = "0.20"

# CLI & Terminal Interface
clap = { version = "4.4", features = ["derive"] }
crossterm = "0.27"

# Utilities
anyhow = "1"
thiserror = "1"
regex = "1"
dotenv = "0.15"
async-trait = "0.1"
```

---

## 3. Inference Server Launchers

Two bash scripts handle the initialization and orchestration of the inference endpoints.

### 3.1 `launch-llama.sh`
This script launches the local llama.cpp server configured for Apple Silicon Macbooks. It targets high-performance Metal acceleration with low memory footprint using `--no-mmap` and Flash Attention.

```bash
#!/usr/bin/env bash
# launch-llama.sh
# Starts the local llama.cpp server running Qwen-35B on Apple Silicon.

set -euo pipefail

# Configuration
MODEL_PATH="${1:-models/qwen2.5-coder-35b-instruct-q4_k_m.gguf}"
PORT="${PORT:-8080}"
THREADS="${THREADS:-8}" # Target 8 performance threads on Apple Silicon M-series

echo "=== Anti-Gravity 2.0: Local llama.cpp Launcher ==="
echo "Model Path : $MODEL_PATH"
echo "Port       : $PORT"
echo "Threads    : $THREADS"
echo "================================================="

if [ ! -f "$MODEL_PATH" ]; then
  echo "Error: Model file not found at $MODEL_PATH."
  echo "Please download the Qwen-35B GGUF or configure MODEL_PATH."
  exit 1
fi

# Execute llama-server with Apple Silicon / Metal optimizations:
# -t 8: 8 CPU threads (bound to Performance Cores)
# -ngl 999: Offload all model layers to Apple Silicon GPU (Metal)
# -c 16384: Set context window to 16,384 tokens
# --flash-attn: Enable Flash Attention to speed up inference and save memory
# --no-mmap: Do not map model into memory, load directly
exec llama-server \
  --model "$MODEL_PATH" \
  --port "$PORT" \
  --threads "$THREADS" \
  --ctx-size 16384 \
  --n-gpu-layers 999 \
  --flash-attn \
  --no-mmap \
  --host 127.0.0.1
```

### 3.2 `run-claude-hybrid.sh`
This script launches the hybrid runtime binary, facilitating escalation variables.

```bash
#!/usr/bin/env bash
# run-claude-hybrid.sh
# Runs the antigravity-hybrid-runtime binary, loading environment variables.

set -euo pipefail

# Load local environment if .env exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Check for Anthropic API Key for Cloud route Escalation
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "Warning: ANTHROPIC_API_KEY environment variable is empty."
  echo "Cloud route escalations will fail. Running local-only mode."
fi

# Build and run the Rust binary
cargo run --release -- "$@"
```

---

## 4. Inference Drivers (`src/inference.rs`)

`src/inference.rs` wraps llama.cpp's local server and Anthropic's Claude API under a common async Rust interface.

### 4.1 Data Models and Driver Trait
```rust
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use reqwest::header::{HeaderMap, HeaderValue, CONTENT_TYPE};
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc::UnboundedSender;
use tokio_stream::StreamExt;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Message {
    pub role: Role,
    pub content: String,
}

#[derive(Debug, Serialize, Deserialize, Clone, Copy, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    System,
    User,
    Assistant,
}

#[async_trait]
pub trait InferenceDriver: Send + Sync {
    /// Generates LLM completion streaming chunks through the transmitter if provided.
    async fn generate(
        &self,
        system_prompt: &str,
        messages: &[Message],
        stream_tx: Option<UnboundedSender<String>>,
    ) -> Result<String>;

    /// Performs connectivity health-check.
    async fn verify_connection(&self) -> Result<()>;
}
```

### 4.2 LlamaDriver (Local Server)
Implements an OpenAI chat completion client targeting `http://127.0.0.1:8080/v1/chat/completions`.
```rust
pub struct LlamaDriver {
    client: reqwest::Client,
    endpoint: String,
    model: String,
}

impl LlamaDriver {
    pub fn new(endpoint: &str, model: &str) -> Self {
        Self {
            client: reqwest::Client::new(),
            endpoint: endpoint.to_string(),
            model: model.to_string(),
        }
    }
}

#[derive(Serialize)]
struct LlamaChatRequest<'a> {
    model: &'a str,
    messages: Vec<Message>,
    temperature: f32,
    stream: bool,
}

#[derive(Deserialize)]
struct ChatCompletionChunk {
    choices: Vec<ChatCompletionChunkChoice>,
}

#[derive(Deserialize)]
struct ChatCompletionChunkChoice {
    delta: ChatCompletionChunkDelta,
}

#[derive(Deserialize)]
struct ChatCompletionChunkDelta {
    content: Option<String>,
}

#[async_trait]
impl InferenceDriver for LlamaDriver {
    async fn generate(
        &self,
        system_prompt: &str,
        messages: &[Message],
        stream_tx: Option<UnboundedSender<String>>,
    ) -> Result<String> {
        let mut full_messages = Vec::new();
        if !system_prompt.is_empty() {
            full_messages.push(Message {
                role: Role::System,
                content: system_prompt.to_string(),
            });
        }
        full_messages.extend_from_slice(messages);

        let request_payload = LlamaChatRequest {
            model: &self.model,
            messages: full_messages,
            temperature: 0.2,
            stream: stream_tx.is_some(),
        };

        let url = format!("{}/v1/chat/completions", self.endpoint);
        let response = self.client.post(&url).json(&request_payload).send().await?;

        if !response.status().is_success() {
            let err_body = response.text().await.unwrap_or_default();
            return Err(anyhow!("llama.cpp error status {}: {}", response.status(), err_body));
        }

        if let Some(tx) = stream_tx {
            let mut stream = response.bytes_stream();
            let mut collected = String::new();

            while let Some(chunk_result) = stream.next().await {
                let bytes = chunk_result?;
                let text = String::from_utf8_lossy(&bytes);
                for line in text.lines() {
                    if let Some(data) = line.strip_prefix("data: ") {
                        let data = data.trim();
                        if data == "[DONE]" {
                            break;
                        }
                        if let Ok(chunk) = serde_json::from_str::<ChatCompletionChunk>(data) {
                            if let Some(content) = chunk.choices.get(0).and_then(|c| c.delta.content.as_ref()) {
                                collected.push_str(content);
                                let _ = tx.send(content.clone());
                            }
                        }
                    }
                }
            }
            Ok(collected)
        } else {
            #[derive(Deserialize)]
            struct ChatCompletionResponse {
                choices: Vec<ChatCompletionChoice>,
            }
            #[derive(Deserialize)]
            struct ChatCompletionChoice {
                message: Message,
            }
            let res = response.json::<ChatCompletionResponse>().await?;
            let content = res.choices.get(0)
                .map(|c| c.message.content.clone())
                .ok_or_else(|| anyhow!("Empty choices in response"))?;
            Ok(content)
        }
    }

    async fn verify_connection(&self) -> Result<()> {
        let url = format!("{}/health", self.endpoint);
        let res = self.client.get(&url).send().await?;
        if res.status().is_success() {
            Ok(())
        } else {
            Err(anyhow!("llama.cpp health endpoint returned {}", res.status()))
        }
    }
}
```

### 4.3 ClaudeDriver (Anthropic Cloud API)
Communicates with `https://api.anthropic.com/v1/messages`.
```rust
pub struct ClaudeDriver {
    client: reqwest::Client,
    api_key: String,
    model: String,
}

impl ClaudeDriver {
    pub fn new(api_key: &str, model: &str) -> Self {
        Self {
            client: reqwest::Client::new(),
            api_key: api_key.to_string(),
            model: model.to_string(),
        }
    }
}

#[derive(Serialize)]
struct ClaudeRequest<'a> {
    model: &'a str,
    max_tokens: usize,
    system: &'a str,
    messages: Vec<Message>,
    stream: bool,
}

#[derive(Deserialize)]
#[serde(tag = "type")]
enum ClaudeEvent {
    #[serde(rename = "content_block_delta")]
    ContentBlockDelta { delta: ClaudeDelta },
    #[serde(other)]
    Unknown,
}

#[derive(Deserialize)]
struct ClaudeDelta {
    text: String,
}

#[async_trait]
impl InferenceDriver for ClaudeDriver {
    async fn generate(
        &self,
        system_prompt: &str,
        messages: &[Message],
        stream_tx: Option<UnboundedSender<String>>,
    ) -> Result<String> {
        let mut headers = HeaderMap::new();
        headers.insert("x-api-key", HeaderValue::from_str(&self.api_key)?);
        headers.insert("anthropic-version", HeaderValue::from_static("2023-06-01"));
        headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));

        let request_payload = ClaudeRequest {
            model: &self.model,
            max_tokens: 4096,
            system: system_prompt,
            messages: messages.to_vec(),
            stream: stream_tx.is_some(),
        };

        let response = self.client
            .post("https://api.anthropic.com/v1/messages")
            .headers(headers)
            .json(&request_payload)
            .send()
            .await?;

        if !response.status().is_success() {
            let err_body = response.text().await.unwrap_or_default();
            return Err(anyhow!("Claude API error status {}: {}", response.status(), err_body));
        }

        if let Some(tx) = stream_tx {
            let mut stream = response.bytes_stream();
            let mut collected = String::new();

            while let Some(chunk_result) = stream.next().await {
                let bytes = chunk_result?;
                let text = String::from_utf8_lossy(&bytes);
                for line in text.lines() {
                    if let Some(data) = line.strip_prefix("data: ") {
                        let data = data.trim();
                        if let Ok(event) = serde_json::from_str::<ClaudeEvent>(data) {
                            if let ClaudeEvent::ContentBlockDelta { delta } = event {
                                collected.push_str(&delta.text);
                                let _ = tx.send(delta.text);
                            }
                        }
                    }
                }
            }
            Ok(collected)
        } else {
            #[derive(Deserialize)]
            struct ClaudeResponse {
                content: Vec<ClaudeContent>,
            }
            #[derive(Deserialize)]
            struct ClaudeContent {
                text: String,
            }
            let res = response.json::<ClaudeResponse>().await?;
            let content = res.content.get(0)
                .map(|c| c.text.clone())
                .ok_or_else(|| anyhow!("Empty content in Claude response"))?;
            Ok(content)
        }
    }

    async fn verify_connection(&self) -> Result<()> {
        if self.api_key.is_empty() {
            return Err(anyhow!("Anthropic API key is empty"));
        }
        // Dry run / verify credentials via simple prompt
        let messages = vec![Message {
            role: Role::User,
            content: "Hello".to_string(),
        }];
        self.generate("You are a helper.", &messages, None).await?;
        Ok(())
    }
}
```

---

## 5. CLI Entrypoint & Interactive TTY Interface (`src/main.rs`)

`src/main.rs` builds CLI handling and a crossterm-based raw TTY loop template.

```rust
use clap::{Parser, Subcommand};
use crossterm::{
    event::{self, Event, KeyCode, KeyEvent, KeyModifiers},
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
    ExecutableCommand,
};
use std::io::{self, Write};
use std::time::Duration;
use tokio::sync::mpsc;

mod inference;
use inference::{ClaudeDriver, InferenceDriver, LlamaDriver, Message, Role};

#[derive(Parser, Debug)]
#[command(name = "antigravity")]
#[command(about = "Anti-Gravity 2.0 Hybrid Local-First Agent CLI", long_about = None)]
struct Cli {
    #[arg(short, long, default_value = "http://127.0.0.1:8080")]
    llama_url: String,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Perform connection health-check on Llama and Claude backends
    Verify,
    /// Run a task using the agent loop (interactive or batch)
    Run {
        /// Task input prompt
        #[arg(short, long)]
        task: String,

        /// Escalation strategy force overrides (local/cloud)
        #[arg(short, long)]
        route: Option<String>,
    },
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    dotenv::dotenv().ok();
    let cli = Cli::parse();

    match cli.command {
        Commands::Verify => {
            println!("Starting backend verification check...");

            // 1. Verify Local Llama Server
            let llama = LlamaDriver::new(&cli.llama_url, "Qwen3.6-35B-A3B");
            match llama.verify_connection().await {
                Ok(_) => println!(" [OK] Local Llama server responded successfully."),
                Err(e) => println!(" [FAIL] Local Llama server check failed: {}", e),
            }

            // 2. Verify Claude API Connection
            let api_key = std::env::var("ANTHROPIC_API_KEY").unwrap_or_default();
            let claude = ClaudeDriver::new(&api_key, "claude-3-5-sonnet-latest");
            match claude.verify_connection().await {
                Ok(_) => println!(" [OK] Cloud Anthropic Claude API connected successfully."),
                Err(e) => println!(" [FAIL] Claude API verification failed: {}", e),
            }
        }
        Commands::Run { task, route } => {
            println!("Initializing Agent Loop for task: \"{}\"", task);

            // Determine routing
            let route_choice = route.unwrap_or_else(|| "local".to_string());
            println!("Routing decision: {}", route_choice);

            // Initialize respective driver
            let driver: Box<dyn InferenceDriver> = if route_choice.to_lowercase() == "cloud" {
                let api_key = std::env::var("ANTHROPIC_API_KEY").unwrap_or_default();
                Box::new(ClaudeDriver::new(&api_key, "claude-3-5-sonnet-latest"))
            } else {
                Box::new(LlamaDriver::new(&cli.llama_url, "Qwen3.6-35B-A3B"))
            };

            // Run interactive TTY loops template
            println!("Entering interactive execution mode...");
            run_tty_agent_loop(driver, &task).await?;
        }
    }

    Ok(())
}

/// Runs the interactive TTY approval flow using Crossterm raw mode.
async fn run_tty_agent_loop(driver: Box<dyn InferenceDriver>, task: &str) -> anyhow::Result<()> {
    let mut stdout = io::stdout();

    // Enable Raw Mode for Crossterm keyboard listener
    enable_raw_mode()?;
    stdout.execute(EnterAlternateScreen)?;

    let mut messages = vec![Message {
        role: Role::User,
        content: task.to_string(),
    }];

    // Communication loop
    loop {
        // Draw TTY GUI representation
        draw_ui(&mut stdout, "Observe & Retrieve Phase: Reading workspace...", true)?;

        // Spin off background inference call
        let (tx, mut rx) = mpsc::unbounded_channel();
        
        let system_prompt = "You are a coding agent. Generate step execution plans.";
        let messages_clone = messages.clone();
        
        // Spawn inference driving task
        let driver_ref = &driver;
        let tokio_handle = tokio::spawn(async move {
            driver_ref.generate(system_prompt, &messages_clone, Some(tx)).await
        });

        // TTY Event loop inside active inference
        let mut response_output = String::new();
        let mut loop_break = false;

        loop {
            // Check for new tokens from inference channel
            while let Ok(token) = rx.try_recv() {
                response_output.push_str(&token);
                print!("{}", token);
                let _ = stdout.flush();
            }

            // Read keyboard input non-blockingly (timeout checking)
            if event::poll(Duration::from_millis(50))? {
                if let Event::Key(key) = event::read()? {
                    // Check for cancel / interrupt (Ctrl+C)
                    if key.code == KeyCode::Char('c') && key.modifiers.contains(KeyModifiers::CONTROL) {
                        println!("\nOperation Cancelled by user.");
                        tokio_handle.abort();
                        loop_break = true;
                        break;
                    }
                }
            }

            // Check if inference process is complete
            if tokio_handle.is_finished() {
                break;
            }
        }

        if loop_break {
            break;
        }

        // Retrieve final result from thread
        let result = tokio_handle.await?;
        match result {
            Ok(output) => {
                messages.push(Message {
                    role: Role::Assistant,
                    content: output.clone(),
                });

                // Request user validation / approval step
                draw_ui(&mut stdout, "Proposed action: Execute local script. Approve? (y/n/q)", false)?;
                
                let mut approve = false;
                loop {
                    if let Event::Key(key) = event::read()? {
                        match key.code {
                            KeyCode::Char('y') | KeyCode::Char('Y') => {
                                approve = true;
                                break;
                            }
                            KeyCode::Char('n') | KeyCode::Char('N') | KeyCode::Char('q') => {
                                break;
                            }
                            _ => {}
                        }
                    }
                }

                if approve {
                    println!("\nAction approved! Executing...");
                    // Add result output logic...
                } else {
                    println!("\nAction rejected. Exiting agent execution loop.");
                    break;
                }
            }
            Err(e) => {
                println!("\nInference generation failed: {}", e);
                break;
            }
        }

        // Safety break for loop demo
        break;
    }

    // Restore terminal
    stdout.execute(LeaveAlternateScreen)?;
    disable_raw_mode()?;

    Ok(())
}

fn draw_ui(stdout: &mut io::Stdout, status: &str, is_working: bool) -> anyhow::Result<()> {
    // Basic terminal draw logic
    write!(stdout, "\r\x1b[2J\x1b[H")?; // Clear screen
    writeln!(stdout, "==================================================")?;
    writeln!(stdout, " Anti-Gravity Runtime v2.0 - Agent Execution      ")?;
    writeln!(stdout, "==================================================")?;
    writeln!(stdout, " Status: {}", status)?;
    if is_working {
        writeln!(stdout, " [ WORKING ] Generating response stream...")?;
    } else {
        writeln!(stdout, " [ PENDING APPROVAL ] Press 'y' to continue, 'n' to quit.")?;
    }
    writeln!(stdout, "--------------------------------------------------")?;
    stdout.flush()?;
    Ok(())
}
```

---

## 6. Verification and Validation Strategy

To verify the correct setup of Milestone 2:
1. **Compilation Check**: The workspace compiles without warnings:
   ```bash
   cd antigravity/hybrid_runtime
   cargo build
   ```
2. **Local Llama Verification (Tier 1 Test simulation)**:
   Ensure `llama.cpp` server is mock-started or running locally:
   ```bash
   ./launch-llama.sh path/to/dummy_model.gguf
   # Should trigger validation checks in CLI:
   cargo run -- verify
   ```
3. **Escalation Routing Integration**:
   Verify fallback routing mechanism behaves properly under `--route cloud` vs `--route local` flags.
