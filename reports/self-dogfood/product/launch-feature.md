# Feature Launch Plan — DAG Workflow Recipes (85 Recipes)

**Feature:** DAG Workflow Recipes | **Version:** v5.0 | **Launch target:** April 2026
**Owner:** Product | **Status:** Pre-launch planning

---

## What We're Launching

85 pre-built DAG (Directed Acyclic Graph) workflow recipes that give Mekong CLI users structured, multi-step playbooks for complete business operations. Not single commands — full orchestrated workflows.

**Examples of what's included:**
- `mekong /annual` → 7-step annual planning DAG: SWOT → OKR → Budget → Roadmap → Team plan → Board deck → Communication plan
- `mekong /sales` → 5-step sales playbook DAG: ICP definition → Outreach sequences → CRM setup → Pipeline tracking → Forecast model
- `mekong /launch-product` → 9-step GTM DAG: Market research → Positioning → Landing page → Waitlist → Beta → Pricing → Launch → Retro

Each recipe chains commands with dependency resolution: step N only runs after step N-1 verifies successfully.

---

## Why This Launch Matters

Single commands (`mekong cook`, `mekong plan`) solve tactical problems. DAG recipes solve **strategic** problems — the kind that require 5–10 connected steps to complete properly.

This is the feature that moves Mekong from "fancy CLI tool" to "AI operating system for your business."

Competitive moat: Cursor doesn't have this. Devin doesn't have this. ChatGPT can't chain 9 steps with verification between each step. This is unique.

---

## Launch Checklist

### T-4 weeks (Documentation)
- [ ] Write recipe reference page for all 85 recipes (name, description, step count, layer)
- [ ] Create 5 deep-dive recipe guides (annual planning, product launch, sprint planning, security audit, fundraise)
- [ ] Record terminal screencast for top 3 recipes (2–3 min each)
- [ ] Write "How DAG recipes work" architecture explainer
- [ ] Update README with recipes section and quick-start example
- [ ] Add `mekong recipe list` command that prints all 85 with descriptions

### T-3 weeks (Distribution prep)
- [ ] Draft Product Hunt post: title, tagline, GIF demo, description
- [ ] Draft Hacker News Show HN post (conversational, founder voice)
- [ ] Identify 10 relevant subreddits: r/IndieHackers, r/SideProject, r/devops, r/startups
- [ ] List 5 YouTube channels that review developer tools (approach for review)
- [ ] Prepare X/Twitter thread: 85 recipes → one per use case, thread format
- [ ] Reach out to 5 indie hacker newsletters for feature mention

### T-2 weeks (Technical validation)
- [ ] Run all 85 recipes against CI in dry-run mode — confirm no broken DAG dependencies
- [ ] Test each recipe with Ollama (local) and OpenRouter (hosted) — verify both work
- [ ] Confirm `mekong recipe run [name]` works with 0 args (prompts for missing inputs)
- [ ] Load test: 10 concurrent recipe runs — confirm no race conditions in PEV orchestrator
- [ ] Confirm recipe output files land in correct directories
- [ ] Fix any recipes that produce empty or malformed output

### T-1 week (Content finalization)
- [ ] Record demo video: solo founder using `/annual` recipe, 5-minute walkthrough
- [ ] Create comparison table: "Before recipes (manual) vs. After recipes (Mekong)"
- [ ] Write 3 customer story templates (based on persona use cases from `persona.md`)
- [ ] Finalize Product Hunt assets: logo, screenshots, 60s video
- [ ] Brief any beta users for testimonials/upvotes on launch day

### Launch day
- [ ] Post to Product Hunt at 12:01 AM PST
- [ ] Post HN Show HN at 8 AM EST (peak HN hours)
- [ ] Post X thread with demo GIFs
- [ ] Respond to every Product Hunt comment within 2 hours
- [ ] Monitor #mekong-cli in any community channels
- [ ] Post to r/IndieHackers with genuine founder story angle

### T+1 week (Follow-up)
- [ ] Write "Week 1 learnings" post for Mekong blog
- [ ] Collect NPS scores from new recipe users
- [ ] Identify which recipes got most traction → double down on that category
- [ ] Fix any recipe bugs reported in first week
- [ ] Update recipe docs based on common confusion questions

---

## Demo Scenarios

### Demo 1: The Annual Planning Recipe (Primary demo)

**Audience:** Solo founders, agency owners
**Duration:** 3 minutes
**Script:**

