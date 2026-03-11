# Security Audit — Mekong CLI

**Date:** 2026-03-11
**Scope:** Shell injection, secrets, auth patterns, CI security jobs

---

## 1. Shell Execution Security

### Double-Layer Sanitization (STRONG)

Every shell command goes through two gates before `subprocess.run()`:

**Gate 1 — Fast pattern check** (`executor.py:40-54`):
```python
DANGEROUS_PATTERNS = [
    "rm -rf /", "mkfs", "dd if=", ": (){",
    "chmod -R 777 /", "curl.*|.*sh", "wget.*|.*sh",
    "eval ", "exec(", "> /dev/sd", "shutdown", "reboot", "init 0",
]
```
Regex scan on lowercase command before any execution.

**Gate 2 — CommandSanitizer** (`src/security/command_sanitizer.py`):
```python
sanitizer = CommandSanitizer(strict_mode=True)
sanitization_result = sanitizer.sanitize(command)
if not sanitization_result.is_safe:
    return ExecutionResult(exit_code=1, stderr="SECURITY_BLOCKED: ...")
```

Applied in three places: executor shell steps, verifier custom checks, rollback handler.
`shlex.split()` used everywhere — never `shell=True`.

**subprocess timeout:** 300s for steps, 30s for custom verification checks.

---

## 2. Hardcoded Secrets Scan

```bash
grep -rE "(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*['\"][a-zA-Z0-9]{16,}['\"]" src/ \
  --include="*.py" | grep -v "os.getenv|os.environ|test"
```

Result: **No hardcoded secrets found** in `src/`.

All sensitive values read from environment:
```python
os.getenv("LLM_API_KEY")
os.getenv("OPENROUTER_API_KEY")
os.getenv("TELEGRAM_BOT_TOKEN")
os.getenv("MEKONG_API_KEY")
```

Cloudflare secrets stored via `wrangler secret put` — not in `wrangler.toml` or code.

---

## 3. Authentication Architecture

### CLI → Gateway Auth

**mk_ API key format:** `mk_live_<32-char-hex>` or `mk_test_<32-char-hex>`

Gateway `edge-auth-handler.js` validates:
- Key prefix (`mk_live_` or `mk_test_`)
- Length/format
- KV lookup for active key

**JWT (dashboard):** Supabase JWT verified at edge, `userId` extracted for per-tenant rate limiting.

### Python Auth (`src/core/auth_jwt.py`, `src/core/auth_session.py`)

JWT validation for backend API calls. Key patterns:
- `auth_tenant.py` — per-tenant isolation of data/quotas
- `auth_types.py` — typed auth context passed through request lifecycle

### RaaS Auth (`src/core/raas_auth.py`, 903 lines)

Handles license JWT + session management for RaaS subscriptions. Signs/verifies JWTs using project-scoped keys.

---

## 4. Rate Limiting

**KV-based sliding window** per API key (gateway):
```javascript
import { checkRateLimit, buildRateLimitHeaders } from './src/kv-rate-limiter-per-api-key.js';
```

Tier-based limits:
```python
# src/lib/tier_config.py
TIER_LIMITS = {
    "free":       {"requests_per_hour": 10,  "mcu_per_month": 0},
    "trial":      {"requests_per_hour": 50,  "mcu_per_month": 50},
    "starter":    {"requests_per_hour": 200, "mcu_per_month": 200},
    "pro":        {"requests_per_hour": 1000,"mcu_per_month": 1000},
    "enterprise": {"requests_per_hour": -1,  "mcu_per_month": -1},  # unlimited
}
```

**`src/core/rate_limit_client.py`** — Python-side rate limit enforcement for internal calls.

---

## 5. MCU Billing Security

**HTTP 402 enforcement:** Gateway returns 402 before proxying to backend if MCU balance = 0. Zero-trust: no execution without credit.

**Audit log** (`src/core/raas_audit_logger.py`): every MCU deduction logged with timestamp, user, command, amount. Tamper-evident append-only log.

**`src/core/mcu_gate.py`** — pre-execution MCU check. Checked in orchestrator before plan execution.

---

## 6. CI Security Pipeline (security-hardening.yml)

5-job security workflow on every push to main/PR:

| Job | Tool | Status |
|-----|------|--------|
| Secret scanning | truffleHog (filesystem) | continue-on-error |
| .env file check | find src/ -name ".env*" | blocks if found |
| Hardcoded secret grep | regex pattern | blocks if found |
| Command injection scan | CommandSanitizer self-test | blocking |
| Dependency audit | pip-audit + safety | continue-on-error |
| Security headers check | grep middleware files | continue-on-error |
| Attestation report | SHA256 signed JSON | uploaded as artifact |
| Security gate | Final pass/fail | blocks merge if FAILED |

Security attestation artifact stored for 90 days per run.

---

## 7. Suspension System

```javascript
import { checkSuspensionStatus, syncSuspensionToKV } from './src/kv-suspension-checker.js';
```

Suspended accounts blocked at edge before any compute. Suspension flag synced to KV from billing system. Response header: `X-Account-Status: suspended`.

---

## 8. Input Validation

**LLM prompts:** Truncated at source before sending (`response.content[:2000]`). No prompt injection mitigation beyond length limits — acceptable for CLI tool where user controls input.

**API step bodies:** Passed directly to `requests.request()` — no schema validation on user-provided `body` dict. Risk: SSRF if gateway URL is user-controlled.

**Recipe files:** Parsed from Markdown — no code execution in parser, steps sanitized at executor layer.

---

## 9. Identified Vulnerabilities

| ID | Issue | Severity | File |
|----|-------|----------|------|
| SEC-01 | `StepExecutor.console` bug could mask security error logs during self-healing | MEDIUM | orchestrator.py:136 |
| SEC-02 | API step `url` param from recipe not validated — SSRF possible if recipe untrusted | MEDIUM | executor.py:136 |
| SEC-03 | truffleHog scan is `continue-on-error` — won't block PRs | MEDIUM | security-hardening.yml:32 |
| SEC-04 | CORS origins hardcoded — adding new origin requires code change + deploy | LOW | index.js:62 |
| SEC-05 | No HMAC verification on Telegram webhook payloads | LOW | gateway routes |
| SEC-06 | `safety check --ignore 70612` — CVE permanently suppressed, needs review | LOW | ci.yml:115 |

---

## 10. Security Strengths

- Double-layer shell sanitization with pattern + sanitizer (strong)
- No hardcoded secrets found anywhere in `src/`
- JWT + mk_ key dual auth well-structured
- Per-tenant rate limiting at edge (KV)
- Audit logs for every MCU deduction
- Security attestation artifact generated on every main push
- Suspension enforcement at edge before compute

---

## 11. Remediation Priority

1. **SEC-01** — Fix `StepExecutor.console` (1 line fix, no risk)
2. **SEC-02** — Add URL allowlist or domain validation for API steps
3. **SEC-03** — Make truffleHog blocking (`exit 1` on verified findings)
4. **SEC-05** — Add `X-Telegram-Bot-Api-Secret-Token` header validation
5. **SEC-06** — Review CVE 70612 — if still relevant, update or document suppression reason
