---
name: project-idea
description: Generate a company blueprint from a business idea by delegating to the `mk idea` CLI, then summarise the files it writes.
---

# /project-idea — Company Blueprint Generator

**Delegate, do not write.** The `mk idea` CLI writes the blueprint to disk. Your job is to run it, read what it produced, and report that.

## Your business idea

$ARGUMENTS

## Run the CLI

```bash
mk idea "<business idea, 1-3 sentences>" -o plans/company-blueprint
```

Flags:

- `--json` — machine-readable result instead of the Rich panel; use when you need to parse it.
- `--dry-run` — reports what would be written without touching disk.
- `--deep` — runs the deep Brainstorm Contract + 25-step Open-Core synthesis through the autonomous loop. **This spends model budget**, so only use it when the user explicitly asks for deep mode.

## What the command writes

`plans/company-blueprint/` receives three files:

- `company.json` — stage, archetype, next commands
- `00-framework.md` — business model blocks, MVP features, non-functional requirements, next commands, and (for open-core/SaaS ideas) the live readiness evidence: verdict, safe-for-public-github flag, paywall flag, contract digest
- `mvp-scope.md` — the MVP feature list

## After it runs

1. Read `company.json` and `00-framework.md` from disk — do not paraphrase them from stdout.
2. Summarise the archetype, stage, and MVP scope in three or four lines.
3. Report the exact absolute file paths so the user can open them.
4. Quote the readiness evidence as written; never assert monetization-readiness yourself.
5. If `--deep` was used, report the `deep_run` block: run id, ok/reason, and the audit-log path.

## Reading the output (interpretation context)

**Tri-layer** — apply to every section you read:

| Layer | Focus |
|-------|-------|
| Business | Strategy, model, market, product, finance, operations |
| Agentic | Which departments are automated, and their KPIs |
| Governance | Controls, legal, risk, audit, IPO readiness |

**Stage** — one of `zero`, `pmf`, `scale`, `ipo`. Read it from the output rather than guessing.

**Next commands** — `company.json` carries the handoff list. Use the 5-layer map below to route follow-up work to the right department:

| Layer | Commands | Agent |
|-------|----------|-------|
| Founder | /studio-strategy, /founder-raise, /studio-portfolio | CEO Agent |
| Business | /sales-pipeline-build, /marketing-campaign-run, /finance-budget-plan | Revenue Agent |
| Product | /product-sprint-plan, /pm-sprint, /design-sprint | Product Agent |
| Engineering | /cook, /dev-feature, /cto-architect, /release-ship | CTO Agent |
| Ops | /ops-health-sweep, /sre-morning-check, /analyst-report | Ops Agent |

## Boundaries

- Do not invent sections the command did not write.
- Do not claim the repo is public-push-safe or paywall-active unless the embedded evidence says so.
- When the evidence shows a gap, say so plainly; a green pipeline panel is not evidence.
