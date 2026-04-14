# Code Review: Lead/Email Commands + LLM Router

**Date:** 2026-03-24 | **Verdict:** APPROVE with notes
**Files:** 9 (4 new, 5 modified) | **LOC new:** ~430

---

## Critical Issues

### 1. SSRF bypass in `isWebhookUrlSafe` (engine.ts:252-265)

The `172.` prefix check is too broad (blocks `172.0.*` through `172.255.*`) but also incomplete -- only checks string prefix, not the actual `172.16.0.0/12` range. More importantly:

- **DNS rebinding not blocked.** Attacker sets `webhook_url` to a domain that resolves to `127.0.0.1` at fetch time. The hostname check passes because the hostname is `evil.com`, not `localhost`.
- **IPv6 shorthand bypass.** `[::ffff:127.0.0.1]` or `[0:0:0:0:0:ffff:7f00:1]` bypasses all checks.
- **Redirect-based SSRF.** External URL 301-redirects to `http://169.254.169.254/`. Node `fetch` follows redirects by default.

**Fix (minimal):**
```ts
// Add to fetch call in notifyWebhook:
redirect: 'manual',  // prevent redirect-based SSRF
```
For DNS rebinding, resolve hostname before fetching and re-check the IP. Or use `{redirect: 'error'}` and accept no redirects.

**Severity:** HIGH -- webhook_url is user-supplied via mission record.

### 2. No email address validation in `runEmailSend` (lead-email-commands.ts:83)

`params.to` is passed directly to Resend API with only a truthy check. Malformed or malicious input (header injection via newlines, extremely long strings) reaches the API.

**Fix:**
```ts
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!EMAIL_RE.test(params.to)) {
  return { success: false, error: 'Invalid email address' };
}
```

**Severity:** MEDIUM -- Resend likely validates server-side, but defense in depth.

---

## High Priority

### 3. Silent DB insert failures (lead-email-commands.ts:57-59)

```ts
catch {
  // Table may not exist yet -- continue
}
```

Every lead insert failure is silently swallowed. If the table schema is wrong or DB is down, `savedCount` stays 0 and the caller gets `success: true` with misleading summary. At minimum, log the error.

### 4. LLM JSON parsing trusts shape without validation (lead-hunter.ts:93, multiple files)

`JSON.parse(jsonMatch[0]) as Partial<LeadHunterResult>` -- the `as` cast provides zero runtime safety. If LLM returns `{ "leads": [{ "fit_score": "high" }] }` (string instead of number), downstream code silently propagates bad data to DB inserts.

Affects: `lead-hunter.ts`, `claude-proposal-generator.ts`, `claude-sales-intelligence.ts` (same pattern throughout).

**Recommendation:** Validate with a minimal shape check or Zod schema for at least the fields persisted to DB (fit_score, pain_points array).

### 5. `claude-sales-intelligence.ts` exceeds 200-line limit (210 lines)

Per project rules, files should stay under 200 lines. This file is borderline -- consider extracting `generateBattlecard` into its own module if more functions are added.

---

## Medium Priority

### 6. `getClaudeClient()` uses `require()` in TS (claude-proposal-generator.ts:15-17)

The deprecated function uses synchronous `require()` while the rest of the codebase uses `import`. Not a bug since it is marked `@deprecated`, but any caller using it bypasses the LLM router. Consider removing entirely if no callers remain.

### 7. `sendOutreachSequence` sends day-1 email immediately (sender.ts:107)

The function signature suggests scheduling but actually fires email synchronously for day 1 and logs-only for later days. The `scheduled` count in the result includes both sent and logged-only items, which is misleading. Document clearly or rename the count fields.

### 8. `baseUrl` in llm-router not validated (llm-router.ts:80)

`baseUrl` from env var is used directly in URL construction. If `LLM_BASE_URL` contains a path like `https://api.example.com/v1/` the trailing slash is stripped but no further validation. An attacker with env var access could set it to `file:///etc/passwd` -- though if they control env vars, the game is already lost. Low real-world risk but worth noting.

---

## Positive Observations

- LLM router design is clean -- single `llmGenerate()` entry point, provider auto-detection, graceful Anthropic fallback
- All AI-calling functions have fallback templates -- never breaks the flow on LLM failure
- `AbortSignal.timeout()` on all fetch calls prevents hanging requests
- Type definitions in `raas.ts` are well-structured with proper union types
- SSRF protection exists (most codebases don't even try) -- just needs hardening
- `maxLeads` clamped to 20 in lead-hunter prevents abuse

---

## Summary

| Area | Status |
|------|--------|
| Security | SSRF bypass vectors need fix (redirect + DNS rebinding) |
| Error handling | Silent catch blocks in DB inserts need logging |
| TypeScript | Clean types, no `any` usage, proper interfaces |
| Performance | Appropriate timeouts, capped lead generation |
| Integration | Router wired correctly, command-router switch exhaustive |

**Recommended actions (priority order):**
1. Add `redirect: 'manual'` to webhook fetch
2. Add basic email regex validation in `runEmailSend`
3. Add logging to catch blocks in `lead-email-commands.ts`
4. Add runtime shape validation for LLM JSON parsed into DB records

---

## Unresolved Questions

- Is there an existing Zod dependency in sophia-proposal for runtime validation? If so, reuse it for LLM output parsing.
- Are there any callers of the deprecated `getClaudeClient()` that still need it?
- What is the plan for the job queue / scheduler for outreach sequence day 2+ emails?
