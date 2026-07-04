# GTM Experiments + Bullseye Framework

## Overview

This document defines the go-to-market experiment strategy for mekong-cli using the Bullseye Framework (from Gabriel Weinberg's "Traction"). The framework identifies the single channel most likely to drive growth, tests it rigorously, then expands outward.

### Key Principles

- Run experiments sequentially — Inner Ring first, then Middle, then Outer.
- Each experiment must have a clear target metric, budget, and timebox.
- Kill experiments that miss target by >50% within the timebox. No sunk-cost.
- Document learnings before moving to the next channel.
- All budgets are in USD. $0 channels are prioritised.

---

## Bullseye Target: Indie Hackers Community

### Inner Ring (test first)

These channels have the highest signal-to-noise ratio for a developer tool targeting indie founders and solo builders. Zero monetary cost; only time investment.

1. **Indie Hackers** — Launch post with narrative (build story + revenue numbers). Follow up with a case study 2 weeks post-launch.
2. **Hacker News** — Show HN post. Must have a working demo link and clear problem statement. Prepare for the comments section — respond within 1 hour.
3. **Twitter/X** — Build in public thread. Daily progress updates. Share metrics, screenshots, and learnings. Tag @IndieHackers and relevant accounts.

### Middle Ring (if inner works)

These channels require more preparation but offer compounding returns once Inner Ring validates the positioning.

4. **GitHub** — Open source the CLI core under MIT license. Encourage community contributions. Add CONTRIBUTING.md and issue templates.
5. **Product Hunt** — Coordinated launch with email list. Prepare maker comment, first 10 upvotes, and a landing page.
6. **YouTube** — Demo video series: "Build your SaaS backend in 5 minutes with mekong-cli". Screencast format with voiceover.

### Outer Ring (scale)

These channels require paid budget or ongoing content commitment. Only activate when Inner and Middle Rings show repeatable unit economics.

7. **Google Ads** — Search ads for ["CLI for SaaS" "backend generator" "AI CLI tool"]. Cap at $500/month. Track cost per signup.
8. **LinkedIn content** — Long-form posts about the solo-founder engineering workflow. Target 2 posts per week.
9. **Podcast appearances** — Pitch to Indie Bites, Software Social, and DevTools FM. Talk about building in public and CLI DX.

---

## Experiment Tracker

| # | Experiment | Channel | Budget | Timeline | Target Metric | Actual | Status |
|---|-----------|---------|--------|----------|--------------|-------|--------|
| 1 | Indie Hackers launch post | Indie Hackers | $0 | Week 1 | 100 signups | -- | Planned |
| 2 | Indie Hackers case study | Indie Hackers | $0 | Week 3 | 50 signups | -- | Planned |
| 3 | Show HN post | Hacker News | $0 | Week 2 | 500 GitHub stars | -- | Planned |
| 4 | Build in public thread | Twitter/X | $0 | Weekly | 50 signups per thread | -- | Planned |
| 5 | Twitter thread — feature deep dive | Twitter/X | $0 | Week 4 | 200 post likes | -- | Planned |
| 6 | Open source CLI core | GitHub | $0 | Week 3 | 10 contributors | -- | Planned |
| 7 | Product Hunt launch | Product Hunt | $0 | Week 5 | 300 upvotes | -- | Planned |
| 8 | Demo video — quickstart | YouTube | $0 | Week 4 | 1,000 views | -- | Planned |
| 9 | Demo video — advanced usage | YouTube | $0 | Week 6 | 500 views | -- | Planned |
| 10 | Google Ads search campaign | Google Ads | $500/mo | Week 8+ | $5 CPA | -- | Planned |
| 11 | LinkedIn thought leadership | LinkedIn | $0 | Week 6+ | 100 clicks/mo | -- | Planned |
| 12 | Podcast — Indie Bites | Podcast | $0 | Week 8 | 50 signups | -- | Planned |

### Scoring Rubric

Each experiment is scored after its timebox on three criteria:

- **Reach** (1-5): How many people saw it.
- **Conversion** (1-5): What fraction of reach took the target action.
- **Effort** (1-5): 1 = low effort, 5 = high effort. Inverted for scoring.

**Channel Score = Reach + Conversion + (6 - Effort)**

Max score = 15. Channels scoring >= 10 graduate to "active channel" status and receive recurring investment.

### Decision Gates

| Gate | Condition | Action |
|------|-----------|--------|
| GREEN | Score >= 10 | Double down: increase frequency or budget |
| YELLOW | Score 6-9 | Refine: change messaging, audience, or format |
| RED | Score < 6 | Kill: document learnings, move to next channel |

---

## Experiment Templates

### Template: Community Launch Post

```
Title: I built [product] for [audience] because [problem]

Hook (2 sentences): The problem every [audience] faces.
Body: How I discovered the problem, what I built, how it works.
Results: Key metrics (signups, revenue, usage).
Learnings: What surprised me.
Call to action: Try it here [link] — feedback welcome.
```

### Template: Show HN Post

```
Title: Show HN: [Product Name] — [one-line value prop]

First comment (pinned):
- What it does in one paragraph
- Link to live demo
- What makes it different from alternatives
- Tech stack (1 line)
- Honest ask: "What would you improve?"
```

### Template: Build in Public Thread

```
1/ I'm building [product] for [audience].
Here's what happened this week:

2/ Metric highlight: [X] signups, [Y] revenue, [Z] retention
3/ What went right: [specific win]
4/ What went wrong: [specific failure]
5/ Key lesson: [takeaway]
6/ Next week's focus: [goal]
```

---

## Notes

- Inner Ring experiments are runway-independent; they cost only time.
- Do not open Middle or Outer channels until at least one Inner Ring experiment scores GREEN.
- Revisit the Bullseye every 4 weeks. Audience targeting or positioning changes may shift the optimal channel.
- Track all results in the tracker above. If a channel is killed, append a `- Killed` reason to the Status column.
