---
name: opus-tomhum-orchestrator
description: "Opus Tôm Hùm Team — Self-orchestrate as 5-department company. Builds full-stack code multi-threaded. 30+ credits, ~90 min."
source: mekong-ai-os
version: 1.0.0
credit_cost: 2
---

description: "Opus Tôm Hùm Team — Self-orchestrate as 5-department company. Builds full-stack code multi-threaded. 30+ credits, ~90 min."
argument-hint: [product or feature to build]
allowed-tools: Read, Write, Bash, Task
---

# /opus-tomhum-orchestrator — Tôm Hùm Team Full-Stack Builder

**Solo Founder Operating Company** — Opus runs ALL 5 levels of the ROIaaS command hierarchy autonomously, spawning parallel sub-agents for multi-department execution.

## Architecture

```
OPUS (You) = Chairman + CTO + PM + Dev + Worker
Delegation: studio → cto → pm → dev(parallel) → worker(atomic)
```

## Execution Pipeline

### Phase 1: STUDIO (Chairman/Investor) — 🏛️
Run as VC Studio — strategic analysis:
1. Analyze the goal: `$ARGUMENTS`
2. Define ROI target metrics (MRR, users, timeline)
3. Identify competitive advantages and risks
4. Output: `reports/studio/strategy.md`

### Phase 2: CTO (Architecture) — 🧠  
Run as CTO — technical design:
1. Design system architecture based on Phase 1 strategy
2. Choose tech stack, define API contracts
3. Identify existing code in monorepo to reuse
4. Output: `reports/cto/architecture.md`

### Phase 3: PM (Sprint Planning) — 📋
Run as PM — break into parallel work units:
1. Decompose architecture into 3-4 parallel sprints
2. Each sprint = 1 sub-agent (Task tool)
3. Define dependencies between sprints
4. Output: sprint backlog with clear acceptance criteria

### Phase 4: DEV (Parallel Execution) — ⚙️
**Spawn 3-4 sub-agents simultaneously** using Task tool:

```
Task 1: "Backend API" — scaffold routes, implement business logic, write tests
Task 2: "Frontend/CLI" — UI components, command integration, user flows
Task 3: "Testing/QA" — unit tests, integration tests, security audit
Task 4: "DevOps" — CI/CD config, deployment scripts, monitoring
```

Each sub-agent:
- Reads the architecture doc from Phase 2
- Implements their department's code
- Runs worker:test and worker:scan
- Commits with descriptive message

### Phase 5: INTEGRATION — 🔗
After al

[Full documentation at agencyos.network]

---
*Powered by Mekong AI OS — Operational knowledge, not just prompts.*
*Full RaaS access: https://agencyos.network*
