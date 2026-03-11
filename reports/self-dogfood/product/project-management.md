# Project Management Setup — Mekong CLI

**Date:** March 2026 | **Author:** Product
**Tool:** GitHub Projects (free, integrated with Issues/PRs)
**Team size:** 1–5 contributors

---

## Philosophy

Mekong CLI is a product that automates business operations. We should run ourselves the way we tell customers to run their businesses. That means: clear sprint goals, daily standups (async), weekly retrospectives, milestone tracking, and no work that cannot be traced to a user outcome.

We use `mekong /sprint` to plan our own sprints. We eat our own cooking.

---

## Kanban Workflow

### Board: "Mekong CLI Development"
URL: `github.com/[org]/mekong-cli/projects/1`

### Columns

```
Inbox → Backlog → This Sprint → In Progress → Review → Done
```

**Inbox:** New issues, feature requests, bug reports land here. Triaged weekly.

**Backlog:** Prioritized, ready-to-pick items. Everything in Backlog has:
- Clear description
- Acceptance criteria or reproduction steps (bugs)
- T-shirt size label (S/M/L/XL)
- Priority label (p0/p1/p2)
- Layer label (founder/business/product/engineering/ops/infra/docs)

**This Sprint:** Items committed to the current 1-week sprint. Max 5 items per person.

**In Progress:** Actively being worked on. One item per person maximum (WIP limit = team size).

**Review:** PR open, waiting for review. Target: 24h turnaround on reviews.

**Done:** Merged to main. Closed automatically when linked PR merges.

---

## Labels

### Priority
- `p0` — Blocking: ship or user-facing broken experience
- `p1` — Important: should ship this sprint
- `p2` — Nice to have: next sprint or backlog
- `wont-fix` — Deliberate decision not to fix

### Type
- `bug` — Something broken
- `enhancement` — New feature or improvement
- `recipe` — New DAG workflow recipe
- `docs` — Documentation only
- `infra` — CI/CD, infrastructure, DevOps
- `security` — Security issues (use `p0` always)

### Layer (maps to Mekong's 5-layer architecture)
- `layer:founder` — Founder-layer commands
- `layer:business` — Business-layer commands
- `layer:product` — Product-layer commands
- `layer:engineering` — Engineering-layer commands
- `layer:ops` — Ops-layer commands
- `layer:core` — PEV engine, LLM router, API gateway

### Size
- `size:S` — 0.5–1 day
- `size:M` — 2–3 days
- `size:L` — 1–2 weeks
- `size:XL` — >2 weeks (break into smaller issues)

---

## Sprint Cadence

### Sprint length: 1 week (Mon–Fri)

Why 1 week vs. 2 weeks: At pre-product-market-fit stage, 2-week sprints create false certainty. A 1-week sprint forces prioritization and catches wrong assumptions faster.

### Sprint Rhythm

**Monday: Sprint Planning (30 min)**
- Review last sprint: what shipped, what carried over, why
- Set one sprint goal (1 sentence, e.g., "Ship DAG recipe CI validation")
- Pull items from Backlog into This Sprint
- Confirm capacity: any holidays, personal commitments this week?
- Run `mekong sprint --goal "..." --capacity 5d` to generate sprint plan

```bash
$ mekong sprint --goal "Ship recipe catalog docs (50 recipes)" --team-size 1 --velocity 5d

[Mekong] Sprint plan generated:
Sprint Goal: Ship recipe catalog docs (50 recipes)
Capacity: 5 engineer-days

Recommended stories (22 story points total):
  P0: Write recipe catalog template (0.5d)
  P0: Document top 20 recipes (2d)
  P1: Update README with recipes section (0.5d)
  P1: Record demo screencast for top 3 recipes (1d)
  P2: Add recipe search to agencyos.network (deferred — over capacity)

Output: ./sprints/sprint-12/plan.md
```

**Daily: Async standup (see `standup.md`)**
- Post by 9 AM local time
- Format: Yesterday / Today / Blockers / CI status

**Wednesday: Mid-sprint check (10 min)**
- Are we on track for sprint goal?
- Any blockers that haven't been unblocked?
- Scope cut if needed — better to ship 3 things done than 6 things half-done

**Friday: Sprint review + retrospective (30 min)**
- Demo everything that shipped (even to yourself — narrating what shipped clarifies thinking)
- Update milestone progress
- Retrospective: What worked? What didn't? One change for next sprint?
- Run `mekong retrospective --sprint 12` for structured retro template

---

## Release Process

### Versioning: Semantic versioning (MAJOR.MINOR.PATCH)
- `MAJOR`: Breaking changes (new PEV engine architecture, API contract changes)
- `MINOR`: New features (new commands, new recipes, new tiers)
- `PATCH`: Bug fixes, documentation, minor improvements

### Release cadence
- Patch releases: as needed (critical bugs get same-day patch)
- Minor releases: every 2–4 weeks (aligned with sprint milestones)
- Major releases: quarterly (v5.0 → v6.0 represents significant architectural or UX change)

### Release checklist

**Before tagging a release:**
- [ ] `python3 -m pytest tests/` passes — 100% green
- [ ] `mekong --version` returns correct version number
- [ ] CHANGELOG.md updated: move `[Unreleased]` → `[v5.X.Y] - YYYY-MM-DD`
- [ ] README updated if new commands or features added
- [ ] PyPI package version bumped in `pyproject.toml`
- [ ] Git tag created: `git tag v5.X.Y && git push origin v5.X.Y`

