# Mekong CLI Development Setup

## Prerequisites

- Python 3.9+
- Poetry package manager
- Node.js 18+ (for CLI tools)
- Rapid-MLX 0.6+ (for local LLM inference on Apple Silicon — 4.2x faster than Ollama)

### Installation Process

1. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   poetry add prometheus-client  # Added missing dependency
   ```

3. **Install in development mode**:
   ```bash
   pip install -e . --break-system-packages
   ```

4. **Verify installation**:
   ```bash
   export PATH="$HOME/Library/Python/3.9/bin:$PATH"
   mekong version  # Should show Mekong CLI v6.0.0
   mekong list     # Shows available recipes
   ```

### Key Features

- **Virtual Environment**: Managed via Poetry with all dependencies
- **Development Mode**: Changes to source code are immediately reflected
- **CLI Access**: Available system-wide after installation
- **Testing**: Run `poetry run pytest tests/` for unit tests

### Available Commands

- `mekong cook "<goal>"` - Full pipeline: Plan → Execute → Verify
- `mekong plan "<goal>"` - Plan only (preview steps, no execution)
- `mekong list` - List available recipes
- `mekong version` - Show version information
- `mekong --help` - Show all available commands

### Running Tests

#### Python 3.11 Virtual Environment (Recommended)

Create an isolated Python 3.11 venv with all dependencies:

```bash
make venv
source .venv/bin/activate
```

Run the **full test suite** (7040+ tests) in the venv:

```bash
make test-venv
```

#### Seed Layer Tests Only

For quick validation without full test suite (69 unit tests, no local LLM needed):

```bash
make test-seed
```

#### Manual Testing

```bash
pytest tests/ -v --tb=short          # Full suite
pytest tests/seed/ -v --tb=short     # Seed layer only
```

## Rapid-MLX Setup (Local LLM Inference)

Mekong CLI uses Rapid-MLX for local model inference on Apple Silicon (M1/M2/M3/M4). This provides free, private LLM access without API keys, with 4.2x faster throughput than Ollama.

### Installation

1. **Install Rapid-MLX**:
   ```bash
   brew install raullenchai/rapid-mlx/rapid-mlx
   ```

2. **Start the model server**:
   ```bash
   bash ~/start_qwen3.6.sh
   # Runs on http://127.0.0.1:11437
   ```

   The startup script launches Qwen3.6-35B-A3B-4bit with optimized flags:
   ```
   --port 11437
   --stream-interval 10
   --default-temperature 0
   --max-num-seqs 1
   --no-mllm
   --kv-cache-turboquant
   --no-thinking
   --gpu-memory-utilization 0.80
   --cache-memory-percent 0.35
   ```

3. **Auto-start on login** (optional):
   ```bash
   # Symlink the launch agent
   ln -sf ~/Library/LaunchAgents/com.user.mlx-qwen3.6.plist ~/Library/LaunchAgents/
   # Load it
   launchctl load ~/Library/LaunchAgents/com.user.mlx-qwen3.6.plist
   ```

4. **Configure environment**:
   ```bash
   # Add to .zshrc or .bashrc
   export MEKONG_ENV=development
   export OPENAI_BASE_URL=http://127.0.0.1:11437/v1
   export OPENAI_API_KEY=mlx
   export OPENAI_MODEL=qwen3.6-35b
   ```

5. **Start the Mekong farm**:
   ```bash
   npm run farm:start:dev
   # Or manually:
   bash bin/start_mekong_farm.sh --dev
   ```

### Model Specifications

#### Development (M1 Max 64GB — Rapid-MLX Qwen 3.6-35B-A3B-4bit)
| Model | Alias | Size | Throughput | Purpose |
|-------|-------|------|-----------|---------|
| mlx-community/Qwen3.6-35B-A3B-4bit | qwen3.6-35b | ~20GB | ~60 tok/s | Primary (256 MoE experts, 262K context) |

**Note:** Qwen 3.6-35B is Mixture-of-Experts with only 3B active parameters per token; 4-bit quantization reduces memory footprint while maintaining quality.

#### Production (B2B, M1 Pro 16GB minimum)
| Model | Size | Purpose |
|-------|------|---------|
| qwen3.6-35b | ~20GB | Primary model (Rapid-MLX) |

### OpenAI-Compatible API

Rapid-MLX provides OpenAI-compatible endpoints:

**Chat Completions:**
```bash
curl http://127.0.0.1:11437/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3.6-35b",
    "messages": [{"role": "user", "content": "Write a function"}],
    "temperature": 0
  }'
```

**List Models:**
```bash
curl http://127.0.0.1:11437/v1/models
```

### Verification

Check that Rapid-MLX is running:
```bash
mekong status
# Output should show: Rapid-MLX configured (http://127.0.0.1:11437/v1)
```

---

## Troubleshooting

### Python Version & Virtual Environment

If you have system Python 3.14+ that causes compatibility issues:

1. **Use the isolated venv instead** (recommended):
   ```bash
   make venv                      # Creates Python 3.11 isolated .venv
   source .venv/bin/activate
   make test-venv                 # Runs full test suite in venv
   ```

2. The venv approach eliminates system Python version conflicts entirely.

### Path Issues

If you encounter issues with the Python PATH:

1. Add the Python scripts directory to your shell profile:
   ```bash
   echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```

2. Or run commands with the explicit PATH:
   ```bash
   export PATH="$HOME/Library/Python/3.9/bin:$PATH" && mekong <command>
   ```

### Rapid-MLX Connection Issues

If Mekong can't connect to Rapid-MLX:

1. **Check if Rapid-MLX is running**:
   ```bash
   curl http://127.0.0.1:11437/v1/models
   # Should return list of available models
   ```

2. **Verify correct endpoint**:
   ```bash
   echo $OPENAI_BASE_URL
   # Should be: http://127.0.0.1:11437/v1
   ```

3. **Restart the server**:
   ```bash
   # Stop existing process (Ctrl+C or kill)
   bash ~/start_qwen3.6.sh
   ```

4. **Check memory**:
     - Dev environment needs 64GB+ for 35B models
     - Reduce memory utilization if constrained: adjust `--gpu-memory-utilization` flag

### Model Download Failures

If Rapid-MLX model download hangs or fails:

1. Check internet connection
2. Clear cache: `rm -rf ~/.cache/huggingface/` and retry
3. Check disk space (models require ~20GB)
4. Verify startup script: `cat ~/start_qwen3.6.sh`