# Sophia AI Factory — Tech Debt Scan Report

**Agent:** code-reviewer | **Date:** 2026-02-11 10:12
**Scope:** `apps/sophia-ai-factory/apps/sophia-ai-factory/src/`
**Files scanned:** ~278 TS/TSX source files

---

## Summary Counts

| Category | Count | Severity |
|----------|-------|----------|
| TODO / FIXME / HACK / XXX / TEMP / WORKAROUND | **0** | -- |
| console.log / console.warn / console.error (excl. logger-utility.ts) | **1** | Low |
| @ts-expect-error directives | **9** | Medium |
| @ts-ignore directives | **0** | -- |
| @ts-nocheck directives | **0** | -- |
| eslint-disable comments | **3** | Low |
| `as any` / `: any` type casts | **1** | Low |
| Hardcoded credentials / API keys / secrets | **0** | -- |

**Overall Tech Debt Score: LOW** — Codebase is well-maintained with minimal debt markers.

---

## Category 1: TODO / FIXME / HACK / XXX / TEMP / WORKAROUND

**Count: 0**

No tech debt comment markers found anywhere in `src/`. Clean.

---

## Category 2: Console Statements (excluding logger-utility.ts)

**Count: 1**

| # | File (relative to src/) | Line | Statement | Severity |
|---|------------------------|------|-----------|----------|
| 1 | `lib/ai/text-to-speech-generator-elevenlabs.ts` | 40 | `console.error(\`[ElevenLabs] API failed, falling back to mock: ${errMsg}\`)` | Low |

**Assessment:** This is a legitimate error log in a catch block for API failure fallback. Should be migrated to the project's structured `logger` utility (`lib/utils/logger-utility.ts`) for consistency, but not a production risk.

**Note on logger-utility.ts:** The logger at lines 83-84 uses `void formatLogEntry(entry)` — effectively a no-op. Logs are formatted but never output. This may be intentional for production cleanliness but means the structured logger is currently silent.

---

## Category 3: TypeScript Directive Suppressions

**Count: 9 @ts-expect-error, 0 @ts-ignore, 0 @ts-nocheck**

All 9 directives are `@ts-expect-error` (preferred over `@ts-ignore`), and all share the same root cause: **Supabase typed client limitations with Json column types**.

| # | File (relative to src/) | Line | Comment | Severity |
|---|------------------------|------|---------|----------|
| 1 | `lib/telegram/telegram-bot.ts` | 100 | `Known Supabase typing limitation with Json column types` | Medium |
| 2 | `lib/telegram/telegram-bot.ts` | 119 | `Known Supabase typing limitation with Json column types` | Medium |
| 3 | `lib/telegram/telegram-bot.ts` | 172 | `Known Supabase typing limitation with Json column types` | Medium |
| 4 | `lib/inngest/functions/generate-campaign.ts` | 84 | `Known Supabase typing limitation with update on tables with Json columns` | Medium |
| 5 | `lib/inngest/functions/auto-discover-affiliates.ts` | 127 | `Database type missing Relationships for Supabase generic inference` | Medium |
| 6 | `lib/intelligence/runner.ts` | 50 | `Known Supabase typing limitation with upsert on tables with Json columns` | Medium |
| 7 | `lib/ingestion/base-adapter.ts` | 62 | `Known Supabase typing limitation with upsert on tables with Json columns` | Medium |
| 8 | `app/actions/settings.ts` | 146 | `Known Supabase typing limitation with update on tables with Json columns` | Medium |
| 9 | `app/api/user/integrations/route.ts` | 38 | `Known Supabase typing limitation with upsert on typed tables` | Medium |

**Assessment:** All suppressions are well-documented with consistent descriptions. Root cause is a known Supabase TypeScript SDK limitation where the auto-generated types from `supabase gen types` do not properly handle `Json` / `jsonb` column types. This is an upstream issue, not a codebase deficiency. Resolution would require either:
- Custom type overrides/wrappers around Supabase client calls
- Waiting for Supabase SDK to improve Json column type inference
- Regenerating types with newer `supabase gen types` version

