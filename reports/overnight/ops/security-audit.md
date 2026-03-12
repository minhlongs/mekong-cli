# Security Audit — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** security, ops-security-audit, audit, benchmark

---

## Executive Summary

| Area | Status | Score |
|------|--------|-------|
| Secrets in code | PASS | No hardcoded secrets in `src/` |
| .gitignore coverage | PASS | `.env`, keys, venv, node_modules covered |
| Env var handling | PASS | All via `os.getenv()` + dotenv |
| Command injection | PASS | Dedicated `CommandSanitizer` class |
| Security CI pipeline | PASS | Dedicated `security-hardening.yml` workflow |
| Bandit SAST | PASS | Runs on every push (continue-on-error) |
| Dependency audit | PARTIAL | `safety check` runs but ignores vuln 70612 |
| Auth middleware | EXISTS | `src/middleware/auth_middleware.py` |
| Rate limiting | EXISTS | `src/telemetry/rate_limit_metrics.py` |
| E2E secret scanning | EXISTS | truffleHog in `security-hardening.yml` |

---

## Secrets Scan

### CI Pattern Detection (`.github/workflows/ci.yml`)
```bash
grep -rE "(API_KEY|SECRET|PASSWORD)\s*=\s*['\"][^'\"]+['\"]" src/ \
  --include="*.py" --include="*.ts" --include="*.js" \
  | grep -v "test" | grep -v ".env.example" \
  | grep -v "os.getenv" | grep -v "os.environ"
```
**Result:** No matches found — CI exits 0

### Advanced Scan (`security-hardening.yml`)
- **truffleHog** filesystem scan on full git history (`fetch-depth: 0`)
- Pattern: `--only-verified --fail` (continue-on-error)
- Hardcoded secret pattern check: 16+ char values assigned to key vars

### Local Verification
```bash
# Run performed during audit:
grep -rE "(API_KEY|SECRET|PASSWORD|TOKEN)\s*=\s*['\"][a-zA-Z0-9]{10,}['\"]" src/ \
  --include="*.py" | grep -v "os.getenv\|os.environ\|example\|test\|mock"
```
**Result: 0 matches** — CLEAN

### Config.py Pattern (correct)
```python
# src/config.py — safe pattern
TELEGRAM_API_TOKEN: str = os.getenv("TELEGRAM_API_TOKEN", "")
```
All API keys loaded from environment via `dotenv`, never hardcoded.

---

## .gitignore Coverage

**Covered:**
- `.env`, `.env.local` — root env files
- `__pycache__/`, `*.pyc`, `.venv/`, `venv/` — Python artifacts
- `node_modules/`, `.next/`, `dist/`, `.cache/` — Node artifacts
- `.vscode/`, `.idea/` — IDE configs
- `.coverage`, `.pytest_cache/` — test artifacts

**Gap identified:** `.env.local`, `.env.*.local` covered but not `.env.production`, `.env.staging`. These could be accidentally committed. Recommend adding:
```
.env.production
.env.staging
.env.development
```

---

## Command Injection Prevention

**`src/security/command_sanitizer.py`** — dedicated sanitizer class:

### DANGEROUS_PATTERNS blocked:
| Pattern | Example |
|---------|---------|
| `command_substitution` | `$(cmd)` or `` `cmd` `` |
| `pipe_injection` | `\| bash`, `\| sh` |
| `redirect_danger` | `> /etc/`, `> /root/` |
| `eval_exec` | `eval()`, `exec()`, `os.system()` |
| `base64_decode` | `base64 -d` |
| `curl_pipe_bash` | `curl url \| bash` |
| `rm_rf_root` | `rm -rf /` |
| `fork_bomb` | `:(){:\|:&};:` |
| `shutdown` | `shutdown`, `reboot`, `halt` |

### Tests
- `test_subsystem_health.py` and `security-hardening.yml` both test sanitizer
- `command-injection-scan` job in security workflow validates sanitizer

---

## Authentication & Authorization

- `src/middleware/auth_middleware.py` — JWT-based auth (71 lines)
- `src/auth/` module exists — OAuth2, session management
- `src/security/attestation_generator.py` — license attestation (123 lines)
- `src/services/license_enforcement.py` — tier-based access control
- HTTP 402 returned on zero MCU balance

### JWT Refresh
- `src/core/jwt_refresh_client.py` — token refresh logic

---

## Rate Limiting

- `src/telemetry/rate_limit_metrics.py` — RateLimitMetricsEmitter class
- Events persisted to `rate_limit_events` table (migration `006_create_rate_limit_events.sql`)
- Tests: `test_rate_limiting_failing_tests.md`, `test_tenant_rate_limiting.py`, `test_tier_rate_limiting.py`
- `test_credit_rate_limiter.py` — credit-based rate limiting

---

## Dependency Security

### Python (`requirements.txt`)
```bash
# CI command:
safety check -r requirements.txt --ignore 70612
```
- CVE 70612 explicitly ignored — **document the reason** (likely known false positive)
- Bandit SAST: `bandit -r src/ -ll --exit-zero` — runs but never fails CI

### Node.js
- No `npm audit` step in frontend CI job
- Recommendation: add `npm audit --audit-level=high` to `frontend` job

---

## Security Workflows Summary

| Workflow | Trigger | Jobs |
|----------|---------|------|
| `ci.yml` security job | push/PR to main | Bandit, Safety, secret grep |
| `security-hardening.yml` | push/PR to main | truffleHog, .env check, patterns, command-injection |

Both workflows use `continue-on-error: true` on most steps — **security failures don't block merges**. This is the primary risk.

---

## Recommendations

1. **CRITICAL: Remove `continue-on-error: true` from secret scanning** — let it fail the build
2. Add `npm audit --audit-level=high` to frontend CI job
3. Document why CVE 70612 is ignored in `requirements.txt` comment
4. Add `.env.production`, `.env.staging` to `.gitignore`
5. Enable branch protection on `main` requiring security checks to pass
6. Consider upgrading Bandit from `--exit-zero` to hard failure for HIGH severity
7. Add CODEOWNERS file review requirement for `src/security/`, `src/auth/`

---

## Security Score: 7/10

Strong foundation (sanitizer, JWT, rate limiting, attestation) but CI soft-failures undermine enforcement.