```bash
# User has just started their terminal. No setup needed beyond env vars.
$ mekong recipe run annual

[Mekong] Running: annual-planning DAG (7 steps)
[Step 1/7] SWOT Analysis...
  → What industry are you in? "B2B SaaS"
  → What's your main product? "AI-powered CRM"
  → Generating SWOT... done (12s)
  → Output: ./plans/annual/swot.md

[Step 2/7] OKR Generation (uses SWOT output)...
  → Generating 3 company OKRs + 9 KRs... done (18s)
  → Output: ./plans/annual/okrs.md

[Steps 3-7 continue...]

[Mekong] Annual planning complete. 7 files generated in ./plans/annual/
[Mekong] Total time: 4m 32s | MCU used: 12
```

**The "wow moment":** A complete annual plan — the kind a strategy consultant charges $5,000 for — in 4 minutes for 12 MCU credits ($0.59 at Starter tier).

---

### Demo 2: Product Launch Recipe

**Audience:** Product managers, founders pre-launch
**Duration:** 4 minutes

```bash
$ mekong recipe run launch-product --name "Mekong CLI" --stage beta

[Step 1/9] Market Research → competitive landscape
[Step 2/9] Positioning → value prop + messaging
[Step 3/9] Landing Page → copy + structure outline
[Step 4/9] Waitlist Setup → email sequence draft
[Step 5/9] Beta Plan → criteria + onboarding flow
[Step 6/9] Pricing → tier analysis + recommendation
[Step 7/9] Launch Sequence → timeline + channels
[Step 8/9] PR Angles → 5 story angles for press
[Step 9/9] Retro Template → metrics to track
```

---

### Demo 3: Sprint Planning Recipe (for dev teams)

**Audience:** Dev team leads, CTOs
**Duration:** 2 minutes

```bash
$ mekong recipe run sprint --backlog ./backlog.md --team-size 3 --velocity 21

[Step 1/4] Backlog prioritization (MoSCoW)
[Step 2/4] Sprint capacity calculation (3 devs × 21pts = 63pts available)
[Step 3/4] Sprint selection — recommend 12 stories
[Step 4/4] Sprint doc generation — daily standup template, DoD checklist

Output: ./sprints/sprint-07/ (5 files)
Time: 45s | MCU: 4
```

---

## Documentation Requirements

### Must-have at launch
1. **Recipe catalog page** — sortable table: name, layer, step count, MCU cost estimate, description
2. **Getting started with recipes** — 5-minute guide, one complete example end-to-end
3. **Recipe reference** — one page per top-10 recipe with inputs, outputs, step breakdown
4. **Custom recipes guide** — how to write your own DAG recipe file
5. **FAQ** — "Can I run a recipe partially?", "What if a step fails?", "How do I retry?"

### Nice-to-have at launch
- Recipe gallery web page (agencyos.network/recipes)
- Community recipe submissions guidelines
- Recipe composability guide (nest one recipe inside another)

---

## Success Metrics

### Launch week (Day 1–7)
| Metric | Target | Stretch |
|--------|--------|---------|
| Product Hunt upvotes | 200 | 500 |
| HN Show HN points | 50 | 150 |
| New signups (attributed to recipe launch) | 50 | 200 |
| Recipe-related GitHub stars delta | +100 | +500 |
| Recipe runs in first week | 500 | 2,000 |

### Month 1 (Day 8–30)
| Metric | Target | Notes |
|--------|--------|-------|
| Users who run ≥1 recipe | 30% of new signups | Leading indicator of activation |
| Most-run recipe | Identify top 3 | Inform next recipe investments |
| Recipe-driven MCU spend | 40% of total MCU | Shows recipes drive revenue |
| Support tickets about recipes | <10% of total tickets | Signals good docs |
| NPS from recipe users vs. non-recipe | +15 NPS lift | Validates recipe value |

### Red flags (launch failure signals)
- Less than 5% of new signups try any recipe in first session
- Most-run recipe has a >20% failure rate
- Zero community recipe contributions in 30 days (no ecosystem pull)

---

## Risk Mitigations

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Recipe step fails silently | Medium | Verify step adds explicit error output + retry prompt |
| MCU cost per recipe feels high | Low-Medium | Show MCU cost estimate before running; add `--dry-run` flag |
| Users confused by DAG concept | Medium | Never use "DAG" in user-facing copy; call them "workflow recipes" |
| Competitor copies the recipes format | Low (short-term) | Ship recipe marketplace to build community moat before copy happens |
| 85 recipes is overwhelming | Medium | Surface "top 10" prominently; hide long tail behind `recipe list --all` |
