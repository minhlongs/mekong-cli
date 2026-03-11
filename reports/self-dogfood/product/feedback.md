# User Feedback Framework — Mekong CLI Beta

**Date:** March 2026 | **Stage:** Beta (pre-public launch)
**Current user count:** <50 (closed beta) | **Target:** Framework ready before Product Hunt launch

---

## Feedback Philosophy

At beta stage, qualitative feedback is 10x more valuable than quantitative. One user explaining exactly why `mekong cook` confused them is worth more than 100 NPS scores. Collect both, but weight qualitative heavily in product decisions.

**Golden rule:** Every piece of feedback must end with a product decision. "Interesting feedback" that sits in a document and changes nothing is a waste of everyone's time.

---

## Collection Methods

### Method 1: CLI Feedback Hook (Primary — highest volume)

After every task completes, Mekong displays a lightweight prompt:

```
[Mekong] Task complete. MCU used: 3. Time: 47s.
Was this helpful? [y/n/s to skip]
```

- `y` → logs positive signal, no follow-up
- `n` → prompts: "What went wrong? (1 line, or press Enter to skip)"
- Text response stored to `.mekong/feedback.log` locally + synced to API if user opted in
- `s` → skip, no log

**Why CLI-native feedback:** Users are already in the terminal. A web survey requires context switch. One keypress → immediate capture.

**Data collected per feedback event:**
```json
{
  "command": "cook",
  "task_summary": "implement user auth with JWT",
  "mcu_used": 3,
  "duration_seconds": 47,
  "helpful": false,
  "comment": "output was generic, didn't use my existing auth patterns",
  "timestamp": "2026-03-11T09:34:12Z",
  "cli_version": "5.0.1",
  "llm_model": "anthropic/claude-haiku",
  "account_tier": "starter"
}
```

**Opt-in:** Feedback sync to API is opt-in, announced in onboarding. Local log always written.

---

### Method 2: Beta Slack Channel (Qualitative — highest signal)

For closed beta: invite all beta users to `#mekong-beta` Slack workspace.

**Channel structure:**
- `#general` — announcements, roadmap previews
- `#feedback` — structured feedback posts (template below)
- `#bugs` — bug reports with reproduction steps
- `#wins` — "Mekong just saved me X hours" posts (social proof pipeline)
- `#recipes` — discussion about DAG workflow recipes

**Weekly prompt (posted every Monday):**
```
Weekly feedback prompt:
This week, what's the ONE thing that would make Mekong more useful for you?
(Be specific — "faster" is not actionable, "cook command should preserve existing file structure" is)
```

**Response rate target:** 30% of beta users respond per week. Below 20% means the channel is not valuable to them — investigate why.

---

### Method 3: Structured Interview (High-signal — monthly)

One 30-minute interview per month with 3–5 users. Selected by:
- High MCU usage (power users — they have the most to say)
- Users who gave negative CLI feedback (understand failure modes)
- Users who churned from paid (if applicable — understand churn drivers)

**Interview guide (30 min):**

*Opening (5 min)*
- "Walk me through how you used Mekong this week."
- "What were you trying to accomplish?"

*Critical incident (15 min)*
- "Tell me about a time Mekong did exactly what you needed."
- "Tell me about a time it frustrated you. What happened?"
- "What did you do instead?"

*Feature validation (5 min)*
- Show one upcoming feature — "Would this have helped with [their frustration]?"
- "What would make this better?"

*Closing (5 min)*
- "If Mekong disappeared tomorrow, what would you miss most?"
- "What's the one thing that would make you refer it to a colleague?"

---

### Method 4: GitHub Issues (Technical feedback)

Bug reports and feature requests via GitHub Issues with templates:

**Bug report template:**
```markdown
**Command:** mekong [command]
**Expected:** What should have happened
**Actual:** What happened
**Steps to reproduce:**
1.
2.
**CLI version:** (mekong --version)
**LLM provider:** (OpenRouter / Ollama / other)
**Relevant output:** (paste terminal output)
```

**Feature request template:**
```markdown
**I want to:** (one sentence description)
**So that:** (the outcome, not the feature)
**Current workaround:** (what do you do today?)
**Priority for you:** [nice-to-have / would-pay-more / blocking my usage]
```

Label taxonomy: `bug`, `enhancement`, `recipe-request`, `docs`, `performance`, `p0`, `p1`, `p2`

---

### Method 5: NPS Survey (Quantitative — monthly)

Triggered 14 days after first paid command (not on signup — on first real value delivery).

**Survey format:**
```
How likely are you to recommend Mekong CLI to a developer friend?
[0 — 1 — 2 — 3 — 4 — 5 — 6 — 7 — 8 — 9 — 10]

(If 0–6): What's the main reason for your score?
(If 9–10): What do you love most about Mekong?
```

