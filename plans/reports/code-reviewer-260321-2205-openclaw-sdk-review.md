# Code Review: OpenClaw SDK + RaaS Docs | Score: 8/10

**Date:** 2026-03-21 | **Files:** 7 | **Tests:** 40/40 GREEN

## Overall: GOOD — Clean, typed, well-tested SDK facade

## Critical Issues: NONE

## High Priority

1. **Phantom exports in package.json** (lines 21-29) — `./raas`, `./orchestration/*`, `./intelligence/*`, etc. point to raw `src/` TS files, not built output. Consumers using Node resolution will get TS source (fails without transpilation). Either remove these or add tsup entries + dist mappings.

2. **Unreachable catch block in submitMission** (sdk.ts:119-129) — The try body is synchronous and never throws. The `catch` block (circuit breaker open logic, missionsFailed++) is dead code. Either add actual async execution logic or remove the try/catch to avoid false sense of error handling.

3. **setTimeout leak in maybeOpenCircuitBreaker** (sdk.ts:160-162) — `setTimeout` with 30s delay is not clearable. If engine is short-lived or GC'd, timer keeps running. Store ref for cleanup; add `destroy()` method.

## Medium Priority

4. **classifyComplexity regex false positive** — `/then/i` matches inside words like "au**then**tication". Test at line 78-82 documents this as known behavior but it is a bug, not a feature. Use word boundary: `/\b(and|then|after|also|plus)\b/i`.

5. **No input validation on submitMission** — Empty `goal` string accepted silently. No max-length guard. Consider basic validation.

6. **maxRetries and timeoutMs accepted but ignored** — MissionConfig declares these optional fields but submitMission never uses them. Either implement or remove to avoid misleading API surface.

## Low Priority

7. **generateMissionId uniqueness** — `Math.random().toString(36).slice(2,8)` gives ~2B combinations. Fine for single-instance but weak for distributed use. Document limitation.

8. **Docs (3 markdown files)** — Well-structured, consistent branding. No secrets found. Minor: credit costs in onboarding doc (1/3/5) differ from SDK constants (1/3/10/25). Align pricing tables.

## Security: PASS
- No secrets, no injection vectors, no user input rendered unsanitized
- No network calls in SDK (pure logic) — minimal attack surface

## Positive
- Clean TypeScript, zero `any` types
- 40 tests with good coverage of constructor, classification, submission, health, circuit breaker
- tsup config correct (ESM + CJS + DTS)
- Docs are professional and sales-ready

## Unresolved Questions
- Are the `./raas/*`, `./orchestration/*` etc. export paths intended for internal monorepo use only? If so, mark package `"private": true` or gate those exports.
