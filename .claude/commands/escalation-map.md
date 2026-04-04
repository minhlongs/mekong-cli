---
description: "OpenClaw Escalation Policy — all commands mapped to L0-L3 autonomy levels"
argument-hint: [level or command-name]
allowed-tools: Read, Write, Bash, Task
---

# /escalation:map — Escalation Policy

Show or query the escalation level for any command.

## Levels

### Level 0: Fully Autonomous (no notification)
Read-only, monitoring, health checks — zero risk.
health, status, daily, sre:morning-check, cto-dashboard, cto-health,
cto-observability, cto-selftest, cto-workforce, production-status,
factory-intelligence, worker:health, worker:log, worker:trace,
worker:scan, portfolio:status, risk:monitor, momentum:velocity,
context:priority, context:compress, obs:metrics, obs:logs,
commands-status, model-matrix

### Level 1: Autonomous with Notification
Write operations, builds, standard ops — low risk.
worker:code, worker:build, worker:test, worker:commit, worker:push,
worker:exec, worker:backup, dev:feature, dev:bug-sprint, dev:pr-review,
eng:sprint-execute, eng:tech-debt, backend:api-build, backend:db-task,
frontend:ui-build, frontend:responsive-fix, qa:plan, qa:e2e, qa:perf,
qa:regression, qa:accessibility, qa:chaos, data:daily-pipeline,
data:transform, data:quality, data:catalog, sec:scan, sec:vuln,
ml:eval, ml:monitor, ml:experiment, ml:cost, marketing:content-engine,
writer:blog, writer:newsletter, writer:social-batch, analyst:report,
analyst:forecast-update, growth:experiment, accounting:daily,
accounting:invoice-batch, hr:performance-cycle, devrel:docs,
devrel:community, devrel:advocate, kb:adr, kb:wiki, infra:topology,
infra:network, obs:dashboard, obs:trace

### Level 2: Propose + Human Approves
Financial, customer-facing, deployment, security — medium risk.
ship, release:ship, release:hotfix, devops:deploy-pipeline,
devops:rollback, finance:monthly-close, finance:budget-plan,
finance:collections, sales:deal-close, marketing:campaign-run,
legal:contract-review, legal:compliance-check, sec:incident,
sec:full-audit, sec:compliance-report, sec:access-review,
sec:secrets, sec:policy, compliance:sox-cycle, compliance:soc2-prep,
ml:deploy, ml:retrain, ml:guardrail, pm:feature-flag, pm:ab-test,
revops:forecast, revops:comp, hr:recruit, hr:onboard, people:offboard,
vendor:assess, vendor:onboard, vendor:offboard, treasury:position,
treasury:forecast, board:manage, board:minutes, ir:narrative,
ir:roadshow, ir:metrics, data:full-refresh, corpdev:evaluate,
infra:region, infra:gateway, infra:optimize, terrain:segment,
terrain:position, terrain:entry, momentum:resource, momentum:network,
momentum:compound, cdp:profile, cdp:segment

### Level 3: Human Initiates Only
Strategic, irreversible, high-stakes — critical risk.
ipo:readiness-check, ipo:board-prep, governance:entity,
governance:disclosure, governance:policy, board:compliance,
corpdev:integrate, corpdev:scout, venture:thesis, studio:launch-full,
sec:incident-response, esg:report, ir:calendar, terrain:defend,
terrain:retreat, momentum:viral-loop, intel:blind-spot, intel:asymmetry

## Override Rules
- `sec:*` commands: minimum Level 1
- `finance:*` commands: minimum Level 2
- `ipo:*` commands: minimum Level 3
- `governance:*` commands: minimum Level 3
- `corpdev:*` commands: minimum Level 2

## Goal context
<goal>$ARGUMENTS</goal>
