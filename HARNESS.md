# HARNESS.md — CEO Solo Agentic Harness Configuration

This file is the **runtime contract** for the mekong-cli agent harness.
It defines context budget, guardrails, delegation rules, and escalation
paths for the CEO Solo operating model.

---

## 1. Context Budget

| Slot | Budget | Notes |
|------|--------|-------|
| System prompt | ≤ 4 000 tokens | HARNESS.md, AGENTS.md, active SOP |
| Conversation history | ≤ 12 000 tokens | Compaction trigger at 10 000 |
| Tool output | ≤ 8 000 tokens | Truncate long bash/grep output |
| Active file context | ≤ 16 000 tokens | One primary file at a time |
| **Total context ceiling** | **≤ 40 000 tokens** | Hard stop; compact before hitting |

**Rule:** Every subagent receives only the SOP fragment relevant to its task, never the full HARNESS.md.

---

## 2. Tool Allowlist by Layer

| Tool | CEO | Business | Product | Engineering | Ops |
|------|-----|----------|---------|-------------|-----|
| Bash | ✓ read-only | ✓ scoped | ✓ scoped | ✓ full | ✓ read-only |
| Read | ✓ | ✓ | ✓ | ✓ | ✓ |
| Write | ask | ask | ✓ | ✓ | ask |
| Edit | ask | ask | ✓ | ✓ | ask |
| Task (subagent) | ✓ | ✓ | ✓ | ✓ | ✓ |
| WebFetch | ✓ | ✓ | ✓ | ✓ | ✗ |

---

## 3. CEO Override Clauses

1. **CEO may override any decision** without explanation.
2. CEO may bypass review gates by adding `--ceo-override` to any command.
3. CEO may terminate any running subagent by name via `/abort <agent>`.
4. CEO may set `risk-gate.autoStopRequired = false` for low-risk tasks.

---

## 4. High-Risk Gate Definitions

A **high-risk** action requires explicit CEO approval before execution:

- Deleting or modifying production database records
- Pushing to `main` branch (force or non-force)
- Publishing packages to public registries
- Modifying billing or payment configuration
- Sending external communications (emails, API calls to clients)
- Rotating secrets or credentials

High-risk actions: `ask` in permissions → CEO approval required.

---

## 5. Agent Delegation Matrix

```
CEO Solo
 ├── Layer: Business      → AE (Account Executive) agent
 │                            Handles: deals, contracts, invoices
 ├── Layer: Product       → PM (Product Manager) agent
 │                            Handles: roadmap, specs, priorities
 ├── Layer: Engineering   → ENG (Engineer) agent
 │                            Handles: code, review, deployment
 └── Layer: Ops           → OPS (Operations) agent
                              Handles: monitoring, incidents, vendor
```

Each subagent receives:
- Relevant SOP fragment (`sops/<layer>/`)
- Task context from CEO
- Budget envelope (token + time limits)

---

## 6. Escalation Path

| Situation | Action |
|-----------|--------|
| Subagent returns `verification_passed: false` | CEO reviews → decide: retry, modify, abort |
| Subagent fails ≥3 times on same task | CEO decides: escalate to human, decompose, deprioritize |
| Context budget exceeded | Auto-compact → resume with summary |
| External API rate limit hit | Backoff + retry (max 3) → escalate if persists |
| Ambiguous intent detected | STOP → Ask CEO via AskUserQuestion |

---

## 7. Observability Integration

Traces are written to `observability/traces/` in OpenTelemetry JSON format:
- `span_id`, `parent_span_id`, `agent_name`, `tool`, `duration_ms`
- `tokens_used`, `verification_passed`, `error`

Eval runs use `evals/solo-ceo-eval.md` as the test suite.

---

## 8. SOP Invocation Rules

- Always load SOP before starting task in that domain
- Reference SOP section explicitly: "Per SOP §X.Y: …"
- Update SOP after task completion if process was found inadequate
- SOP version tracked in frontmatter; bump when behavior changes

HARNESS.md v1.0.0 — CEO Solo Agentic Platform — Mekong CLI