**Publishing to PyPI:**
```bash
python3 -m build
twine upload dist/*
# Verify: pip install mekong-cli==5.X.Y in clean virtualenv
```

**GitHub Release:**
- Draft release notes from CHANGELOG
- Attach `dist/` artifacts
- Mark as "Latest release"
- Post to `#announcements` in community Slack

**Post-release monitoring:**
- Watch PyPI download stats for 24h
- Monitor GitHub Issues for immediate bug reports
- Check CI on `main` branch — should stay green
- If critical bug found within 24h: ship hotfix as `v5.X.Y+1`

---

## Milestone Tracking

### Current Milestones

**Milestone 1: Public Launch Ready (Target: April 14, 2026)**
- [ ] PyPI package published and installable (`pip install mekong-cli`)
- [ ] agencyos.network landing page live with Polar.sh checkout
- [ ] 85 recipes CI-validated and documented
- [ ] `mekong auth` and `mekong balance` commands working end-to-end
- [ ] README 5-minute quickstart tested by 3 external people
- [ ] Product Hunt draft prepared
- [ ] QUICKSTART.md covers all 3 LLM provider paths (OpenRouter, Ollama, hosted)

**Milestone 2: First Revenue (Target: May 15, 2026)**
- [ ] 10 paying Starter customers
- [ ] 1 paying Pro customer
- [ ] 1 Enterprise conversation active
- [ ] Polar.sh webhook → credit provisioning working in production
- [ ] NPS survey deployed, first 20 responses collected
- [ ] Churn rate below 20% after 30 days

**Milestone 3: Product-Market Fit Signal (Target: July 1, 2026)**
- [ ] 100 paying customers
- [ ] MRR > $5,000
- [ ] NPS > 40
- [ ] Organic signups > paid acquisition (word-of-mouth working)
- [ ] 3 Enterprise customers or LOIs
- [ ] Plugin marketplace seeded (10 community plugins)
- [ ] Top 3 use cases clearly identified from usage data

### Milestone Progress View (GitHub Projects)

Use GitHub Projects "Milestones" view to track completion:
- Each milestone is a GitHub Milestone with a due date
- Issues tagged to milestones auto-track progress
- Milestone burndown visible on project board

---

## GitHub Projects Setup Instructions

### Initial Setup

```bash
# Install GitHub CLI if not present
brew install gh

# Create project board
gh project create --org [org] --title "Mekong CLI Development" --format board

# Create labels (run once)
gh label create "p0" --color "d73a4a" --description "Blocking - must fix now"
gh label create "p1" --color "e4e669" --description "Important - this sprint"
gh label create "p2" --color "0075ca" --description "Backlog - next sprint"
gh label create "size:S" --color "c5def5" --description "0.5-1 day"
gh label create "size:M" --color "c5def5" --description "2-3 days"
gh label create "size:L" --color "c5def5" --description "1-2 weeks"
gh label create "size:XL" --color "c5def5" --description ">2 weeks — break it down"
gh label create "layer:core" --color "e99695" --description "PEV engine, LLM router, API"
gh label create "layer:engineering" --color "e99695" --description "Engineering layer commands"
gh label create "recipe" --color "d4edda" --description "New DAG workflow recipe"
gh label create "bug" --color "d73a4a" --description "Something is broken"
gh label create "enhancement" --color "a2eeef" --description "New feature or improvement"
```

### Issue Templates

Create `.github/ISSUE_TEMPLATE/` with:
- `bug-report.yml` — structured bug form
- `feature-request.yml` — structured feature request
- `recipe-request.yml` — request for new DAG recipe

### Automation Rules (GitHub Actions)

```yaml
# .github/workflows/project-automation.yml
name: Project Automation
on:
  issues:
    types: [opened, labeled]
  pull_request:
    types: [opened, closed]

jobs:
  add-to-project:
    runs-on: ubuntu-latest
    steps:
      - name: Add new issues to Inbox
        # Automatically moves new issues to Inbox column
      - name: Move merged PRs to Done
        # Automatically closes linked issues when PR merges
```

---

## Working with Mekong to Manage Mekong

We dogfood our own commands for project management:

```bash
# Generate this week's sprint plan
mekong sprint --goal "Ship recipe catalog" --capacity 5d

# Daily standup
mekong standup

# Weekly retrospective
mekong retrospective --sprint 12 --what-shipped "recipe docs, balance command" --what-didnt "VS Code extension delayed"

# Prioritize backlog
mekong brainstorm "which features to prioritize for Product Hunt launch"

# Write release notes from git log
mekong docs --type release-notes --from v5.0.0 --to HEAD
```

Every time we use a Mekong command to run our own development process, we're validating product quality and discovering UX issues firsthand. This is the self-dogfood principle in action.

---

## Escalation Paths

| Situation | Action |
|-----------|--------|
| P0 bug in production | Fix immediately, skip sprint process, patch release same day |
| Sprint goal at risk by Wednesday | Scope cut — drop P2 items, protect sprint goal |
| Two consecutive missed sprint goals | Retrospective focused on sprint sizing, reduce scope |
| Contributor blocked >1 day | Async message with blocker details, founder unblocks or reassigns |
| Security vulnerability reported | P0 immediately, private patch, disclose after fix |
| Major feature request from Enterprise customer | Evaluate against roadmap in next sprint planning, communicate timeline |
