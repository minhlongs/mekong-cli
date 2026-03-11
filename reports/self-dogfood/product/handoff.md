# Product-to-Engineering Handoff Template

**Purpose:** Standardize how Product hands off features to Engineering in Mekong CLI development
**Context:** Small team (1–5 people) — handoffs are often the same person, but the discipline of writing it forces clarity
**When to use:** Any feature >1 day of engineering effort; all P0 bugs; all new commands or recipes

---

## Handoff Document Structure

Every handoff lives in `plans/[date]-[feature-slug]/` as `plan.md` with linked phase files.

---

## Template: Product Requirements Document (PRD)

```markdown
# PRD: [Feature Name]

**Author:** [Product]
**Engineering owner:** [Name or TBD]
**Date:** [YYYY-MM-DD]
**Target version:** v[X.Y.Z]
**Priority:** P0 / P1 / P2
**Status:** Draft → Review → Approved → In Progress → Done

---

## Problem Statement
[1–3 sentences: what user pain does this solve? Why now?]

## Proposed Solution
[1–2 sentences: what are we building?]
Not: "A better UX." Yes: "A `mekong cancel` command that sends SIGTERM to the running PEV process."

## Success Criteria
- [ ] [Specific, testable outcome 1]
- [ ] [Specific, testable outcome 2]
- [ ] [Specific, testable outcome 3]

## Out of Scope
- [Explicit list of what this PRD does NOT include]
- [Reason for each exclusion]

## User Stories
- As a [persona], I want to [action] so that [outcome].
- As a [persona], I want to [action] so that [outcome].

## Acceptance Criteria
[See dedicated section below]

## Design Specs
[Link to Figma / ASCII wireframe / description]

## Technical Notes
[Optional: known constraints, architectural decisions product has already made]

## Open Questions
[Questions product needs engineering to answer before starting]
```

---

## Acceptance Criteria Standards

Acceptance criteria must be testable by a QA engineer who has never seen the feature before. If it requires product context to evaluate, rewrite it.

### Format: Given / When / Then

```
Given [initial state]
When [user action or system event]
Then [observable outcome]
```

### Example: `mekong cancel` command AC

```
Given a `mekong cook` command is running
When the user presses Ctrl+C or runs `mekong cancel` in a second terminal
Then the running PEV process terminates within 2 seconds
And the MCU deduction for the incomplete task is 0
And the terminal displays: "Task cancelled. 0 MCU charged."
And the partial output files (if any) are cleaned up from ./plans/

Given no command is currently running
When the user runs `mekong cancel`
Then the terminal displays: "No active task to cancel."
And exit code is 0 (not an error)

Given the PEV Verify step has already completed
When the user runs `mekong cancel`
Then the terminal displays: "Task already complete — nothing to cancel."
And the MCU charge is not reversed (task delivered successfully)
```

### Acceptance Criteria Anti-Patterns

**Too vague:**
- "The command should work correctly" → Rewrite: "The command should return exit code 0 and output [specific text]"
- "Performance should be good" → Rewrite: "Response latency should be <200ms at P95"

**Untestable:**
- "Users should feel confident" → This is a design goal, not an AC
- "The output should be high quality" → Define quality: "Output should contain all 5 required sections per the template"

**Missing edge cases:**
Every AC set must include at least one negative path (what happens when it fails) and one empty/null state.

---

## Design Specs Format

### For CLI commands (no UI)

Document the exact terminal interaction:

```
## Command: mekong balance

Usage: mekong balance [--json]

Output (default):
  Mekong CLI — Account Status
  ───────────────────────────
  Tier:    Pro
  Balance: 847 MCU
  Resets:  April 1, 2026

Output (--json flag):
  {
    "tier": "pro",
    "balance": 847,
    "reset_date": "2026-04-01",
    "account_email": "user@example.com"
  }

Error state (invalid API key):
  Error: Invalid API key. Run `mekong auth --key [your-key]` to authenticate.
  Exit code: 1

Error state (network failure):
  Error: Could not connect to Mekong API. Check your internet connection.
  Exit code: 1
```

### For web UI features

Provide:
1. **Wireframe** — ASCII is fine for internal handoffs

```
┌─────────────────────────────────────────────┐
│  agencyos.network/dashboard                 │
├─────────────────────────────────────────────┤
│  Balance: 847 MCU  [Top Up]  Tier: Pro      │
├─────────────────────────────────────────────┤
│  Recent Missions                            │
│  ─────────────────────────────────────────  │
│  [✓] cook "implement auth"    3 MCU  14:32  │
│  [✓] plan "sprint week 12"    2 MCU  11:15  │
│  [✗] deploy (failed)          0 MCU  09:44  │
└─────────────────────────────────────────────┘
```

