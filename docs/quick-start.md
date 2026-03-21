# Mekong CLI — Quick Start Guide

**Get up and running in 15 minutes.**

> AI-operated business platform. 319 commands • 5 layers • Universal LLM

---

## 1. Installation

**Prerequisites:** Python 3.9+, Node.js 18+

```bash
# Clone the repository
git clone https://github.com/longtho638-jpg/mekong-cli.git
cd mekong-cli

# Install dependencies
pip install -e .
npm install -g @anthropic/mcp-server-filesystem

# Verify installation
mekong --version
mekong health
```

---

## 2. Configure LLM

Choose your provider (3 env vars):

### Option A: OpenRouter (Recommended)
```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-your-key
export LLM_MODEL=anthropic/claude-sonnet-4
```

### Option B: Anthropic (Native)
```bash
export LLM_BASE_URL=https://api.anthropic.com/v1
export LLM_API_KEY=sk-ant-your-key
export LLM_MODEL=claude-opus-4-6
```

### Option C: Local (Free)
```bash
# Install Ollama: https://ollama.ai
ollama pull qwen2.5-coder
export LLM_BASE_URL=http://localhost:11434/v1
export LLM_MODEL=qwen2.5-coder
```

**Verify:**
```bash
mekong status
# Output: LLM configured • Ready to execute
```

---

## 3. First Command

### Simple Example
```bash
mekong cook "Create a Python function to reverse an array"
# Output: /src/reverse_array.py (ready to use)
```

### Multi-step Example
```bash
# Plan → Execute → Verify (PEV engine)
mekong cook "Build a REST API with authentication"
# Step 1: Planner decomposes into tasks
# Step 2: Executor writes code + tests
# Step 3: Verifier runs tests + security check
# Output: Full API implementation ready
```

---

## 4. Explore Commands by Layer

### Founder (Strategy)
```bash
mekong annual "2026 business plan"
mekong okr "Q2 2026 objectives"
mekong fundraise "Series A funding"
```

### Business (Revenue)
```bash
mekong quote "Acme Corp" --budget 50000
mekong marketing "Q2 content calendar"
mekong finance "Monthly P&L analysis"
```

### Product (Planning)
```bash
mekong plan "AI code assistant"
mekong sprint "2-week sprint planning"
mekong roadmap "12-month roadmap"
```

### Engineering (Build)
```bash
mekong cook "Build REST API"
mekong fix "Debug memory leak"
mekong test "Write unit tests"
mekong deploy
```

### Ops (Monitor)
```bash
mekong audit "Security audit"
mekong health "System health check"
mekong status "Service status"
```

---

## 5. Key Aliases

```bash
mekong                    # Interactive (default: Claude Opus)
mekong-sonnet            # Force Claude Sonnet 4 (faster, cheaper)
mekong-qwen              # Force DashScope Qwen 3.5 (cheapest)
mekong-cto               # Daemon mode (autonomous)
mekong help              # List all commands
mekong status            # Check LLM config
```

---

## 6. Shell Integration

Add to `.zshrc` or `.bashrc`:

```bash
source ~/mekong-cli/scripts/shell-init.sh
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bashrc
```

---

## 7. Pricing & Billing

**Free tier:** Start now, upgrade later.

| Tier | Price | Credits | Good for |
|------|-------|---------|----------|
| Free | $0 | 10 MCU | Learning |
| Starter | $79 | 150 MCU | Solo founders |
| Pro | $249 | 750 MCU | Small teams |
| Enterprise | $599 | Unlimited* | Agencies |

*Fair use: 2,000 MCU/month average

See `/docs/pricing.md` for full details.

---

## 8. Common Workflows

### Build a Feature End-to-End
```bash
mekong cook "User authentication with OAuth2"
# Generates: src/auth/ with tests + security checks
```

### Debug Production Issue
```bash
mekong fix "High memory usage in API"
# Generates: root cause analysis + fix
```

### Create Marketing Content
```bash
mekong marketing "Blog post on AI trends"
# Generates: 2,000-word blog post + social clips
```

### Analyze Sales Pipeline
```bash
mekong sales "Q1 pipeline analysis"
# Generates: Win/loss analysis + recommendations
```

---

## 9. Project Structure

```
mekong-cli/
├── docs/                    # Documentation
├── packages/
│   └── mekong-cli-core/    # Main package
│       ├── src/
│       │   ├── core/       # PEV engine
│       │   ├── api/        # API routes
│       │   ├── agents/     # AI roles
│       │   └── tests/
│       └── pyproject.toml
├── .claude/
│   ├── commands/           # 319 command defs
│   ├── skills/             # 542 skills
│   └── agents/             # 32 roles
├── factory/
│   ├── contracts/          # 410 machine contracts
│   └── recipes/            # 85 workflow recipes
├── mekong/
│   ├── infra/              # Cloudflare deploy
│   ├── adapters/           # LLM routers
│   └── daemon/             # Autonomous CTO
└── apps/                   # 8+ applications
```

---

## 10. Next Steps

1. **Choose LLM provider** (OpenRouter, Anthropic, or local Ollama)
2. **Run first command** (`mekong cook "..."`)
3. **Check dashboard** (`mekong account:usage`)
4. **Explore commands** (`mekong help`)
5. **Read full docs** (links below)

---

## Docs & Resources

- **API Reference:** `/docs/api-reference.md`
- **Command Catalog:** `/docs/command-catalog.md`
- **Codebase Summary:** `/docs/codebase-summary.md`
- **Pricing & Billing:** `/docs/pricing.md`
- **Architecture:** `/docs/ARCHITECTURE.md`
- **Contributing:** `/CONTRIBUTING.md`

---

## Troubleshooting

**Issue:** `mekong: command not found`
```bash
# Reload shell
source ~/.zshrc
# Or reinstall
pip install -e .
```

**Issue:** LLM connection error
```bash
# Check env vars
echo $LLM_BASE_URL
echo $LLM_API_KEY

# Test connection
mekong status
```

**Issue:** No MCU left
```bash
# Check balance
mekong account:usage

# Upgrade tier
# Visit: agencyos.network/upgrade
```

---

## Support

- **Email:** support@agencyos.network
- **Slack:** Join community (Pro/Enterprise)
- **Issues:** GitHub Issues
- **Status:** status.agencyos.network

Happy building! 🚀
