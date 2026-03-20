# 🏯 Mekong CLI

**AI-operated business platform. Open source. Universal LLM.**

Describe your goal → AI plans → executes → verifies → delivers results.
319 commands • 463 skills • 410 contracts • 5 business layers.

## Quick Start

### With API key (OpenRouter / Qwen / DeepSeek / any provider):

```bash
pip install mekong-cli
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
mekong cook "Create a REST API with auth"
```

### With local LLM (free):

```bash
pip install mekong-cli
# Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
mekong cook "Create a Python calculator"
```

### For founders (non-tech):

```bash
mekong annual "2026 business plan"
mekong founder:raise "Pre-seed for AI platform"   # 8 agents parallel
mekong founder:validate-sprint "Is this investable?"  # PMF verdict in 25 min
```

## 5 Business Layers

```
👑 Founder    /annual /okr /fundraise /swot         — Strategy & fundraising
💼 Business   /sales /marketing /finance /hr         — Revenue & operations
🎯 Product    /plan /sprint /roadmap /brainstorm     — Product management
⚙️ Engineering /cook /code /test /deploy /review      — Build & ship
🔧 Ops        /audit /health /security /status       — Monitor & maintain
```

## 101 Super Commands

One command triggers parallel AI agents via DAG recipes:

```bash
$ mekong founder:raise "Series A for AI platform"
  ⚡ Group 1 (parallel): /unit-economics + /tam + /moat-audit
  ⚡ Group 2 (parallel): /financial-model + /data-room
  ⚡ Group 3 (sequential): /cap-table → /pitch → /vc-map
  ✅ Output: reports/raise-ready-kit/ (investor-ready)
```

32 roles from CEO to intern. 85 DAG workflow recipes. [See full list →](docs/COMMANDS.md)

## Architecture

```
Plan → Execute → Verify (PEV Engine)
       ↓ failed?             ↓ self-heal              ↓ auto-retry
     Debug → Fix → Retest   Learn → Adapt            Escalate → Human
```

- **Universal LLM**: 3 env vars, any OpenAI-compatible provider
- **DAG Scheduler**: Parallel execution with dependency graphs
- **Self-healing**: Failed steps auto-diagnosed and corrected
- **100% Cloudflare**: Pages (frontend) + Workers (backend) + D1 + KV + R2

## Deploy

All infrastructure runs on Cloudflare:

| Layer | Platform | Cost |
|-------|----------|------|
| Frontend | Cloudflare Pages | $0 |
| Edge API | Cloudflare Workers | $0 |
| Database | Cloudflare D1 | $0 |
| Storage | Cloudflare R2 | $0 |
| Cache | Cloudflare KV | $0 |

## Project Structure

```
├── src/                   # Python CLI core (PEV engine)
├── apps/openclaw-worker/  # Tôm Hùm autonomous daemon
├── frontend/landing/      # Next.js 16 landing (agencyos.network)
├── .agencyos/commands/    # 319 command definitions
├── factory/contracts/     # 410 JSON machine contracts
├── recipes/               # 85 DAG workflow recipes
├── mekong/                # Namespace (skills, adapters, config)
└── reports/               # Self-dogfood analysis (242 reports)
```

## Verify Installation

After installation, verify everything works:

```bash
# 1. Check version
mekong version
# Expected: Mekong CLI v5.0.0

# 2. Run self-test
make setup && make self-test
# Expected: Score 100/100

# 3. Test a command
mekong status
# Expected: Current LLM config
```

If any step fails, see [Troubleshooting](#troubleshooting) below.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md), [FORK.md](FORK.md) and [QUICKSTART.md](QUICKSTART.md).

## Troubleshooting

### Installation issues

```bash
# Reinstall
pip uninstall mekong-cli
pip install -e .

# Verify
pip list | grep mekong
```

### LLM connection errors

```bash
# Check env vars
echo $LLM_BASE_URL
echo $LLM_API_KEY

# Test with different provider
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=qwen2.5-coder
```

### Command not working

```bash
# Reload shell
source ~/mekong-cli/scripts/shell-init.sh

# Or restart terminal
```

### Test failures

```bash
# Reinstall dev dependencies
pip install -e ".[dev]"

# Run tests verbose
python3 -m pytest tests/ -v --tb=short

# Clear cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## License

**Mekong CLI** © 2026 Binh Phap Venture Studio — [MIT License](LICENSE)
