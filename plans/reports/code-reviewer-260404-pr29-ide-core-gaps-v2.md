# Code Review: PR #29 — close IDE-core gaps v2

**Repo:** longtho638-jpg/mekong-cli | **Branch:** claude/close-ide-core-gaps-v2
**Scope:** 1,676 files, +58,483/-46,159 lines
**Date:** 2026-04-04

## Score: 4/10 — REQUEST_CHANGES

## Critical Issues

### C1. LEAKED VERCEL OIDC JWT TOKEN (SEVERITY: CRITICAL)

File `apps/dashboard/.env.local` is being DELETED but the diff exposes a full JWT:
```
-VERCEL_OIDC_TOKEN="eyJhbGciOiJSUzI1NiIs..."
```
This token was committed to git history in a previous commit and is now visible in diff.
The token contains: project ID (`prj_zdtBk57Aiv19cV06h8qoHxlLQruZ`), team ID, user ID.

**Action required:**
1. Rotate the Vercel OIDC token immediately (if Vercel account still active)
2. Add `*.env.local` to `.gitignore` if not already present
3. Consider `git filter-branch` or BFG to purge from history (public repo)

### C2. `escaped_value` STILL INJECTABLE in `secure_storage.py`

The PR adds `_sanitize_credential_name()` for key/account (good), but the credential
VALUE is only escaped with `.replace('"', '""')` before being embedded in a PowerShell
command string:
```python
escaped_value = value.replace('"', '""')
command = f'cmdkey ... /pass:"{escaped_value}"'
```
This does NOT prevent injection via backtick `` ` ``, `$()`, or `$(...)` in PowerShell.
An attacker-controlled credential value can execute arbitrary commands.

**Fix:** Use `subprocess.run(["cmdkey", ...])` with list args instead of shell string,
or apply the same strict sanitization to values.

### C3. CommandSanitizer ImportError = SILENT BYPASS

In `tool_registry.py`, if `CommandSanitizer` import fails, shell:run executes unsanitized:
```python
except ImportError:
    logger.warning("CommandSanitizer unavailable; shell:run executing without sanitization")
```
This is a fail-open security pattern. If the module is missing or renamed, all shell
commands execute without any sanitization.

**Fix:** Fail closed. Raise RuntimeError on ImportError instead of logging a warning.

## High Priority

### H1. API Key Validation is Still Stub

`src/polymarket/api_server.py` accepts ANY non-empty token:
```python
return APIKeyInfo(key=token, tier="starter", ...)
```
Comment changed from "TODO" to description but behavior unchanged. Any request with
`Authorization: Bearer anything` gets full API access. Not safe for any environment.

### H2. Tests Are Not Pytest-Compatible

Both `test_e2e_mission.py` and `test_10_missions.py` use `asyncio.run()` with manual
`sys.path.insert()` and `if __name__ == "__main__"` runners. They won't be discovered
by pytest without `pytest-asyncio` markers. They require a live LLM provider, making
them integration tests that can't run in CI without infrastructure.

### H3. PR Size Is Unreviable

1,676 files in one PR is impossible to review thoroughly. Contains:
- ~290 command .md files (bulk generated)
- ~220 dashboard stub pages (hardcoded fake data)
- ~200+ factory contract JSON files
- 12 Clipmart AGENTS.md files
- Core Python changes mixed in

Should be split into at minimum: (1) command files, (2) dashboard scaffold,
(3) core Python changes, (4) config/tooling.

## Medium Priority

### M1. Dashboard Pages Are Hardcoded Stubs

220 dashboard pages all follow identical pattern with hardcoded numbers:
```tsx
<span>Workers</span><span>4</span>
<span>Missions</span><span>12</span>
<span>Success</span><span>94%</span>
```
No data fetching, no API integration, no components. Pure HTML with inline CSS vars.
These add 220 files of maintenance burden with zero functionality.

### M2. `command_loader.py` Global Mutable State

Uses module-level `_COMMANDS: list[Command] | None = None` with no thread safety.
If `get_commands()` is called concurrently from async handlers, race condition on
the global cache. Use `functools.lru_cache` or `threading.Lock`.

### M3. Dashboard Config is Fine but Minimal

- `next.config.mjs`: Valid Next.js 15 config, `@tailwindcss/postcss` in postcss is correct for Tailwind v4
- `tsconfig.json`: Standard Next.js config with bundler moduleResolution
- `layout.tsx`: Clean, correct
- `globals.css` token path fix (`./tokens/` -> `../styles/tokens/`): correct relative path fix

### M4. `bin/mekong` Missing Execute Permission Check

No `chmod +x` ensured in package.json scripts or install docs. The fallback error
message references `npm run dev` which may not exist in Python-only installs.

## Low Priority

- STRATEGY.md is a non-technical narrative doc; no code impact
- `config.env` contains no secrets (only model names and localhost config) -- acceptable
- `.env.local.example` and `.env.example` contain only placeholder values -- good

## Positive Observations

1. `_sanitize_credential_name()` in secure_storage.py is a real security improvement
   for the key/account injection vector previously identified
2. `find_best_command()` scoring algorithm is reasonable: role prefix (10pts) +
   keyword overlap (2pts/word) + domain boost (5pts) with threshold of 4
3. hybrid_router Stage 1.5 injection is clean: `command_system_prompt or system_prompt`
   fallback pattern is correct
4. Removing the Vercel .env.local file is the right direction (just needs history purge)
5. SQL migration additions (qwen-image-plus/max rate cards) are clean with proper
   ON CONFLICT handling

## Verdict: REQUEST_CHANGES

Must fix before merge:
1. **Purge JWT token from git history** (C1)
2. **Fix escaped_value injection in secure_storage.py** (C2)
3. **Fail closed on missing CommandSanitizer** (C3)
4. **Split PR** -- at minimum extract the 290 command .md files and 220 dashboard
   stubs into separate PRs so core Python changes can be reviewed properly

## Metrics

- Type Coverage: N/A (Python files lack type annotations on most functions)
- Test Coverage: Effectively 0% in CI (tests require live LLM)
- Security Issues: 3 critical
- Linting: Not verified (PR too large for automated check)
