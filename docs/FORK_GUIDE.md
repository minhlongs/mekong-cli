# OpenClaw Fork Guide

How to fork mekong-cli and run your own autonomous CTO agent.

## Prerequisites

- Python 3.11+
- Node.js 18+ and pnpm
- Supabase account (or use SQLite for local dev)
- NOWPayments account (for billing)
- Anthropic API key or Antigravity proxy

## Quick Start

```bash
git clone https://github.com/your-org/mekong-cli
cd mekong-cli
make setup
cp .env.example .env
# Fill in your API keys in .env
make generate-contracts
make self-test
```

## Customizing Your Fork

### 1. Update Identity

Edit `CLAUDE.md` — change the identity section (Section 1) to your company/product name.

### 2. Add Your Commands

Add `.md` files to `.claude/commands/`. Each file needs YAML frontmatter:

```markdown
---
description: Brief description of what this command does
allowed-tools: Read, Write, Bash
---

# /your-command — Title

Command implementation...
```

### 3. Update Layers

Edit `factory/layers.yaml` — add your command name to the appropriate layer's `commands` list.

### 4. Regenerate Contracts

```bash
make regenerate
```

This runs `generate_contracts.py` and `self_test.py`. All contracts in
`factory/contracts/commands/` are rebuilt from your command files.

### 5. Configure Billing

Set these environment variables:

```
NOWPAYMENTS_ACCESS_TOKEN=your_polar_token
NOWPAYMENTS_WEBHOOK_SECRET=your_webhook_secret
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

Edit `factory/contracts/pricing.json` to set your own service cards and credit prices.

### 6. Configure Approval Rules

Edit `factory/contracts/approval_rules.json` to control which layer transitions
and commands require Telegram approval before execution.

### 7. Start the Daemon

```bash
make start-daemon
```

The Tôm Hùm daemon (`apps/openclaw-worker/`) reads contracts from
`factory/contracts/` and dispatches missions automatically.

## Directory Structure

```
factory/
├── contracts/
│   ├── commands.schema.json   # Contract schema
│   ├── missions.schema.json   # Mission dispatch schema
│   ├── pricing.json           # RaaS service cards
│   ├── approval_rules.json    # Telegram approval gates
│   ├── skills.registry.json   # Auto-generated skills index
│   ├── agents.registry.json   # Auto-generated agents index
│   └── commands/              # Per-command contracts (generated)
├── generate_contracts.py      # Contract generator
├── validate_contracts.py      # Contract validator
├── self_test.py               # Health check (score 0-100)
└── layers.yaml                # 5-layer pyramid config
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `make generate-contracts` | Generate contracts from command files |
| `make validate-contracts` | Validate all contracts against schemas |
| `make self-test` | Run full health check, output score |
| `make regenerate` | generate + validate + self-test |
| `make start-daemon` | Start Tôm Hùm autonomous daemon |
| `make stop-daemon` | Stop the daemon |
| `make daemon-status` | Check daemon health |
| `make start-gateway` | Start FastAPI gateway on :8000 |

## Health Score

Run `make self-test` to get a health score (0-100):

- **90-100**: Production ready
- **80-89**: Minor issues
- **60-79**: Fix before deploying
- **<60**: Critical gaps

Report is written to `factory/self-test-report.json`.

## Adding RaaS Services

To offer your commands as paid services, add entries to `factory/contracts/pricing.json`:

```json
{
  "name_vi": "Vietnamese name",
  "name_en": "English name",
  "credits": 3,
  "command": "your-command-id",
  "layer": "engineering",
  "description_en": "What this service does"
}
```

Credits are billed via NOWPayments webhooks → `src/raas/credits.py`.
1 MCU (Mekong Credit Unit) = 1 credit = configurable USD price.

## License

See `LICENSE`. The `src/core/` PEV engine is open source.
The `src/raas/` commercial layer requires a `RAAS_LICENSE_KEY`.
