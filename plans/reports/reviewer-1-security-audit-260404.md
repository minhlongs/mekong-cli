# Security Audit Report — Mekong CLI v6.0

**Date:** 2026-04-04
**Auditor:** Code Reviewer Agent (Opus 4.6)
**Scope:** `src/`, `ide-core/`, `mekong/`, `scripts/`, root config files
**Method:** Static analysis, pattern matching, manual code review

---

## CRITICAL FINDINGS

### C1. Vercel OIDC JWT Token Committed to Git (PUBLIC REPO)

**Severity:** CRITICAL
**File:** `apps/dashboard/.env.local` (tracked in git via `git ls-files`)
**Evidence:** Full JWT token exposed:
```
VERCEL_OIDC_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Im1yay00MzAy..."
```
Decoded payload reveals: project `dashboard`, owner `minh-longs-projects-f5c82c9b`, team `team_nLLphBYdo5mpHIgVzf0npMOp`, user ID, Vercel Pro plan.

**Impact:** Any internet user can decode this JWT. Even if expired, it leaks internal Vercel project IDs, team IDs, and user identity. Attackers could use this to enumerate or target the Vercel account.

**Recommendation:**
1. `git rm --cached apps/dashboard/.env.local` immediately
2. Rotate any Vercel credentials associated with this project
3. Add `apps/dashboard/.env.local` to `.gitignore` (already partially covered but file was committed before rule)
4. Run `git filter-branch` or `bfg` to purge from history since this is a public repo

---

### C2. `eval()` Used on Dynamic Condition Strings in Binh Phap Reactions

**Severity:** CRITICAL
**File:** `src/binh_phap/reactions.py:219`
**Evidence:**
```python
if not eval(reaction.condition, {"data": data}):
    continue
```
`reaction.condition` is a string evaluated as Python code. If any reaction condition is influenced by external input (event data, user-supplied configs, LLM output), this is a direct **arbitrary code execution** vulnerability.

**Impact:** Full RCE if an attacker can influence reaction condition strings. Even with `{"data": data}` as the namespace, `eval` can escape to `__builtins__`.

**Recommendation:** Replace `eval()` with a safe expression evaluator:
```python
# Option A: ast.literal_eval for simple comparisons
# Option B: Use a restricted expression parser like simpleeval
from simpleeval import simple_eval
if not simple_eval(reaction.condition, names={"data": data}):
```

---

### C3. Executor Uses `shell=True` Without Sanitizer Integration

**Severity:** CRITICAL
**File:** `src/core/executor.py:312-313`
**Evidence:**
```python
process = subprocess.run(
    command, shell=True, check=True, text=True, capture_output=True
)
```
The `command` variable comes from `step.description.strip()` (recipe step content parsed from Markdown). No call to `CommandSanitizer` exists in `executor.py` — grep confirms zero references.

**Impact:** Any recipe containing shell metacharacters executes with full shell expansion. If recipes are fetched from external sources, plugins, or LLM output, this is command injection.

**Recommendation:** Integrate `CommandSanitizer` from `src/security/command_sanitizer.py` before execution:
```python
from src.security.command_sanitizer import sanitize_command
result = sanitize_command(command)
if not result.is_safe:
    return ExecutionResult(exit_code=1, stderr=f"Blocked: {result.blocked_patterns}")
# Then use shlex.split(command) without shell=True
```

---

### C4. NOWPayments Webhook Skips Signature Verification When Secret Missing

**Severity:** CRITICAL
**File:** `src/raas/nowpayments-webhook-handler.py:49-51`
**Evidence:**
```python
if not IPN_SECRET:
    logger.warning("NOWPAYMENTS_IPN_SECRET not set — skipping verification")
    return True  # Accepts ANY webhook payload
```
When `NOWPAYMENTS_IPN_SECRET` is not set, ALL incoming webhooks are accepted as valid. An attacker can forge payment completion webhooks to grant themselves unlimited credits.

**Impact:** Free credits / credit fraud. Attacker sends forged `payment_status: "finished"` webhooks to grant credits to any workspace.

**Recommendation:** Reject webhooks when secret is not configured:
```python
if not IPN_SECRET:
    logger.error("NOWPAYMENTS_IPN_SECRET not set — rejecting webhook")
    return False
```

---

## IMPORTANT FINDINGS

### I1. JWT Decoded Without Signature Verification (auth_jwt.py)

**Severity:** IMPORTANT
**File:** `src/core/auth_jwt.py:19-53`
**Evidence:** `decode_jwt()` function base64-decodes the payload without verifying the cryptographic signature. Comment says "edge-side validation only" but this function is used in `raas_auth.py` for tenant extraction.

