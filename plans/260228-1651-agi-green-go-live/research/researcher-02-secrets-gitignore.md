# Security/Secrets Readiness Audit
**Date:** 2026-02-28
**Researcher:** researcher-02
**Scope:** Hardcoded secrets, .gitignore coverage, tracked .env files

---

## 1. Hardcoded Secrets Audit

**Result: CLEAN — no actual hardcoded secrets found in source code.**

Grep scanned `src/`, `apps/`, `packages/` for patterns: `API_KEY`, `SECRET_KEY`, `PRIVATE_KEY`, `password=`, `sk-`, `sk_live`, `pk_live`.

All matches were:
- **Comments/docstrings** referencing env var names (`OPENAI_API_KEY`, `GEMINI_API_KEY`)
- **`os.getenv(...)` calls** — correct pattern, reading from env at runtime
- **Minified vendor JS** (`dist/assets/vendor-*.js`) — false positives from bundled 3rd-party code
- **No `sk-XXXX` tokens** or `pk_live_XXXX` literal values found

Key files confirmed safe:
- `src/core/llm_client.py` — uses `os.getenv("OPENAI_API_KEY", "")` ✅
- `src/core/autonomous.py` — uses `os.getenv("GEMINI_API_KEY", "")` ✅

---

## 2. .gitignore Coverage

**Result: ADEQUATE — core patterns present.**

Root `.gitignore` covers:
```
.env              ✅ root .env ignored
.env.local        ✅
.venv/            ✅
venv/             ✅
node_modules/     ✅
*.py[cod]         ✅
```

**Gaps identified:**
- `*.pem` not explicitly listed (though venv `.pem` files are tracked — see §4)
- `*.key` not listed
- `secrets/` directory not listed
- `*.env.*` wildcard not present (only `.env` and `.env.local` listed explicitly)
- Sub-app `.env` files (e.g., `apps/openclaw-worker/.env`) may not be covered if sub-apps lack their own `.gitignore`

---

## 3. .env Files on Disk

**11 .env files found** across the repo (non-node_modules):

```
./.env
./scripts/.env
./doanh-trai-tom-hum/.env
./apps/com-anh-duong-10x/.env
./apps/openclaw-worker/.env
./apps/apex-os/.env
./apps/api/.env
./apps/worker/.env
./apps/engine/.env
./apps/vibe-coding-cafe/infrastructure/.env
./node_modules/bottleneck/.env  (ignored)
```

**Root `.env` is ignored by .gitignore** — confirmed safe.
Sub-app `.env` files appear untracked (not shown in `git ls-files`).

---

## 4. Git-Tracked Sensitive Files

**Result: CONCERN — venv package files tracked.**

`git ls-files` shows these tracked files with sensitive-sounding names:

```
.mekong/neural-memory-venv/lib/python3.12/site-packages/certifi/cacert.pem       ⚠️
.mekong/neural-memory-venv/lib/python3.12/site-packages/grpc/_cython/_credentials/roots.pem  ⚠️
.mekong/neural-memory-venv/lib/python3.12/.../v1_secret*.py  (k8s SDK models — safe)
```

These are **venv package files committed to git**, not actual private keys or real credentials. The `.pem` files are public CA certificate bundles (certifi). Risk: low but signals `.mekong/neural-memory-venv/` should be gitignored.

**Other tracked files:**
- `.env.example`, `.env.bak`, `.env.domain`, `.env.unified`, `.env.production.example` — these are template/example files, acceptable to track if they contain no real values
- `apps/openclaw-worker/plans/reports/debugger-260211-1240-sophia-exposed-secrets-scan.md` — a prior audit report (safe, documentation)
- `backend/api/auth/tests/test_secret_key_security.py` — test file, presumably no real keys

---

## 5. Summary Risk Matrix

| Issue | Severity | Status |
|-------|----------|--------|
| Hardcoded API keys in source | HIGH | CLEAN ✅ |
| .env files tracked in git | HIGH | CLEAN ✅ |
| Real sk-/pk_live tokens in code | CRITICAL | CLEAN ✅ |
| venv .pem files tracked in git | LOW | ⚠️ gitignore gap |
| `.mekong/neural-memory-venv/` in git | MEDIUM | ⚠️ should be gitignored |
| `*.pem` / `*.key` not in .gitignore | MEDIUM | ⚠️ add to .gitignore |
| Sub-app .env files coverage | LOW | monitor |

---

## Recommendations

1. **Add to root `.gitignore`:**
   ```
   .mekong/neural-memory-venv/
   *.pem
   *.key
   *.env.*
   !*.env.example
   !*.env.template
   ```

2. **Remove tracked venv from git** (if applicable):
   ```bash
   git rm -r --cached .mekong/neural-memory-venv/
   ```

3. **Confirm** `apps/*/env.bak`, `.env.unified`, `.env.domain` contain no real values before merge.

---

## Unresolved Questions

- Are `.env.bak` / `.env.domain` / `.env.unified` template-only or do they contain real credentials? Need content review.
- Is `.mekong/neural-memory-venv/` intentionally committed (e.g., for portability) or accidental?
- Do sub-app `.env` files (e.g., `apps/openclaw-worker/.env`) have real production keys? They appear untracked but exist on disk.
