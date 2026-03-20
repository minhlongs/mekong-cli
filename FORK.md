# Forking Mekong CLI

**Quick start guide for developers** — Get Mekong CLI running locally in 5 minutes.

---

## Prerequisites

- Python 3.9+
- Node.js 18+ (for frontend/landing)
- Git
- LLM API key (OpenRouter, Anthropic, or local Ollama)

---

## Quick Start

### 1. Fork and Clone

```bash
# Option A: GitHub CLI
gh repo fork mekong-cli/mekong-cli --clone
cd mekong-cli

# Option B: Manual fork
# 1. Click "Fork" button on GitHub
# 2. Clone your fork:
git clone https://github.com/YOUR_USERNAME/mekong-cli.git
cd mekong-cli
```

### 2. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### 3. Setup Environment

```bash
# Run setup script
bash scripts/setup-dev.sh

# Or quick setup (skip optional steps)
bash scripts/setup-dev.sh --quick
```

### 4. Configure LLM Provider

**Option A: OpenRouter (Recommended)**

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

**Option B: Local Ollama (Free)**

```bash
# Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=qwen2.5-coder
```

**Option C: Anthropic Direct**

```bash
export LLM_BASE_URL=https://api.anthropic.com
export LLM_API_KEY=sk-ant-yourkey
export LLM_MODEL=claude-sonnet-4-20251022
```

### 5. Add to Shell (Optional)

```bash
# Add to ~/.zshrc or ~/.bashrc for persistence
echo 'export LLM_BASE_URL=https://openrouter.ai/api/v1' >> ~/.zshrc
echo 'export LLM_API_KEY=sk-or-v1-yourkey' >> ~/.zshrc
echo 'export LLM_MODEL=anthropic/claude-sonnet-4' >> ~/.zshrc
source ~/.zshrc
```

---

## Verify Installation

### Step 1: Check Version

```bash
mekong version
# Expected: Mekong CLI v5.0.0
```

### Step 2: Run Self-Test

```bash
make setup && make self-test
# Expected: Score 100/100, 3588+ tests passing
```

### Step 3: Test Commands

```bash
# Check command count
mekong help
# Expected: 319 commands listed

# Test a simple command
mekong status
# Expected: Current LLM configuration

# Test cook command
mekong cook "Create a Python function that adds two numbers"
# Expected: AI generates working code
```

### Step 4: Verify Skills

```bash
# List available skills
ls .claude/skills/
# Expected: 463+ skill definitions
```

---

## Verification Checklist

Mark these as you complete:

- [ ] `mekong version` shows v5.0.0
- [ ] `make self-test` passes 100/100
- [ ] `mekong help` shows 319 commands
- [ ] `mekong status` shows LLM config
- [ ] `/cook` command works
- [ ] `/plan` command works
- [ ] 463+ skills in `.claude/skills/`

---

## Project Structure

```
mekong-cli/
├── src/                    # Python CLI core (PEV engine)
├── mekong/                 # Adapters, infra, daemon
├── .claude/skills/         # 463 skill definitions
├── .claude/commands/       # 319 command definitions
├── factory/contracts/      # 410 JSON machine contracts
├── frontend/landing/       # Next.js landing (agencyos.network)
├── scripts/                # Setup and utility scripts
└── tests/                  # Test suite
```

---

## Troubleshooting

### Test Failures

```bash
# Reinstall dependencies
pip uninstall mekong-cli
pip install -e ".[dev]"

# Run tests with verbose output
python3 -m pytest tests/ -v --tb=short

# Common fix: clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

### Command Not Found

```bash
# Ensure you're in project root
cd ~/mekong-cli

# Reload shell configuration
source scripts/shell-init.sh

# Or restart your terminal
```

### LLM Connection Errors

```bash
# Check environment variables
echo $LLM_BASE_URL
echo $LLM_API_KEY

# Test API key (OpenRouter)
curl -H "Authorization: Bearer $LLM_API_KEY" https://openrouter.ai/api/v1/models

# Try different provider
export LLM_BASE_URL=http://localhost:11434/v1  # Ollama
export LLM_MODEL=qwen2.5-coder
```

### Permission Denied (macOS/Linux)

```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x mekong/infra/*.sh
```

### Next.js Build Errors (Frontend)

```bash
cd frontend/landing

# Clean install
rm -rf node_modules package-lock.json .next
npm install

# Rebuild
npm run build

# If Turbopack fails, use Webpack
npm run build -- --no-turbopack
```

---

## Next Steps

1. **Read Documentation**
   - [CONTRIBUTING.md](CONTRIBUTING.md) — Contribution guidelines
   - [QUICKSTART.md](QUICKSTART.md) — Quick start for users
   - [docs/COMMANDS.md](docs/COMMANDS.md) — Full command reference

2. **Explore Commands**
   ```bash
   mekong help                    # List all commands
   mekong cook "your task"        # Start building
   mekong plan "your feature"     # Plan before coding
   ```

3. **Join Community**
   - Discord: https://claudekit.cc/discord
   - GitHub Issues: https://github.com/mekong-cli/mekong-cli/issues

4. **Deploy Your Own Project**
   ```bash
   # Scaffold new project
   bash mekong/infra/scaffold.sh myproject startup

   # Deploy to Cloudflare
   cd myproject
   git push  # Triggers Cloudflare Pages deploy
   ```

---

## License

**Mekong CLI** © 2026 Binh Phap Venture Studio — [MIT License](LICENSE)
