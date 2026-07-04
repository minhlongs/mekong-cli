# OKR Execution: Agentic Workflow for Q3 2026

> This document defines how OKRs are executed using Mekong CLI agents. Every KR below is
> owned by a specific agent pipeline, not by a person. The system executes, reports, and
> escalates autonomously.

---

## Q3 2026 OKR Framework

### Execution Model

Each KR follows a three-stage lifecycle:

1. **Plan** — Agent reads current state, generates a task list, estimates effort.
2. **Execute** — Agent runs subtasks using Mekong CLI commands or direct file writes.
3. **Verify** — Agent checks output against acceptance criteria and reports status.

Escalation: If a KR fails verification twice, the agent writes a `reports/{kr-slug}-escalation.md`
and pauses. A human reviews the escalation report and unblocks the agent.

---

### Objective 1: First Paying Customers

**Owner:** billing-agent pipeline (mekong + payment-integration skills)

- **KR1: Implement billing (Stripe or NOWPayments)** — Week 2
  - Plan: Audit current payment stubs, choose Stripe vs NOWPayments based on Vietnam/global mix.
  - Execute: Wire up webhook handler, subscription tier map, invoice generation.
  - Verify: `curl -X POST` to webhook endpoint returns 200, test card charge succeeds in sandbox.

- **KR2: Launch trial -> paid conversion flow** — Week 4
  - Plan: Map trial start -> day 7 reminder -> day 14 expiration -> conversion prompt.
  - Execute: Implement trial timer in DB, email trigger via Inngest, upsell page.
  - Verify: Create test user with trial flag, advance clock, confirm prompt renders.

- **KR3: Get 10 paying customers** — End of Q3
  - Plan: No agent action — this is a market result. Agent monitors Stripe dashboard daily.
  - Execute: Auto-post to #sales channel when count hits 5, 8, 10.
  - Verify: Agent reads Stripe API subscription count and compares against target.

---

### Objective 2: Content Engine Running

**Owner:** content-agent pipeline (content-blog + marketing-campaign + copywriting skills)

- **KR1: 12 blog posts published**
  - Plan: Generate content calendar from 22 department topics, assign 3 posts/week.
  - Execute: Each post goes through outline -> draft -> seo-meta -> publish flow.
  - Verify: Agent checks blog CMS for published count every Monday.

- **KR2: Twitter following to 1,000**
  - Plan: Research ICP hashtags, schedule 3 posts/day, engage with 10 accounts/day.
  - Execute: Use agent-browser to post via Twitter web UI (no API key needed).
  - Verify: Agent checks follower count weekly, logs growth rate.

- **KR3: Indie Hackers launch post**
  - Plan: Draft "How we built an AI factory for Mekong businesses" narrative.
  - Execute: Post to Indie Hackers with screenshots, tag relevant products.
  - Verify: Agent monitors upvotes and comments for 7 days, reports engagement.

---

### Objective 3: Product Stability

**Owner:** qa-agent pipeline (security-scan + test + sre-morning-check skills)

- **KR1: Zero critical bugs**
  - Plan: Run full test suite every deploy, tag regressions as P0.
  - Execute: Pre-commit hooks block merges with failing critical-path tests.
  - Verify: Agent runs `npm run test:e2e` on staging, compares pass rate to baseline.

- **KR2: Install script works for 100% of users**
  - Plan: Test on macOS (zsh + bash), Linux (Ubuntu, Debian), Windows (Git Bash).
  - Execute: Spin up clean VM per platform via script, run `curl ... | bash`, capture exit code.
  - Verify: Agent logs pass/fail per platform to `reports/install-matrix.md`.

- **KR3: Documentation complete for all 22 departments**
  - Plan: Audit `plans/company-blueprint/` for missing department docs.
  - Execute: Fill gaps using template from `01-overview.md`, cross-link from `README.md`.
  - Verify: Agent runs `grep -r "^# " plans/company-blueprint/*.md | wc -l` and checks count.

---

## Weekly Agent Rhythm

| Day | Agent | Action |
|-----|-------|--------|
| Monday | billing-agent | Reconcile subscriptions, generate MRR report |
| Tuesday | content-agent | Publish 3 blog posts, schedule tweets |
| Wednesday | qa-agent | Run full test suite, generate stability report |
| Thursday | billing-agent | Check trial expirations, send conversion nudges |
| Friday | content-agent | Engagement review, adjust content calendar |
| Saturday | all | Auto-generated weekly OKR status report |

Each agent writes its output to `reports/` with a timestamp prefix so the full history is
auditable. If an agent fails to complete its daily action, it retries once after 30 minutes,
then files an escalation.

---

## Files

| Artifact | Path |
|----------|------|
| This document | `plans/company-blueprint/21-okr-execution.md` |
| Weekly status reports | `plans/reports/okr-weekly-*.md` |
| Escalation reports | `plans/reports/okr-escalation-*.md` |
| Install matrix | `plans/reports/install-matrix.md` |

---

*Last updated: 2026-07-04*
