# Mekong CLI Development Setup

## Prerequisites

- Python 3.9+
- Poetry package manager
- Node.js 18+ (for CLI tools)
- Ollama 0.19+ (for local LLM inference on Apple Silicon)

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
   mekong version  # Should show Mekong CLI v3.0.0
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

Run the **full test suite** (6950+ tests) in the venv:

```bash
make test-venv
```

#### Seed Layer Tests Only

For quick validation without full test suite (69 unit tests, no Ollama needed):

```bash
make test-seed
```

#### Manual Testing

```bash
pytest tests/ -v --tb=short          # Full suite
pytest tests/seed/ -v --tb=short     # Seed layer only
```

## Ollama Setup (Local LLM Inference)

Mekong CLI uses Ollama 0.19+ for local model inference on Apple Silicon (M1/M2/M3). This provides free, private LLM access without API keys.

### Installation

1. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

   Or download from: https://ollama.ai/download

2. **Start Ollama service**:
   ```bash
   # Default: runs on http://127.0.0.1:11434
   ollama serve
   # Or run as daemon:
   brew services start ollama
   ```

3. **Pull models for development**:
   ```bash
   # Primary coding model (33B - recommended for M1 Max)
   ollama pull qwen2.5-coder:32b

   # Reasoning model (complex analysis)
   ollama pull deepseek-r1:32b

   # Lightweight audit model
   ollama pull qwen2.5-coder:7b
   ```

4. **Configure environment**:
   ```bash
   # Add to .zshrc or .bashrc
   export MEKONG_ENV=development
   export OPENAI_BASE_URL=http://127.0.0.1:11434/v1
   export OPENAI_API_KEY=ollama
   export OPENAI_MODEL=qwen2.5-coder:32b
   ```

5. **Start the Mekong farm**:
   ```bash
   npm run farm:start:dev
   # Or manually:
   bash bin/start_mekong_farm.sh --dev
   ```

### Model Specifications

#### Development (M1 Max 64GB — 100/100 Stack)
| Model | Size | Throughput | Purpose |
|-------|------|-----------|---------|
| qwen3:30b-a3b | 18GB | 53.4 tok/s | Primary (MoE, only 3B active) |
| deepseek-r1:32b | 19GB | 4.1 tok/s | Reasoning & complex analysis |
| **Total** | **38.7GB** | — | 25.3GB headroom for tools |

**Note:** qwen3:30b-a3b is Mixture-of-Experts with only 3B active parameters; hence fast throughput despite nominal size.

#### Production (B2B, M1 Pro 16GB minimum)
| Model | Size | Purpose |
|-------|------|---------|
| qwen2.5-coder:7b | 4GB | Fast inference, primary |
| qwen3:8b | 4.7GB | Fallback specialized tasks |
| **Total** | **14.7GB** | — |

### OpenAI-Compatible API

Ollama 0.19+ provides OpenAI-compatible endpoints:

**Chat Completions:**
```bash
curl http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-coder:32b",
    "messages": [{"role": "user", "content": "Write a function"}],
    "temperature": 0.7
  }'
```

**List Models:**
```bash
curl http://127.0.0.1:11434/v1/models
```

### Verification

Check that Ollama is running:
```bash
mekong status
# Output should show: Ollama configured (http://127.0.0.1:11434/v1)
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

### Ollama Connection Issues

If Mekong can't connect to Ollama:

1. **Check if Ollama is running**:
   ```bash
   curl http://127.0.0.1:11434/api/tags
   # Should return list of pulled models
   ```

2. **Verify correct endpoint**:
   ```bash
   echo $OPENAI_BASE_URL
   # Should be: http://127.0.0.1:11434/v1
   ```

3. **Restart Ollama**:
   ```bash
   brew services restart ollama
   # Or if running manually, stop and restart:
   # Press Ctrl+C, then: ollama serve
   ```

4. **Check memory**:
   - Dev environment needs 64GB+ for 32B models
   - Reduce model sizes if memory-constrained: use 7B models instead

### Model Download Failures

If `ollama pull` hangs or fails:

1. Check internet connection
2. Try with smaller model: `ollama pull qwen2.5-coder:7b`
3. Clear cache: `rm -rf ~/.ollama/` and retry
4. Check disk space (models require 20-30GB)