Sent via email. Target response rate: 25%+. Below 15% → survey timing or channel wrong.

---

## Feedback Categories

All feedback — regardless of source — gets categorized into one of these buckets before entering the prioritization process:

| Category | Description | Example |
|----------|-------------|---------|
| **Broken** | Feature doesn't work as documented | "cook command exits with error on Windows" |
| **Confusing** | Works but users don't understand how | "I don't know what MCU means or how many I need" |
| **Slow** | Works and understood but too slow | "Plan command takes 90s — I give up and use ChatGPT" |
| **Missing** | Feature users expect that doesn't exist | "No way to cancel a running command" |
| **Wrong output** | Runs but produces bad results | "Cook outputs Python 2 code even when I specify Python 3" |
| **Pricing** | Feedback about cost/value | "200 MCU runs out too fast" |
| **Documentation** | Unclear or missing docs | "No example for how to use --model flag" |
| **Praise** | Positive signal | "Annual planning recipe saved me 4 hours" |

---

## Prioritization Matrix

Every categorized feedback item gets scored:

**Impact score (1–5):**
- 5: Affects every user, every session
- 4: Affects most users, frequently
- 3: Affects some users, occasionally
- 2: Edge case, rare
- 1: Single user, unique setup

**Effort score (1–5):**
- 1: Fix in <2 hours
- 2: Fix in <1 day
- 3: Fix in <1 week
- 4: Fix in <2 weeks
- 5: Fix in >2 weeks

**Priority formula: Impact ÷ Effort = Score**

| Score | Action |
|-------|--------|
| ≥ 3.0 | P0 — fix this sprint |
| 2.0–2.9 | P1 — fix next sprint |
| 1.0–1.9 | P2 — backlog, review quarterly |
| < 1.0 | Defer — not worth the effort yet |

**Example:**
- "Cook command crashes on macOS Sonoma" → Impact: 5, Effort: 2 → Score: 2.5 → P1
- "Add syntax highlighting to recipe editor" → Impact: 2, Effort: 4 → Score: 0.5 → Defer
- "MCU explanation missing in onboarding" → Impact: 4, Effort: 1 → Score: 4.0 → P0

---

## NPS Tracking Plan

### Baseline (first 50 users)
- Run NPS monthly, report in product standup
- Track by tier: Starter, Pro, Enterprise — they have different expectations
- Track by use case: code-focused users vs. business-layer users

### NPS Targets

| Milestone | NPS target | Action if below target |
|-----------|-----------|----------------------|
| Beta (first 50 users) | >30 | Investigate top detractor themes |
| Launch (first 200 users) | >40 | If still low, delay marketing spend |
| 500 users | >50 | Standard for "great" developer tool |
| 1,000 users | >55 | Referral program viable at this score |

**Reference NPS scores:** GitHub: 61, Vercel: ~55, Linear: ~68, Slack: ~35

### Detractor Response Protocol

Any NPS score of 0–6 gets a personal email from the founder within 48 hours:

```
Subject: Your feedback on Mekong — can I ask a quick follow-up?

Hi [name],

Thanks for taking the time to rate Mekong. A score of [N] tells me we're not
delivering the value you need yet.

Would you be willing to share what specifically isn't working? Even one sentence
would help — I read every response personally.

[Founder name]
```

Goal: convert detractors to neutral through response quality, not through fixing everything. People who feel heard forgive product gaps more readily.

---

## Feedback Review Cadence

| Review | Frequency | Participants | Output |
|--------|-----------|-------------|--------|
| CLI feedback log review | Weekly | Product | Top 3 friction points → added to backlog |
| Slack channel review | Weekly | Product | Themes summarized, flagged items tagged |
| NPS analysis | Monthly | Product + founder | Report with trend + top themes |
| User interviews | Monthly | Product | Interview summary + 3 action items |
| GitHub issues triage | Weekly | Engineering | Labels applied, P0 bugs escalated |
| Feedback → roadmap mapping | Quarterly | All | Confirm roadmap reflects user reality |

---

## Feedback Closing the Loop

When feedback leads to a shipped fix, tell the user:

**For GitHub issues:**
```
Fixed in v5.0.2 — released today. Thanks for reporting this!
The [specific fix] should resolve the issue you described.
If it doesn't, reopen this issue.
```

**For Slack feedback:**
```
@user — based on your feedback about [X], we shipped [fix] in v5.0.2.
Would love to know if this resolves the issue.
```

**For NPS detractors who responded:**
```
Update on your feedback: we shipped [fix] that addresses [specific issue].
Would you be willing to re-rate after trying the new version?
```

Closing the loop is rare in early-stage products. It builds disproportionate loyalty.
