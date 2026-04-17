---
description: "4-phase AI-SDLC scaffold — Spec → Design → Code → Deploy. Run a feature through the full agentic lifecycle. ~30-90min total depending on feature scope."
argument-hint: [feature-slug, e.g. auth-mfa]
allowed-tools: Read, Write, Bash, Task
---

# /sdlc — Agentic SDLC Orchestrator

**Super command** — walks a feature through 4 agent-driven phases.

## The 4 Phases (PEV loop × contracts)

| # | Phase | Agent | Contract | Output |
|---|-------|-------|----------|--------|
| 1 | Spec | planner | `.mekong/phases/CLAUDE.spec.md` | `.mekong/SPEC_OUTPUT.md` — requirements |
| 2 | Design | architect | `.mekong/phases/CLAUDE.design.md` | `.mekong/DESIGN_OUTPUT.md` — architecture + ADR |
| 3 | Code | fullstack-developer | `.mekong/phases/CLAUDE.code.md` | `.mekong/TASKS.todo` — backlog |
| 4 | Deploy | tester | `.mekong/phases/CLAUDE.deploy.md` | `.mekong/DEPLOY_REPORT.md` — gate-verified ship report |

Each phase READS the prior phase's output + a `CLAUDE.<phase>.md` contract, then an agent FILLS the phase's output file.

## Usage

### Full flow (recommended)

```bash
# Start new feature
mekong spec new $ARGUMENTS

# After planner fills SPEC_OUTPUT.md
mekong design new $ARGUMENTS

# After architect fills DESIGN_OUTPUT.md
mekong code new $ARGUMENTS

# After developer fills TASKS.todo
mekong deploy new $ARGUMENTS
# → queries all 6 gates, scaffolds DEPLOY_REPORT.md
```

### Individual phase shortcuts

- `/sdlc:spec <feat>` — spec phase only
- `/sdlc:design <feat>` — design phase only
- `/sdlc:code <feat>` — code phase only
- `/sdlc:deploy <feat>` — deploy phase only (also queries CI gates via `gh run list --workflow=gates.yml`)

## Gate integration

The `deploy` phase auto-queries `.github/workflows/gates.yml` latest run and prints per-gate table:
- G1 Validation (ruff + pyright + tsc + pytest)
- G2 Security (bandit + semgrep + trivy)
- G3 Quality (coverage)
- G4 Dep Audit (osv-scanner + pip-audit)
- G5 Deploy Ready
- Merge Gate (aggregator)

Non-blocking if `gh` CLI unavailable (solo fast-path). Repo auto-detected from `git remote origin url`.

## Post-deploy signals

```bash
mekong metrics                          # overview: URL table + eval summary
mekong eval-agent <feat> --days 1       # per-feature success rate, p95, avg credits
```

Offline evals stored in `data/signals.sqlite`. PostHog + Statsig stubs present in `docker-compose.posthog.yml` and `src/core/signals/feature_flags.py` (deferred until >50 paying customers per YAGNI).

## Per-feature isolation (optional)

Set `MEKONG_FEATURE_DIR=1` to store each feature's 4 outputs under `.mekong/features/<slug>/` instead of flat `.mekong/*.md`. Useful when running multiple features concurrently.

## References

- Phase contracts: `.mekong/phases/CLAUDE.*.md`
- Templates: `.mekong/phases/templates/*.template.md`
- CLI source: `src/cli/sdlc/`
- Plan: `plans/260416-2323-mekong-cli-ide-raas-solo-platform/phase-04-sdlc-scaffold.md`