**Impact:** If any code path trusts the decoded payload for authorization decisions without gateway verification, an attacker can forge JWT claims (tenant_id, tier, role).

**Recommendation:** Ensure all authorization-critical paths use `session_manager.decode_token()` (which uses `pyjwt` with signature verification), not `auth_jwt.decode_jwt()`. Add explicit warning in docstring: "DO NOT use for authorization decisions."

---

### I2. CORS Configured as `allow_origins=["*"]` with `allow_credentials=True`

**Severity:** IMPORTANT
**Files:**
- `src/gateway.py:74` — `allow_origins=["*"]`
- `src/core/gateway/gateway_main.py:195` — `allow_origins=["*"]`

**Evidence:** Both gateways set:
```python
allow_origins=["*"],
allow_credentials=True,
```

**Impact:** `allow_origins=*` with `allow_credentials=True` is a security anti-pattern. Browsers actually block this combination (credentials require specific origins), but it signals misconfiguration. Any origin can make credentialed requests if the browser implementation is lax. CSRF attacks become trivial against the API.

**Recommendation:** Restrict to actual frontend origins:
```python
allow_origins=["https://agencyos.network", "http://localhost:3000"],
```

---

### I3. Windows Vault Backend — PowerShell Command Injection

**Severity:** IMPORTANT
**File:** `src/auth/secure_storage.py:153-154`
**Evidence:**
```python
escaped_value = value.replace('"', '""')
command = f'cmdkey /generic:"{self.SERVICE_NAME}:{key}:{self.account}" /user:"{self.account}" /pass:"{escaped_value}"'
returncode, stdout, stderr = self._run_powershell(command)
```
The `key` parameter is not sanitized and is interpolated into a PowerShell command string. Characters like `;`, `|`, or backticks in `key` could inject arbitrary PowerShell commands.

**Impact:** If an attacker controls the `key` parameter, they can execute arbitrary commands on Windows. The `value` escaping is also insufficient — `""` escaping does not handle all PowerShell injection vectors (e.g., `$(...)` subexpressions).

**Recommendation:** Use `subprocess.run(["cmdkey", "/generic:...", ...])` with argument list instead of PowerShell string interpolation. Or use the `keyring` library.

---

### I4. Plugin Loader Executes Arbitrary Python from User Directory

**Severity:** IMPORTANT
**File:** `src/core/plugin_loader.py:90-98`
**Evidence:**
```python
for fpath in sorted(pdir.glob("*.py")):
    spec = importlib.util.spec_from_file_location(fpath.stem, fpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # Executes arbitrary code
```
Files from `~/.mekong/plugins/` are loaded and executed. While `plugin_validator.py` exists, `plugin_loader.py` does NOT call the validator before loading.

**Impact:** If an attacker writes a malicious `.py` file to `~/.mekong/plugins/`, it executes on next CLI startup with full user privileges.

**Recommendation:** Call `PluginValidator.validate_all()` before `exec_module()` and refuse to load plugins that fail validation.

---

### I5. Tool Registry Builtin `shell:run` Bypasses All Security

**Severity:** IMPORTANT
**File:** `src/core/tool_registry.py:421`
**Evidence:**
```python
("shell:run", "Execute a shell command", "sh -c '{command}'"),
```
This builtin tool template wraps user input in `sh -c`. While `execute()` uses `shlex.quote()` on params, the template format `sh -c '{command}'` with a single-quoted `{command}` may interact poorly with `shlex.quote()` which also adds single quotes, creating shell escaping edge cases.

Additionally, `file:write` template `echo '{content}' > {path}` allows arbitrary file writes.

**Recommendation:** Remove `shell:run` and `file:write` from builtins or add sandbox capability checks before execution.

---

## MODERATE FINDINGS

### M1. `.env.unified` and `config.env` Committed to Git

**Severity:** MODERATE
**Files tracked in git:**
- `.env.unified` — domain config (no secrets, but sets production expectations)
- `ide-core/engine-farm/config.env` — model configuration (no API keys, but leaks internal model strategy)

**Impact:** Low direct risk (no credentials), but violates security posture. Any `.env*` file in a public repo trains contributors to commit env files.

**Recommendation:** `git rm --cached .env.unified ide-core/engine-farm/config.env` and add to `.gitignore`.

---

### M2. Weak Machine-Derived Encryption Keys (Linux/Windows Secure Storage)

**Severity:** MODERATE
**File:** `src/auth/secure_storage.py:218-240`
**Evidence:**
```python
machine_id = platform.node() + platform.machine()
salt = "mekong-cli-secure-storage-v1"
key_material = f"{machine_id}:{salt}"
return hashlib.sha256(key_material.encode()).digest()
```
Encryption key is derived from hostname + architecture + static salt. Hostname is often publicly known. No PBKDF2/Argon2 key stretching.

