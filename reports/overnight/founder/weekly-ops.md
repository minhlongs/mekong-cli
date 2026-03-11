# Founder Weekly Ops Template — Mekong CLI

**Date:** March 2026
**Covers:** founder-weekly, standup, schedule, win-check
**Run via:** `mekong founder-weekly` every Monday 8am

---

## Weekly Rhythm Overview

```
Mon  — Review metrics, plan week, clear blockers
Tue  — Deep work: product / engineering
Wed  — Community, content, outreach
Thu  — Deep work: product / engineering
Fri  — Wrap-up, wins log, prep next week
Sat  — Optional: async community engagement
Sun  — Rest / strategic thinking only
```

---

## Monday: Metrics Review & Week Planning (2 hours)

### Metrics Dashboard Pull

Run: `mekong kpi --week`

| Metric | This Week | Last Week | Delta | Target |
|--------|-----------|-----------|-------|--------|
| MRR | $X | $X | +/- $X | On track? |
| New trials | X | X | +/- X | — |
| Trial → paid conversions | X | X | +/- X | >2% |
| Churn (cancelled subs) | X | X | +/- X | <5%/mo |
| GitHub stars | X | X | +X | +50/wk |
| PyPI installs (7d) | X | X | +/- X | Growing |
| P1 bugs open | X | X | — | 0 |
| Top command used | `mekong X` | — | — | — |
| MCU consumed (total) | X | X | +/- X | — |

### Weekly Standup (self)

Answer 3 questions:

1. **What shipped last week?**
   - Features / commands added
   - Bug fixes merged
   - Content published
   - Customers onboarded

2. **What's the #1 priority this week?**
   - Single most important thing that moves the needle
   - If everything fails, this ONE thing gets done

3. **What's blocked?**
   - List blockers explicitly — don't let them hide
   - Assign unblock action + deadline

### Week Planning Template

```
WEEK OF [DATE]

#1 Priority: [ONE THING]

Mon: Metrics review, [task]
Tue: [Deep work — product/eng]
Wed: [Community/content/outreach]
Thu: [Deep work — product/eng]
Fri: [Wrap-up, wins log]

Experiments running:
- G[N]: [name] — checking [metric] by [date]

Customers to follow up:
- [name/email] — [context]

Content to publish:
- [title] → [platform] → [date]
```

---

## Tuesday / Thursday: Deep Work Blocks (6 hours each)

### Engineering Deep Work

Use Tôm Hùm daemon for parallel execution:
```bash
mekong cook "implement [feature]" --verbose
mekong fix "bug: [description]" --strict
mekong test --coverage
```

Focus areas rotate weekly:
- Week A: PEV engine improvements
- Week B: New commands / skills
- Week C: RaaS billing hardening (`src/raas/`)
- Week D: Documentation + onboarding

### Product Deep Work

- User interviews (2 per month minimum)
- `mekong founder-validate` — check PMF signals
- Command usage analytics review (`usage_analytics.py`)
- Feature backlog triage: RICE scoring

---

## Wednesday: Community, Content & Outreach (4 hours)

### Community Block (90 min)

- Reply to GitHub issues + discussions
- Review + merge community PRs (agent marketplace)
- Respond to Discord/Slack community messages
- Check Viblo.asia / TopDev mentions

### Content Block (90 min)

Weekly content calendar rotation:
- **Week 1:** Technical deep-dive blog post (Dev.to / Hashnode)
- **Week 2:** Twitter/X thread: "What `mekong [command]` does + example"
- **Week 3:** Vietnamese community post (Viblo + Facebook groups)
- **Week 4:** YouTube video or demo GIF for README

Content checklist:
- [ ] Draft written
- [ ] Code examples tested and working
- [ ] Published to primary platform
- [ ] Cross-posted (2nd + 3rd platforms)
- [ ] Reply to first 10 comments within 24h

### Outreach Block (60 min)

