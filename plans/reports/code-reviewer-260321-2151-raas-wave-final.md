# Code Review: RaaS Wave Final

**Date:** 2026-03-21
**Reviewer:** code-reviewer agent
**Verdict:** APPROVE with notes

---

## Scope

| File | LOC | Focus |
|------|-----|-------|
| `packages/mekong-cli-core/src/core/pev-bridge.ts` | 131 | Core PEV orchestrator |
| `packages/mekong-cli-core/src/cli/commands/cloud-run.ts` | 89 | CLI cloud run command |
| `packages/mekong-cli-core/src/integration/raas-e2e.test.ts` | 217 | E2E integration tests |
| `packages/raas-dashboard/public/index.html` | 111 | Dashboard HTML shell |
| `packages/raas-dashboard/public/dashboard.css` | 71 | Dashboard styles |
| `packages/raas-dashboard/public/dashboard-api-client.js` | 121 | Dashboard API client |
| `.github/workflows/npm-publish.yml` | 71 | npm publish CI workflow |

**Total:** 811 LOC across 7 files

---

## Overall Assessment

Code quality is solid across all files. Clean separation of concerns, proper error handling in CLI, XSS escaping in dashboard renderers. No critical security issues found.

---

## Critical Issues

None found.

---

## High Priority

### H1. Dashboard `renderOverview()` uses innerHTML without escaping numeric API values (XSS risk)

**File:** `dashboard-api-client.js:45-49`

`renderOverview()` injects `t.total`, `m.total`, `c.totalEarned` etc. directly into innerHTML via template literals. These come from API response and are expected to be numbers, but if the API is compromised or returns string payloads, this is an XSS vector.

All other renderers (`renderTenants`, `renderMissions`, `renderCredits`) correctly use `esc()` for string fields -- good. But overview stats skip escaping entirely.

**Fix:** Wrap all interpolated values in `esc()` or `Number()` coercion:
```js
<div class="val">${Number(t.total)||0}</div>
```

### H2. Admin API key stored in localStorage (credential exposure)

**File:** `dashboard-api-client.js:20-21`

`localStorage` is accessible to any JS on the same origin (XSS = key theft). For an admin dashboard this is an accepted trade-off if the dashboard is served from a dedicated origin, but worth noting.

**Mitigation:** Add CSP headers when serving the dashboard. Consider `sessionStorage` instead so keys don't persist across tabs/sessions.

### H3. Test file exceeds 200-line limit (217 lines)

**File:** `raas-e2e.test.ts` (217 LOC)

Per project rules, files should be under 200 lines. This test file is marginally over. Could split the mock-fetch test suites (Signup, Mission, Billing) into a separate file.

---

## Medium Priority

### M1. PEV Bridge emits untyped events

**File:** `pev-bridge.ts:36`

`PEVBridge extends EventEmitter` but `PEVEvents` interface is defined yet never enforced at the type level. The `emit()` and `on()` calls are untyped -- any event name string is accepted.

**Fix:** Use a typed EventEmitter pattern or add overload signatures:
```ts
declare interface PEVBridge {
  on<K extends keyof PEVEvents>(event: K, listener: (...args: PEVEvents[K]) => void): this;
  emit<K extends keyof PEVEvents>(event: K, ...args: PEVEvents[K]): boolean;
}
```

### M2. No URL validation in dashboard login

**File:** `index.html:86-89`, `dashboard-api-client.js:19`

`doLogin()` checks fields are non-empty but doesn't validate URL format. A malformed URL would silently fail on first fetch. The `<input type="url">` provides browser-level validation but `doLogin()` bypasses form submission, so browser validation is not triggered.

**Fix:** Add `try { new URL(url) } catch { ... }` validation in `saveConfig()` or `doLogin()`.

### M3. GitHub Actions workflow: `--passWithNoTests` flag

**File:** `npm-publish.yml:66`

`pnpm --filter "${{ matrix.package }}" test --passWithNoTests` silently passes packages with zero tests. This is fine during bootstrap but should be removed once test suites are established, otherwise regressions can slip through if all tests are accidentally deleted.

### M4. Unused `fsExistsResult` variable in test

**File:** `raas-e2e.test.ts:15`

`let fsExistsResult = false;` is declared but never read. Dead code.

### M5. Unused `tmpdir` and `mkdtempSync` imports

**File:** `raas-e2e.test.ts:8-9`

```ts
import { tmpdir } from 'node:os';
import { mkdtempSync } from 'node:fs';
```

Neither is used anywhere in the file.

---

## Low Priority

### L1. `clearInterval(refreshTimer)` called on null-safe `refreshTimer`

**File:** `dashboard-api-client.js:28`

`clearInterval(null)` is a no-op in browsers, so functionally fine. But `refreshTimer` should be typed or initialized consistently.

### L2. Magic number 2 hardcoded in verify retry check

**File:** `cloud-run.ts:48`

```js
if (!passed && retries < 2)
```

Should reference `MAX_VERIFY_RETRIES` from pev-bridge instead of hardcoding `2`. If the constant changes, this UI message will be wrong.

### L3. `fmtDate` catch clause is empty

**File:** `dashboard-api-client.js:99`

```js
try { return new Date(s).toLocaleDateString(); } catch { return s; }
```

Acceptable for a utility, but `new Date()` doesn't throw on invalid input -- it returns `Invalid Date`. The catch is unreachable. Better: check `isNaN(date.getTime())`.

---

## Positive Observations

1. **XSS protection in renderers** -- `esc()` function properly handles `& < > " '` and is used consistently for all user-data string fields
2. **Credential file permissions** -- `raas-client.ts:36` uses `mode: 0o600` for credentials file, good security practice
3. **Clean PEV architecture** -- plan/execute/verify with retry loop is well-structured, timeout protection prevents infinite polling
4. **Error handling in CLI** -- `cloud-run.ts` properly handles `PEVTimeoutError` separately, sets `process.exitCode` instead of `process.exit()` (allows cleanup)
5. **CI safety checks** -- `npm-publish.yml` validates package path prefix and uses `--frozen-lockfile`, `--no-git-checks`
6. **Least-privilege CI permissions** -- `contents: read` only, no write access
7. **All files under 200-line limit** except test file (marginal at 217)

---

## Recommended Actions

1. **[HIGH]** Escape or coerce numeric values in `renderOverview()` to close XSS gap
2. **[HIGH]** Consider `sessionStorage` over `localStorage` for admin key
3. **[MED]** Add typed event emitter to PEVBridge
4. **[MED]** Add URL validation in dashboard login flow
5. **[MED]** Remove dead imports/variables in test file (`fsExistsResult`, `tmpdir`, `mkdtempSync`)
6. **[LOW]** Import `MAX_VERIFY_RETRIES` in cloud-run.ts instead of hardcoding
7. **[LOW]** Fix `fmtDate` to check `isNaN` instead of relying on unreachable catch

---

## Metrics

| Metric | Value |
|--------|-------|
| Files reviewed | 7 |
| Total LOC | 811 |
| File size violations | 1 (test file, 217 LOC -- marginal) |
| Critical issues | 0 |
| High issues | 3 |
| Medium issues | 5 |
| Low issues | 3 |

---

## Unresolved Questions

- Is the dashboard intended to be served from a dedicated origin with CSP headers? If so, localStorage for admin key is acceptable. If served alongside other content, sessionStorage or httpOnly cookie approach is safer.
- Should `--passWithNoTests` be removed from CI now or tracked as a follow-up once test coverage is established?