**Impact:** If `~/.mekong/credentials.enc` is exfiltrated, decryption is trivial with knowledge of the hostname.

**Recommendation:** Use `cryptography.hazmat.primitives.kdf.pbkdf2.PBKDF2HMAC` with a random salt stored alongside the ciphertext, or use OS keyring via the `keyring` Python library.

---

### M3. Code Evolution Engine Can Self-Modify Agent Source Code

**Severity:** MODERATE
**File:** `src/core/code_evolution.py:79`
**Evidence:**
```python
SAFE_DIRS: List[str] = ["src/core", "src/agents"]
```
The self-modification engine allows LLM-generated code to be written to `src/core/` and `src/agents/`. While `governance.py` and `code_evolution.py` are excluded, an LLM could modify critical security files like `command_sanitizer.py`, `auth_jwt.py`, or `agent_execution_sandbox.py`.

**Recommendation:** Add security-critical files to `FORBIDDEN_FILES`:
```python
FORBIDDEN_FILES = [
    "governance.py", "code_evolution.py",
    "command_sanitizer.py", "auth_jwt.py", "agent_execution_sandbox.py",
    "plugin_validator.py", "command_authorizer.py",
]
```

---

### M4. CommandSanitizer Regex Bypass via Encoding/Whitespace

**Severity:** MODERATE
**File:** `src/security/command_sanitizer.py:28`
**Evidence:** The `command_substitution` pattern `r"\$\(.*?\)|`.*?`"` uses non-greedy matching and does not handle nested substitutions or multiline input. Patterns like `$(echo$(id))` or encoded variants could bypass detection.

Also, the sanitizer returns the *original command* when `shlex.split` fails (line 120-121), with only a warning.

**Recommendation:**
1. On `shlex.split` failure, mark as unsafe instead of passing through
2. Add tests for nested command substitution
3. Consider allowlist approach instead of denylist

---

### M5. Broad `except Exception: pass` in YAML Loading

**Severity:** MODERATE
**Files:**
- `src/core/tool_registry.py:515-516` — `except Exception: pass`
- `src/core/code_evolution.py:559-560` — `except Exception: self._journal = []`

**Impact:** Silently swallows corruption, deserialization errors, or permission issues. A corrupted YAML file could disable the tool registry or evolution journal without any log entry.

**Recommendation:** At minimum, log the exception at warning level.

---

## POSITIVE OBSERVATIONS

1. **Session Manager JWT handling** (`src/auth/session_manager.py`) properly uses `pyjwt` with signature verification, HS256, and enforces `JWT_SECRET=REDACTED` in production
2. **Verifier** (`src/core/verifier.py:379`) uses `shlex.split()` to avoid shell injection
3. **Code Evolution** validates generated code via AST parsing and dangerous pattern detection before writing
4. **Secure Storage** uses AES-256-GCM with proper nonce handling, 0o600 file permissions on Linux
5. **Rate limiting** infrastructure exists across 82+ files with credit-based and tier-based enforcement
6. **Plugin Validator** exists with AST-based import scanning and secret detection
7. **OAuth2** implementation uses PKCE and CSRF state parameters correctly
8. **Cookie config** uses HTTPOnly, Secure (in production), and SameSite attributes

---

## Summary by Severity

| Severity | Count | Verdict |
|----------|-------|---------|
| CRITICAL | 4 | **REQUEST_CHANGES** |
| IMPORTANT | 5 | Must fix before production |
| MODERATE | 5 | Fix in next sprint |

**Overall Verdict: REQUEST_CHANGES**

The Vercel OIDC token in git history (C1) and the `eval()` RCE (C2) require immediate remediation. The executor `shell=True` without sanitizer (C3) and webhook signature bypass (C4) must be fixed before any production deployment.

---

## Recommended Priority Actions

1. **IMMEDIATE:** Remove `apps/dashboard/.env.local` from git, purge history with `bfg`, rotate Vercel credentials
2. **IMMEDIATE:** Replace `eval()` in `reactions.py` with safe expression evaluator
3. **THIS WEEK:** Wire `CommandSanitizer` into `executor.py`, switch to `shell=False`
4. **THIS WEEK:** Reject webhooks when IPN secret is not configured
5. **THIS WEEK:** Restrict CORS origins in both gateways
6. **NEXT SPRINT:** Wire `PluginValidator` into `PluginLoader`, harden secure storage key derivation, expand `FORBIDDEN_FILES` in code evolution
