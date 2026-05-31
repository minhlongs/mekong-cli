# Mekong Harness Engineering Architecture
**Version:** 1.0.0 | **Pattern:** awesome-harness-engineering

## What is Harness Engineering?

Harness engineering is the practice of **shaping the environment around AI agents** so they behave reliably at scale. It is not prompt engineering — it is system design for agentic work.

> "The harness is the difference between a clever prompt and a reliable system." — walkinglabs

---

## Mekong's Harness Design

Mekong applies harness engineering principles to the **CEO Solo Agentic** use case: one person operating a company through a structured AI agent system.

### 1. Context Engineering

**Problem:** Context window is finite. Without discipline, agents lose track of constraints, history, and company-specific rules.

**Mekong Solution:**
- `HARNESS.md` — Runtime contract loaded at session start
  - Context budget rules (hard ceiling: 40k tokens)
  - Tool allowlists per layer (CEO, Business, Product, Engineering, Ops)
  - CEO override clauses
  - High-risk gate definitions
- Subagents receive **SOP fragments only**, never full HARNESS.md
- Auto-compaction triggers at defined thresholds

### 2. Constraints & Guardrails

**Problem:** Agents with broad capabilities can cause real damage (push to main, delete data, send external comms).

**Mekong Solution:**
- `.claude/settings.json` — Claude Code permission model
  - `allow`: whitelist of safe Bash commands
  - `deny`: explicit blocks (rm -rf /, git push --force, .env access)
  - `ask`: high-risk actions requiring CEO approval
- SOP-level hard gates (e.g., code review required before merge)
- CEO override clause (`--ceo-override` flag) with audit trail

### 3. Specs & Workflow Design

**Problem:** Ad-hoc agent work is unpredictable. Without structured workflows, quality and consistency suffer.

**Mekong Solution:**
- `sops/` — Standard Operating Procedures as executable specs
  - Each SOP: intent → steps → acceptance criteria → escalation
  - Version-tracked, updated when process gaps found
  - Agents reference SOPs explicitly: "Per SOP §X.Y: …"
- `/cook` command — Structured implementation workflow with hard gates
  - TDD gate, review gate, verification gate
  - Anti-rationalization table prevents cutting corners

### 4. Evals & Observability

**Problem:** You cannot improve what you cannot measure. How do you know if your agent harness is working?

**Mekong Solution:**
- `observability/` — OpenTelemetry-compatible trace collection
  - Prometheus + Grafana dashboards for agent metrics
  - Cost tracking, error rates, response times
- `evals/solo-ceo-eval.md` — Harness quality eval suite
  - Context budget compliance
  - SOP adherence
  - Guardrail enforcement
  - Escalation behavior
  - Review gate compliance

### 5. Orchestration

**Problem:** A solo CEO needs multiple specialized agents without operational overhead.

**Mekong Solution:**
- `agents/registry.yaml` — Declarative agent definitions
  - Role, tools, SOP scope, context budget per agent
  - Delegation rules: route task to correct layer agent
  - CEO Solo has override authority, max 4 concurrent subagents
- `/cook-auto` — Autonomous goal execution with checkpointing
- `/cook-auto-parallel` — Parallel task execution with independent agent isolation

### 6. Safe Autonomy

**Problem:** Autonomous agents running without oversight can cause cascading failures.

**Mekong Solution:**
- CEO override available at any point
- High-risk actions always require approval (never auto-executed)
- All-fail halt: if all parallel agents fail review, halt and escalate
- Post-mortem required for P1/P2 incidents
- Decision log: every CEO decision documented before execution

---

## Harness vs Prompt Engineering

| Aspect | Prompt Engineering | Harness Engineering |
|--------|--------------------|--------------------|
| Focus | What to tell the model | What to build around the model |
| Scope | Single interaction | System-wide reliability |
| Tools | Prompts, few-shots | Context, guardrails, workflows, evals |
| Failure mode | Bad output | Systemic failure |
| Fix approach | Rewrite prompt | Redesign environment |

---

## Getting Started

1. Read `HARNESS.md` — understand context budget and guardrails
2. Load relevant SOP from `sops/<layer>/` before starting work
3. Use `/cook` for implementation tasks (structured workflow)
4. Monitor `observability/dashboards/` for system health
5. Run `evals/solo-ceo-eval.md` weekly to validate harness quality

## Awesome-Harness-Engineering References

See: https://github.com/walkinglabs/awesome-harness-engineering