- 5 cold GitHub DMs to potential users (developers with relevant repos)
- 2 partnership emails (LLM providers, dev tool builders)
- 1 investor warm-up email (if in fundraise window)
- 3 replies to relevant HN/Reddit threads (non-promotional, genuinely helpful)

---

## Friday: Wrap-Up & Wins Log (90 min)

### Win Check

Every Friday, log wins — no matter how small:

```markdown
## Week of [DATE] — Wins

### Shipped
- [Feature/fix/command added]

### Numbers
- Stars gained: +X
- Trials started: X
- Paid conversions: X
- MRR change: +$X

### Community
- PRs merged: X
- Issues closed: X
- Positive feedback: "[quote]"

### Personal
- [Something learned]
- [Something to be proud of]

### Next week focus: [ONE THING]
```

### Monthly Retrospective (last Friday of month)

1. What experiments worked? Double down.
2. What experiments failed? Kill them.
3. What's the single highest-leverage thing I'm NOT doing?
4. Am I building what users actually want? (check support tickets + interviews)
5. Is the current trajectory leading to $10K MRR? If not, what changes?

---

## Monthly Founder Review (First Monday of Month, 3 hours)

### Financial Review
- [ ] P&L update (actuals vs. projection)
- [ ] MRR cohort analysis (which month's signups are churning?)
- [ ] Runway recalculation
- [ ] LTV:CAC update

### Product Review
- [ ] NPS or satisfaction survey sent?
- [ ] Top 5 feature requests from support tickets
- [ ] Command usage 80/20: which 20% of commands drive 80% of usage?
- [ ] Onboarding funnel drop-off analysis

### Strategic Review
- [ ] On track for annual OKRs?
- [ ] Any pivot signals? (users using Mekong for unexpected use cases?)
- [ ] Competitor moves: check Cursor, Aider, Claude Code changelogs
- [ ] One strategic decision to make this month

### Investor Update (post-raise)
- [ ] Draft and send monthly investor update
- [ ] Format: see fundraise-strategy.md investor update template

---

## `mekong founder-weekly` Auto-Checklist

When running the command, auto-pull:

- [ ] Metrics from Cloudflare D1 (billing data via `src/raas/`)
- [ ] GitHub stats: stars, open issues, merged PRs
- [ ] PyPI download stats (weekly)
- [ ] MRR delta (new subs - churned × price)
- [ ] Top 5 commands by MCU consumption this week
- [ ] P1 bugs surfaced (open GitHub issues labeled `P1`)
- [ ] Week plan template pre-filled with last week's context
- [ ] Win log entry prompted

---

## Solo Founder Sustainability Rules

Solo founder + AI agents is powerful but has limits. Protect the human:

| Rule | Detail |
|------|--------|
| No decisions after 9pm | Tired decisions are bad decisions |
| Delegate 80% to Tôm Hùm | If a task can be automated, automate it first |
| 2 user interviews/month minimum | Prevents building in a vacuum |
| Weekly win log non-negotiable | Motivation is fuel, log it |
| One founder day off/week | Sunday = no work, no Slack, no code |
| 3-week blocker rule | Same blocker for 3 weeks → change approach, don't grind |

---

## Schedule Template (Sample Week)

```
MON 8:00–10:00  Metrics review + week planning
MON 10:00–12:00 PEV engine: address P1 bugs

TUE 9:00–15:00  Deep work: [feature/command]
TUE 15:00–17:00 Code review + merge PRs

WED 9:00–10:30  Community: GitHub issues + Discord
WED 10:30–12:00 Content: draft blog post
WED 14:00–15:00 Outreach: 5 DMs + 2 partnership emails

THU 9:00–15:00  Deep work: [feature/command continued]
THU 15:00–17:00 mekong test --coverage + fix failures

FRI 9:00–10:30  Wrap-up: wins log + MRR update
FRI 10:30–11:30 Prep next week's #1 priority
FRI 14:00–15:00 Content: publish + distribute

SAT (optional)  Async community replies only
SUN             Off
```
