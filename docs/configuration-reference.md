# Configuration Reference

This document provides a complete reference for all Mekong CLI configuration options, environment variables, and settings files.

---

## Table of Contents

- [Environment Variables](#environment-variables)
  - [LLM Provider Configuration](#llm-provider-configuration)
  - [Authentication & Security](#authentication--security)
  - [Billing & Payments](#billing--payments)
  - [Observability](#observability)
  - [Vietnam Hub (VN HUB)](#vietnam-hub-vn-hub)
  - [CashClaw Trading](#cashclaw-trading)
  - [Social Auto-Poster](#social-auto-poster)
  - [Miscellaneous](#miscellaneous)
- [Claude Settings](#claude-settings)
- [Mekong Configuration Files](#mekong-configuration-files)
- [Plugin Configuration](#plugin-configuration)

---

## Environment Variables

### LLM Provider Configuration

Choose ONE provider configuration:

#### OpenRouter (Recommended - 200+ models, $5 free credit)

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_BASE_URL` | API endpoint | `https://openrouter.ai/api/v1` |
| `LLM_API_KEY` | API key | `sk-or-v1-...` |
| `LLM_MODEL` | Model name | `anthropic/claude-sonnet-4` |

```bash
export LLM_BASE_URL=https://openrouter.ai/api/v1
export LLM_API_KEY=sk-or-v1-yourkey
export LLM_MODEL=anthropic/claude-sonnet-4
```

#### Provider-Specific API Keys (auto-detected)

| Variable | Provider | Models |
|----------|----------|--------|
| `OPENROUTER_API_KEY` | OpenRouter | 200+ models |
| `ANTHROPIC_API_KEY` | Anthropic | Claude family |
| `OPENAI_API_KEY` | OpenAI | GPT-4, GPT-4o |
| `DASHSCOPE_API_KEY` | Alibaba DashScope | Qwen family |
| `DEEPSEEK_API_KEY` | DeepSeek | DeepSeek models |
| `GOOGLE_API_KEY` | Google | Gemini family |
| `OLLAMA_HOST` | Ollama (local) | Local models |

#### Local LLM (Free)

```bash
# Ollama
export OLLAMA_HOST=http://localhost:11434
export LLM_MODEL=qwen2.5-coder

# or Rapid-MLX (Apple Silicon, 4.2x faster)
export LOCAL_LLM_URL=http://localhost:8001/v1
export LOCAL_LLM_MODEL=qwen3.6-35b
```

**Fallback Chain**: OpenRouter → DashScope → DeepSeek → Anthropic → OpenAI → Google → Ollama → Offline

---

### Authentication & Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AUTH_ENVIRONMENT` | No | `dev` | Auth environment: `dev`, `staging`, `production` |
| `JWT_SECRET` | Staging/Prod | (auto-generated) | JWT signing secret (min 32 bytes) |
| `JWT_ACCESS_EXPIRY_MINUTES` | No | `30` | Access token expiry |
| `JWT_REFRESH_EXPIRY_DAYS` | No | `7` | Refresh token expiry |
| `MEKONG_ADMIN_TOKEN` | Optional | - | Admin token for privileged operations |
| `MEKONG_API_TOKEN` | Gateway auth | - | API gateway authentication |

**Generate JWT_SECRET for production:**
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
# or
openssl rand -hex 32
```

---

### Billing & Payments

#### Polar.sh (Primary billing)

| Variable | Required | Description |
|----------|----------|-------------|
| `POLAR_API_KEY` | Yes (backend) | Polar API key from dashboard |
| `POLAR_WEBHOOK_SECRET` | Yes (webhooks) | Webhook signing secret |
| `POLAR_STARTER_PRODUCT_ID` | Yes | Product ID for Starter tier |
| `POLAR_GROWTH_PRODUCT_ID` | Yes | Product ID for Growth tier |
| `POLAR_PRO_PRODUCT_ID` | Yes | Product ID for Pro tier |
| `POLAR_SUCCESS_URL` | No | Checkout success redirect |
| `POLAR_CANCEL_URL` | No | Checkout cancel redirect |

#### Stripe (Alternative)

| Variable | Required | Description |
|----------|----------|-------------|
| `STRIPE_SECRET_KEY` | Yes | Stripe secret API key |
| `STRIPE_WEBHOOK_SECRET` | Yes | Webhook signing secret |
| `STRIPE_PRICE_STARTER` | Yes | Price ID for Starter |
| `STRIPE_PRICE_GROWTH` | Yes | Price ID for Growth |
| `STRIPE_PRICE_PRO` | Yes | Price ID for Pro |
| `STRIPE_DOMAIN` | No | Checkout domain |

#### App Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_BASE_URL` | `https://mekongmind.com` | Base URL for redirects |

---

### Observability

| Variable | Description |
|----------|-------------|
| `LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `LOG_FORMAT` | `json` (production) or `console` (dev) |
| `SENTRY_DSN` | Sentry DSN for error tracking |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OpenTelemetry endpoint |
| `MEKONG_NO_USAGE_TRACKING` | Set to `true` to disable tracking |

---

### Vietnam Hub (VN HUB)

For Vietnamese market operations (1 Triệu Doanh Nghiệp 1 Người):

| Variable | Description | Default |
|----------|-------------|---------|
| `VN_LLM_BASE_URL` | Vietnamese LLM endpoint | `http://localhost:8001/v1` |
| `VN_LLM_MODEL` | Vietnamese specialist model | `qwen3.6-35b` |
| `VN_REASONING_MODEL` | General reasoning model | `qwen3.5-9b` |
| `VN_BUSINESS_TYPE` | Business profile | `shop_online` |
| `VN_CITY` | City code | `hcm` |
| `VN_BANK` | Preferred bank | `vcb` |
| `VN_TAX_CODE` | Tax code (optional) | - |

**Setup:**
```bash
brew install raullenchai/rapid-mlx/rapid-mlx
rapid-mlx serve qwen3.6-35b --port 8001
```

---

### CashClaw Trading

For Polymarket prediction trading:

| Variable | Required | Description |
|----------|----------|-------------|
| `POLYMARKET_PRIVATE_KEY` | Yes | Ethereum private key |
| `POLYMARKET_API_KEY` | Yes | Polymarket API key |
| `PAPER_TRADING` | No | Default `true` - always start with paper trading |
| `CAPITAL_USDC` | No | Trading capital in USDC |
| `OLLAMA_HOST` | Optional | Local LLM for predictions |
| `OLLAMA_MODEL` | Optional | Model for predictions |
| `DATABASE_PATH` | No | Trading database path |
| `TELEGRAM_BOT_TOKEN` | Optional | Telegram bot for alerts |
| `TELEGRAM_CHAT_ID` | Optional | Telegram chat for alerts |

---

### Social Auto-Poster

| Variable | Description |
|----------|-------------|
| `DISCORD_WEBHOOK_URL` | Discord webhook for auto-posting |
| `DEVTO_API_KEY` | dev.to API key |
| `RAAS_URL` | RaaS landing URL (default: `https://agencyos.network`) |

---

### Miscellaneous

| Variable | Description |
|----------|-------------|
| `MEKONG_CONFIG_DIR` | Config directory (default: `~/.mekong`) |
| `MEKONG_DEV_MODE` | Set to `true` for development mode |
| `MEKONG_FEATURE_PLUGIN_SYSTEM_ENABLED` | Enable plugin system |
| `MEKONG_PLUGIN_HOT_RELOAD` | Enable hot reload for plugins |
| `MEKONG_PLUGIN_CACHE_ENABLED` | Enable plugin caching |
| `LITELLM_MASTER_KEY` | LiteLLM proxy master key |
| `LITELLM_URL` | LiteLLM proxy URL |
| `LITELLM_DB_URL` | LiteLLM database URL |
| `BAILIAN_API_KEY` | Alibaba Cloud AI API key |
| `BAILIAN_BASE_URL` | Alibaba base URL |

---

## Claude Settings

Location: `.claude/settings.json`

This file configures Claude Code CLI behavior. See the [Claude Code documentation](https://docs.claude.com/claude-code/settings) for full schema.

### Key Settings

```json
{
  "outputStyle": "coding-level-3-senior",
  "permissions": {
    "allow": [...],
    "deny": [...],
    "ask": [...]
  },
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...]
  }
}
```

#### Output Styles

| Style | Description |
|-------|-------------|
| `coding-level-1-eli5` | Simple explanations |
| `coding-level-2-regular` | Standard detail |
| `coding-level-3-senior` | Expert-level (default) |
| `coding-level-4-god` | Maximum detail |

#### Permissions

Permissions control which tools Claude can use:

| Tool Type | Format |
|-----------|--------|
| Bash | `Bash(command:*)` or `Bash(git status:*)` |
| Read | `Read(path)` |
| Write | `Write(path)` |
| Edit | `Edit(path)` |

**Examples:**
```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",
      "Read(./src/**)"
    ],
    "deny": [
      "Read(./.env)",
      "Edit(./mekong/daemon/**)"
    ],
    "ask": [
      "Bash(git push:*)"
    ]
  }
}
```

#### Hooks

Hooks run code at specific points:

| Hook | When |
|------|------|
| `SessionStart` | Session begins |
| `UserPromptSubmit` | User submits a prompt |
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool execution |
| `SubagentStart` | Subagent spawns |
| `SubagentStop` | Subagent terminates |
| `SessionEnd` | Session ends |

---

## Mekong Configuration Files

### `~/.mekong/settings.json`

Main Mekong CLI configuration.

```json
{
  "plugin_system": {
    "enabled": true,
    "compatibility_mode": false,
    "hot_reload": true
  },
  "feature_flags": {
    "plugin_build": true,
    "plugin_deploy": true
  },
  "billing": {
    "default_plan": "starter",
    "credit_alert_threshold": 50
  },
  "database": {
    "path": "~/.mekong/data.db"
  }
}
```

### `~/.mekong/company.json`

Company manifest created by `mekong company/init`:

```json
{
  "company_name": "YourCo AI",
  "mission": "Build tools for solo founders",
  "founder": {
    "name": "Your Name",
    "email": "you@example.com",
    "timezone": "Asia/Ho_Chi_Minh"
  },
  "constitution": {
    "principles": [...],
    "budget_limits": {
      "monthly_spend_cap": 1000,
      "daily_credit_alert": 50
    }
  },
  "economic_particle": {
    "type": "micro_enterprise",
    "allocation_rules": {
      "reserve": 0.30,
      "tax": 0.25,
      "reinvest": 0.30,
      "draw": 0.15
    }
  }
}
```

### `~/.mekong/plugins/installed/<plugin-id>/config.json`

Plugin-specific configuration (auto-generated).

---

## Plugin Configuration

Plugins declare configuration in their manifest:

```json
{
  "config_schema": {
    "type": "object",
    "properties": {
      "api_key": {
        "type": "string",
        "secret": true
      },
      "base_url": {
        "type": "string",
        "default": "https://api.example.com"
      },
      "timeout": {
        "type": "number",
        "default": 30
      }
    },
    "required": ["api_key"]
  }
}
```

### Environment Variable Mapping

Plugins can read config via environment variables:

```
MEKONG_PLUGIN_<PLUGIN_ID>_<KEY>=value
```

Example for plugin `zalo-oa`:
```
MEKONG_PLUGIN_ZALO_OA_ACCESS_TOKEN=your-token
MEKONG_PLUGIN_ZALO_OA_APP_ID=your-app-id
```

Or via Mekong config store:
```bash
mekong config set zalo-oa access_token "your-token"
```

---

## Configuration Hierarchy

1. **Environment Variables** - Highest priority
2. **`~/.mekong/plugins/<plugin>/config.json`** - Plugin config
3. **`~/.mekong/settings.json`** - Global settings
4. **Manifest defaults** - Fallback values

---

## Validation

Validate configuration files:

```bash
# Validate Claude settings
cat .claude/settings.json | jq empty

# Validate plugin manifest
python3 -m scripts.plugin_validator validate plugin.json

# Check Mekong config
mekong config validate
```

---

## See Also

- [Environment Setup Guide](./greenfield-quickstart.md#phase-1-install-mekong-cli)
- [Plugin Developer Guide](./plugin-developer-guide.md#secret-management)
- [Plugin Migration Guide](./plugin-migration-guide.md#handling-configuration-migration)
- [Troubleshooting Guide](./troubleshooting.md) (coming soon)
