---
name: idea
description: >-
  Generate a full company blueprint from a business idea. Delegates to the `mk idea` CLI, which writes real files to disk, then reports what landed.
---

# /idea — Company Blueprint Generator

**Never generate blueprint content inline.** The CLI writes it. Your job is to run the command, read what it produced, and report it.

## Run it

```bash
mk idea "<the user's business idea, 1-3 sentences>" -o plans/company-blueprint
```

Add `--json` for machine-readable output, `--dry-run` to preview without writing, and `--deep` only when the user explicitly asks for the autonomous autopilot pass (it spends model budget).

## What the command writes

`plans/company-blueprint/` receives `company.json`, `00-framework.md`, and `mvp-scope.md`. `00-framework.md` embeds the **live** open-core readiness evidence (verdict, public-repo safety, paywall flag, contract digest) — quote that evidence rather than asserting readiness yourself.

## After it runs

1. Read `plans/company-blueprint/company.json` and `00-framework.md` from disk.
2. Summarise the archetype, stage, MVP scope, and the readiness evidence in three or four lines.
3. Report the exact file paths so the user can open them.
4. If `--deep` was used, report the `deep_run` section: run id, ok/reason, and the audit-log path.

## Reading the result (context for interpretation)

| Lens | What to look for |
|------|------------------|
| Business | Strategy, model, market, product, finance, operations |
| Agentic | Which agents/departments are automated, and their KPIs |
| Governance | Controls, legal, risk, audit, IPO readiness |

Stage is detected by the command (`zero`, `pmf`, `scale`, `ipo`) — read it from the output rather than guessing.

## Boundaries

- Do not invent sections the command did not write.
- Do not claim the repo is monetization-ready or public-push-safe unless the embedded evidence says so.
- When the report shows a gap, say so plainly; a green pipeline panel is not evidence.