---

## Category 4: eslint-disable Comments

**Count: 3**

| # | File (relative to src/) | Line | Directive | Severity |
|---|------------------------|------|-----------|----------|
| 1 | `lib/ai/video-generator.ts` | 42 | `eslint-disable-next-line @typescript-eslint/no-unused-vars` | Low |
| 2 | `lib/ingestion/base-adapter.ts` | 79 | `eslint-disable-line @typescript-eslint/no-unused-vars` | Low |
| 3 | `app/actions/templates.ts` | 1 | `eslint-disable @typescript-eslint/no-unused-vars` (file-level) | Low |

**Assessment:**
- Items 1 and 2 are narrow, line-scoped suppressions for intentionally unused parameters (likely method signatures with required positional args). Acceptable pattern.
- Item 3 is a **file-level** disable, which is broader. The `templates.ts` server action file likely has unused import artifacts. This should be investigated — file-level disables can mask real issues.

---

## Category 5: `any` Type Usage

**Count: 1**

| # | File (relative to src/) | Line | Usage | Severity |
|---|------------------------|------|-------|----------|
| 1 | `lib/subscription.test.ts` | 27 | `} as any);` | Low |

**Assessment:** Single occurrence in a test file, used for mocking a Supabase client return value. Common and acceptable test pattern. No `any` types found in production source code.

---

## Category 6: Hardcoded Credentials / Secrets

**Count: 0 real credentials**

Test files use test fixture values (`'test-bot-token'`, `'test-key'`) in:
- `lib/gateway/adapters/telegram-notification-adapter.test.ts` (8 occurrences of `process.env.TELEGRAM_BOT_TOKEN = 'test-bot-token'`)
- `lib/heygen/heygen-client.test.ts` (1 occurrence of `HEYGEN_API_KEY: 'test-key'`)

**Assessment:** All are in `.test.ts` files with obvious test fixture values. No real secrets detected. Production code properly reads from `process.env.*`. Clean.

---

## Additional Observations

### Hardcoded Mock URLs in Production Code

`lib/ai/text-to-speech-generator-elevenlabs.ts` lines 49-56 contain hardcoded mock audio URLs from `www2.cs.uic.edu`. These are used as fallback when ElevenLabs API fails. While not a security risk, hardcoded external URLs in production code create a fragile dependency.

### Silent Logger

`lib/utils/logger-utility.ts` line 83-84: `void formatLogEntry(entry)` — the structured logger formats log entries but discards the output. All `logger.info()`, `logger.warn()`, `logger.error()` calls across the codebase are effectively no-ops. This was likely an intentional console cleanup, but it means the application has **zero runtime logging**.

---

## Verdict

The sophia-ai-factory codebase is in **excellent shape** for tech debt:
- Zero TODO/FIXME markers
- Zero hardcoded secrets
- Zero `any` types in production code
- All TypeScript suppressions are well-documented with consistent rationale
- Only 1 stray console statement
- eslint-disable usage is minimal and mostly line-scoped

**Primary concern:** The 9 `@ts-expect-error` directives for Supabase Json columns represent the largest cluster of tech debt. These should be revisited when Supabase upgrades their TypeScript SDK type generation.

**Secondary concern:** The silent logger utility means zero observability in production. If this was intentional for console cleanup compliance, consider re-enabling output behind `NODE_ENV` check or sending to a structured logging service.

---

## Unresolved Questions

1. Is the silent logger (`void formatLogEntry(entry)`) intentional or a cleanup side effect? The codebase has zero runtime logging as a result.
2. Should the file-level `eslint-disable` in `app/actions/templates.ts` be narrowed to specific lines?
3. Are the hardcoded mock audio URLs in `text-to-speech-generator-elevenlabs.ts` acceptable for production fallback, or should they be moved to config?