2. **States to implement** — Empty state, loading state, error state, success state
3. **Interactions** — What happens on click, hover, keyboard navigation
4. **Responsive breakpoints** — if applicable (mobile: 375px, tablet: 768px, desktop: 1280px)

---

## QA Checklist

Engineering fills this out before marking a PR "ready for review":

### Functional
- [ ] All acceptance criteria pass manually
- [ ] Negative paths tested (invalid input, network failure, empty state)
- [ ] Edge cases from AC document tested
- [ ] Works with all 3 LLM provider configs (OpenRouter, Ollama, mock/test)

### Code Quality
- [ ] No `# type: ignore` or `# noqa` comments added without explanation
- [ ] No `TODO` or `FIXME` comments in the diff
- [ ] Function/class docstrings added for new public APIs
- [ ] No hardcoded API keys, secrets, or environment-specific values

### Security
- [ ] New API endpoints require authentication (check `src/api/middleware.py`)
- [ ] User input sanitized before passing to shell commands
- [ ] No sensitive data logged (API keys, user content, PII)
- [ ] Webhook signatures validated before processing

### Performance
- [ ] New CLI commands respond in <3s for simple operations
- [ ] New API endpoints respond in <500ms at P95 (no blocking LLM calls in API layer)
- [ ] No N+1 database queries introduced

### Tests
- [ ] Unit tests written for new functions (coverage ≥ 80% for new code)
- [ ] Integration test covers the primary AC happy path
- [ ] `python3 -m pytest tests/` passes locally before PR opens
- [ ] CI green before requesting review

### Documentation
- [ ] `mekong [command] --help` output is accurate and complete
- [ ] If new command: added to `README.md` command table
- [ ] If new recipe: added to recipe catalog
- [ ] CHANGELOG.md entry added under `[Unreleased]`

---

## Handoff Anti-Patterns (what we've seen go wrong)

### "The context dump PRD"
PRD includes 5 pages of background research and 1 paragraph of actual requirements. Fix: invert the ratio. Lead with requirements; background is an appendix.

### "The implicit acceptance criteria"
AC says "works correctly" and engineer and product discover during review they had different mental models. Fix: write Given/When/Then for every story before engineering starts.

### "The moving spec"
Product changes requirements after engineering has started. Fix: PRD must be "Approved" before engineering starts. Changes after Approved require a new version with changelog.

### "The missing edge cases"
AC covers only the happy path. Engineering ships, QA finds 5 edge cases in review. Fix: Product owns edge case discovery. Engineers should not be the first to think of "what if the network is down?"

### "The verbal handoff"
"I told them what to build in Slack." No written spec exists. Six weeks later, nobody remembers the decisions. Fix: every feature >1 day gets a written PRD. Slack is for questions, not specs.

---

## Example Handoff: `mekong balance` Command

**Plan file:** `plans/260311-1607-mekong-balance-command/plan.md`

### PRD Summary
- **Problem:** Users don't know how many MCU credits they have left without calling the API manually
- **Solution:** `mekong balance` command that shows current balance, tier, and reset date
- **Priority:** P0 (required before public launch — users need to know their balance)
- **Engineering effort:** S (0.5 days)

### Acceptance Criteria (abbreviated)
```
Given: valid API key configured
When: user runs `mekong balance`
Then: output shows tier, current balance (integer), reset date (YYYY-MM-DD)
And: exit code 0

Given: no API key configured
When: user runs `mekong balance`
Then: output shows "Run mekong auth --key [key] to authenticate."
And: exit code 1

Given: valid API key, --json flag
When: user runs `mekong balance --json`
Then: stdout is valid JSON with keys: tier, balance, reset_date, email
And: exit code 0
```

### Design spec
See "For CLI commands" example above — `mekong balance` section.

### QA owner: Engineering (self-QA for S-sized items)
### Review: Product spot-checks output format before merging

---

## Handoff Checklist (Product completes before handing off)

- [ ] Problem statement is 1–3 sentences (not a paragraph)
- [ ] "Out of scope" section explicitly listed (not implied)
- [ ] All acceptance criteria are in Given/When/Then format
- [ ] At least one negative path AC per user story
- [ ] Design spec provided (ASCII wireframe minimum for web; exact output for CLI)
- [ ] Open questions listed — not left as "TBD" without a resolution owner
- [ ] PRD reviewed by at least one engineer before "Approved" status
- [ ] Plan file created in `plans/` directory with correct naming format
