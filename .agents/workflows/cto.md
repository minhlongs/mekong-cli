---
description: "CTO command suite — architecture decisions, team management, observability, deploy, incident response, roadmap, budget, code review."
---

# /cto — CTO Command Suite

**AUTO-EXECUTE MODE.** Detect sub-command from user prompt and execute.

## Available Sub-Commands

### `/cto architect` — Architecture Decision Record
1. Analyze current codebase architecture
2. Evaluate proposed change against existing patterns
3. Write ADR in `reports/cto/architect/`
4. Include: context, decision, consequences, alternatives

### `/cto review` — Code Review
1. Read specified files or recent changes (`git diff`)
2. Review for: correctness, security, performance, readability
3. Output review report with actionable items

### `/cto deploy` — Deployment Orchestration
1. Pre-deploy checklist (tests, lint, build)
2. Execute deployment steps
3. Post-deploy verification

### `/cto incident` — Incident Response
1. Gather error context (logs, stack traces)
2. Root cause analysis
3. Apply fix → test → verify
4. Write incident report in `reports/cto/incident/`

### `/cto roadmap` — Technical Roadmap
1. Review current state of project
2. Identify technical priorities
3. Create roadmap in `reports/cto/roadmap/`
4. Include: milestones, dependencies, risks

### `/cto budget` — Engineering Budget
1. Estimate infrastructure costs
2. CI/CD and tooling costs
3. Team allocation planning
4. Output budget document

### `/cto team` — Team Management
1. Team structure and roles
2. Skill matrix
3. Hiring recommendations

### `/cto onboard` — Onboarding New Developer
1. Generate project overview document
2. Setup guide (deps, env, run)
3. Key architecture walkthrough
4. First task assignment

### `/cto scorecard` — Engineering Scorecard
1. Code quality metrics (lint, test coverage)
2. Deployment frequency
3. Lead time for changes
4. Mean time to recovery

### `/cto archive` — Archive Completed Work
1. Move completed plans to `archive/`
2. Update project status
3. Generate completion report

### `/cto health` — System Health Check
// turbo
```bash
echo "🏥 CTO Health Check"
echo "==================="
echo ""
echo "📦 Dependencies:"
if [ -f "package.json" ]; then npm outdated 2>/dev/null | head -10; fi
if [ -f "pyproject.toml" ]; then pip list --outdated 2>/dev/null | head -10; fi
echo ""
echo "🧪 Tests:"
if [ -f "package.json" ]; then npm test 2>/dev/null; fi
if [ -f "pyproject.toml" ]; then python3 -m pytest -q --tb=no 2>/dev/null; fi
echo ""
echo "🔍 Lint:"
if [ -f "package.json" ]; then npm run lint 2>/dev/null; fi
if [ -f "pyproject.toml" ]; then python3 -m ruff check . 2>/dev/null; fi
```

### `/cto observability` — Observability Setup
1. Review existing logging/monitoring
2. Suggest improvements
3. Setup structured logging if missing
4. Configure alert thresholds

## Output Convention
All reports go to `reports/cto/{sub-command}/` directory.

## Not Available on Antigravity
- `/cto-dashboard` — requires OpenClaw factory-roi-calculator
- `/cto-workforce` — requires factory-throughput-optimizer
- `/cto-selftest` — requires factory self-test infrastructure
