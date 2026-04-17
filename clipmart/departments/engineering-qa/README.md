# QA Engineering Department as a Service

> Replace a QA team with AI agents that run automated test suites, performance benchmarks, and accessibility audits on every release.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| QA Engineer ($130k) | $130,000/yr | $49/mo floor |
| Playwright + k6 + tools | $5,000/yr | Included |
| **Total replaced** | **$135,000/yr** | **~$1,800/yr** |

## What This Department Does

1. **E2E Testing** — Full user journey tests with Playwright across browsers
2. **Regression Suites** — Automated regression on every PR
3. **Performance Testing** — Load testing with k6, p95/p99 benchmarks
4. **Accessibility Audits** — WCAG 2.1 AA compliance checks
5. **Chaos Engineering** — Fault injection, failure mode validation

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| E2E test suite run | $5 |
| Regression suite | $8 |
| Performance benchmark report | $12 |
| Accessibility audit | $15 |
| Chaos experiment | $20 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong qa-e2e           # E2E test run
mekong qa-regression    # Regression suite
mekong qa-perf          # Performance benchmarks
mekong qa-accessibility # Accessibility audit
mekong qa-chaos         # Chaos engineering
mekong qa-plan          # QA plan generation
```

## Install

```bash
mekong install dept-engineering-qa
```

## Configuration

```bash
# .mekong/.env.dept-engineering-qa
DEPT_QA_TARGET_URL=https://staging.yourapp.com
DEPT_QA_BROWSERS=chromium,firefox,webkit
DEPT_QA_PERF_VUS=100  # virtual users for load test
DEPT_QA_PERF_DURATION=30s
DEPT_QA_WCAG_LEVEL=AA
DEPT_QA_CI_GATE=true  # fail CI on test failures
```
