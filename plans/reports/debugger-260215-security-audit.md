# Security Audit Report - Mekong CLI Monorepo
Date: 2026-02-15
Auditor: Debugger Agent (a1e7ebc)

## Executive Summary
This report details the findings of a deep security audit performed on the `mekong-cli` monorepo. The audit focused on identifying hardcoded secrets, misconfigured gitignores, and exposed internal infrastructure details that could pose a risk if the repository is made public.

**CRITICAL WARNING:** Several active API keys and tokens were found hardcoded in tracked files. These must be rotated immediately before any public release.

## Severity Level Definitions
- **CRITICAL:** Active credentials/secrets that provide access to paid services or sensitive data.
- **HIGH:** Infrastructure tokens, sensitive internal URLs, or backup environment files.
- **MEDIUM:** Internal IP addresses, developer-specific paths, or legacy config files.
- **LOW:** Non-sensitive internal naming or documentation of private strategies.

---

## 🔴 Findings: Hardcoded Credentials (CRITICAL)

### 1. Gemini / Google AI API Keys
- **Key:** `AIzaSyBeFTNIvKtav1DoZKFACQVyrgNusRODfcg`
  - `src/core/autonomous.py:65`
  - `scripts/verify_vertex.py:19`
  - `scripts/gemini_chat.py:16`
  - `apps/antigravity-gateway/wrangler.toml:11`
- **Key:** `AIzaSyCzyAYh_D_wGJkdFqRLtVkuCZeTvsVMuh0`
  - `.env.bak:15`
  - `plans/reports/meta-analysis-260129-2110-framework-self-generation.md:211`
  - `apps/antigravity-gateway/wrangler.toml:11`
- **Key:** `AIzaSyC79sMC-4fLacJDpDpGmFZKxvsvwZMC2IQ`
  - `scripts/start-telegram-bot.sh:16`

### 2. Anthropic / Antigravity Proxy Keys
- **Key:** `sk-6219c93290f14b32b047342ca8b0bea9`
  - `scripts/tom-hum-persistent-dispatch.exp:62`
  - `scripts/qwen_bridge.py:22`
  - `apps/antigravity-gateway/wrangler.toml:10`
  - `apps/antigravity-gateway/cook.js:25`
- **Key:** `sk-c397f4b713e6400e96c18e8c07ffeaef`
  - `scripts/qwen_bridge.py:23`

### 3. Telegram Bot Tokens
- **Token:** `8405197398:AAHuuykECSxEGZaBZVhtvwyIWM84LtGLO5I`
  - `scripts/start-telegram-bot.sh:14`
  - `apps/openclaw-worker/openclaw-service.sh:10`
  - `apps/openclaw-worker/tunnel-manager.sh:6`
  - `apps/openclaw-worker/telegram-notify.sh:5`
  - `apps/openclaw-worker/scripts/tom-hum-deep-loop.sh:19`

### 4. Cloudflare API Tokens
- **Token:** `ZGmz0rgZp4l8q8YYp8Qo9nDpu-rJbbg0QnxCkWVu`
  - `apps/raas-gateway/update_secret.sh:2`
  - `apps/openclaw-worker/openclaw-service.sh:9`
  - `apps/openclaw-worker/tunnel-manager.sh:5`
  - `apps/openclaw-worker/scripts/tom-hum-deep-loop.sh:18`

---

## 🟠 Findings: Exposed Configuration & Environment (HIGH)

### 1. Tracked Environment Backups
- `.env.bak` is tracked in git and contains a `GEMINI_API_KEY`.

### 2. Hardcoded Infrastructure Details
- `scripts/tom-hum-launchd-install.sh`: Creates `$HOME/.mekong/api-key` and manages it via shell commands.
- `apps/openclaw-worker/config.js`: Contains absolute paths like `/Users/macbookprom1/mekong-cli`. While not a "secret", it exposes the host machine's directory structure.

---

## 🟡 Findings: Internal Information (MEDIUM/LOW)

### 1. Internal IP Addresses
- Multiple files in `.opencode/skills/` and `.claude/skills/` contain references to local IPs (`10.0.0.1`, `192.168.1.1`, `192.168.2.75`). Most appear to be examples or local swarm configs.

### 2. Strategy & Revenue Docs
- Several documents under `docs/` and `plans/` detail internal business strategies, revenue models, and competitor analysis. While some are ignored in `.gitignore` (e.g., `dna/pricing/`), others like `plans/revenue-strategy-2026.md` are currently tracked.

---

## Recommended Actions

1. **Rotate All Secrets:** Every key listed in the CRITICAL section must be invalidated and regenerated.
2. **Move to Environment Variables:** Refactor all scripts (`.sh`, `.py`, `.js`, `.exp`) to use environment variables instead of hardcoded strings.
3. **Clean Git History:** Use a tool like `bfg-repo-cleaner` or `git filter-repo` to permanently remove these secrets and the `.env.bak` file from the git history before making the repo public.
4. **Strict .gitignore Enforcement:** Ensure `*.bak`, `*.log`, and all `.env` files are never committed.
5. **Path Normalization:** Replace hardcoded absolute paths in `config.js` with relative paths based on project root.

## Unresolved Questions
- Are the hardcoded IPs in `tests/` and `skills/` purely for documentation, or are they used in active local swarm deployments?
- Are the strategies in `plans/` intended to be part of the "Open Core" or should they be moved to `plans/internal/`?

