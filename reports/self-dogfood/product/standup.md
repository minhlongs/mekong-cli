# Daily Standup — Mekong CLI Development

**Format:** Async-first (post in #standup by 9 AM local) | **Sync optional:** Tuesdays 15 min
**Team size:** 1–5 people | **Cadence:** Every working day

---

## Template (copy-paste daily)

```
### Standup [DATE]

**Yesterday:**
-

**Today:**
-

**Blockers:**
-

**MCU health:** [balance] credits remaining | [N] missions ran yesterday
**CI status:** [green/red] | Last deploy: [timestamp]
```

---

## Sample Standup — March 11, 2026

### Standup 2026-03-11

**Yesterday:**
- Merged PR #312: `mekong /cook` now passes `--model` flag through to PEV executor
- Fixed bug where `verifier.py` would exit 0 even when shell command returned non-zero
- Wrote 3 recipe files: `sprint.yaml`, `annual.yaml`, `launch-product.yaml`
- Reviewed competitor analysis (Devin updated pricing to $500/mo confirmed)

**Today:**
- P0: Fix DAG dependency resolution bug — recipes with >5 steps sometimes run step 6 before step 5 verifies (issue #318)
- P0: Publish `mekong-cli==5.0.1` to PyPI — blocked on twine auth yesterday, now resolved
- P1: Write recipe catalog docs (target: 15 recipes documented today, 85 total needed)
- P2: Draft Enterprise tier proposal for review (see `proposal.md`)

**Blockers:**
- OpenRouter rate limits hitting during recipe CI tests — need to add exponential backoff in `llm_client.py` or mock LLM responses in test suite
- White-label API design decision still open: do we namespace by subdomain or API key prefix? Need decision before engineering starts

**MCU health:** 847 credits remaining (test account) | 23 missions ran yesterday (CI + manual testing)
**CI status:** RED — `test_pev_orchestrator.py::test_dag_step_order` failing since yesterday 6 PM
**Last deploy:** agencyos.network — 2026-03-10 14:32 UTC (staging only, not prod)

---

## Standup Categories Explained

### Yesterday
- What actually shipped or moved forward (not what you worked on — what got done)
- PRs merged, bugs fixed, decisions made, content written
- Be specific: "fixed verifier bug" not "worked on backend"

### Today
- Max 3–4 items. If you list 8 things, you're planning, not standing up
- Mark P0/P1/P2 priority — helps team understand what's critical
- Include estimated time if relevant: "P0 fix (2h estimated)"

### Blockers
- Anything that will prevent today's P0 from completing
- Tag the person/system that can unblock: "@engineer — need DB schema decision"
- If no blockers: write "None" (don't leave blank — blank reads as forgot)

### MCU Health (Mekong-specific)
- Track credit burn rate to catch runaway test suites
- Flag if burn rate is >2x normal (could indicate infinite loop in a recipe)
- Reference: production account vs. test account separately

### CI Status
- Green/Red + which test is failing if Red
- Never start a new PR if CI is Red — fix first
- Reference the commit or PR that broke it

---

## Weekly Rhythm

### Monday — Sprint kickoff standup
Add to template:
```
**Sprint goal this week:**
**Top 3 priorities:**
1.
2.
3.
```

### Friday — Retrospective micro-standup
Add to template:
```
**Shipped this week:**
**Carried over (why?):**
**One thing to do differently next week:**
```

### Tuesday sync (optional, 15 min)
- Only if there are cross-person blockers
- Agenda: unblock → decisions → nothing else
- Skip if standup thread shows no blockers

---

## Current Sprint Priorities (v5.0 → v5.1)

Tracking against `roadmap.md` milestones:

| Priority | Item | Owner | Status |
|----------|------|-------|--------|
| P0 | DAG recipe step-order bug fix | Engineering | In progress |
| P0 | PyPI v5.0.1 publish | Engineering | Today |
| P0 | Recipe catalog docs (85 recipes) | Product/Docs | 3/85 done |
| P1 | Enterprise tier proposal | Product | Today |
| P1 | LLM client rate-limit backoff | Engineering | This week |
| P1 | agencyos.network landing page update | Frontend | This week |
| P2 | White-label API design decision | All | Blocked — needs decision |
| P2 | VS Code extension v0.1 scaffold | Engineering | Next week |

---

## Standup Anti-Patterns (what not to do)

**"Working on recipes"** — Too vague. Which recipe? What step? What's the output?

**"Lots of stuff, will update later"** — Standup is not a status report you write at 5 PM. Post by 9 AM.

**"No blockers"** when there actually are — Blockers aren't weakness. Hiding them costs the team a day.

**Listing 8 priorities** — If everything is priority, nothing is. Pick 3.

**Skipping CI status** — One broken test that sits for 2 days is a compounding tax on every PR that follows.

---

## Mekong CLI Self-Dogfood Note

We run `mekong standup` to generate the standup template each morning. The command reads:
- `git log --since=yesterday` for yesterday's work
- `.mekong/tasks/` for today's active tasks
- CI status from GitHub Actions API

The output pre-fills the template. Engineers edit and post. The tool eats its own cooking.

```bash
$ mekong standup
[Mekong] Reading git log since 2026-03-10...
[Mekong] Found 4 commits, 2 PRs merged
[Mekong] Reading active tasks...
[Mekong] Checking CI status...
[Mekong] Standup draft ready:

### Standup 2026-03-11
**Yesterday:** [4 items from git log]
**Today:** [3 items from task list]
**Blockers:** [1 item flagged in tasks]
...
```
