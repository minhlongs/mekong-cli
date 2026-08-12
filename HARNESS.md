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

---

## 9. Core DNA and Contribution Gate

Mekong is open source, but the official runtime feature surface is governed
by `dna/core-dna.json`.

- Existing shipped features must be declared in the Core DNA manifest.
- New local-only features are blocked by `src/core/core_dna.py` unless they
  run in a pull-request contribution context.
- Advanced Binh Phap and autonomous features remain usable only when declared
  by the manifest or contributed for owner/community review.
- The harness roots are public and auditable: `HARNESS.md`, `sops/`,
  `agents/registry.yaml`, `evals/`, `src/harness/`, `src/binh_phap/`.
- The CLI command `mekong binh-phap dna --feature <name>` explains the gate.
- The Binh Phap operating doctrine is declared in
  `dna/binh-phap-operating-system.json` and validated by
  `mekong binh-phap doctrine`.
- The Hermes-style learning loop is declared in
  `dna/hermes-learning-loop.json` and validated by `mekong harness-eval`.
- The root CLI command surface is declared in `dna/command-surface.json`;
  new commands must update it through PR review.

HARNESS.md v1.1.0 — CEO Solo Agentic Platform — Mekong CLI

---

# Appendix A — `mk auto` (v7 Natural-Language Auto-Harness)

## Usage

```bash
mk auto "<yêu cầu ngôn ngữ tự nhiên>"          # plan + execute với gates
mk auto "<yêu cầu>" --dry-run                  # chỉ sinh plan, không chạy
mk auto "<yêu cầu>" --resume                    # tiếp tục từ checkpoint cuối
mk auto "<yêu cầu>" --resume --decision approve # ghi đè gate (approve|deny)
```

## Pipeline

1. **Intent router** (`src/mk7/core/router.py`) — Haiku classify → JSON-strict:
   `{task_type, skill_hint, target_agent, danger_level, confidence}`.
   `confidence < 0.7` → exit 1, yêu cầu rephrase (HITL).
2. **Planner** — sonnet decompose → DAG nodes `{id, task, agent, depends_on, gate}`.
3. **Graph engine** (`src/mk7/core/graph.py`) — topo execution, checkpoint sau mỗi
   node tại `~/.mekong/state/<slug>.json`, retry ≤3/node, budget: max 20 nodes /
   60 LLM calls. Node độc lập chạy song song (tuần tự trong v7 MVP).
4. **Gate protocol** (`src/mk7/core/gates.py`) — node có `gate` → dừng, exit **42**,
   host agent hỏi operator → `--resume --decision approve|deny`.

## Gates mặc định (exit 42)

| Keyword | Gate key | Hard |
|---|---|---|
| deploy | deploy | no |
| rm / xóa file | rm | no |
| git push --force | force_push | no |
| chi-tien / spend | spend_money | no |
| xoa-data / delete data | delete_data | no |
| code_review_required | — | **yes** |
| ci_checks_pass | — | **yes** |
| no_force_push_main | — | **yes** |

Hard gates không thể override bằng `--decision`.

## Tool whitelist (`src/mk7/core/tools.py`)

Chỉ cho phép: `read`, `write`, `cat`, `bash-test`, `bash`.
`bash-test`/`bash` chặn mọi command phá hoại: `rm`, `mv`, `git push`,
`git reset --hard`, `sudo`, `dd`, `mkfs`.

## Exit codes

| Code | Ý nghĩa |
|---|---|
| 0 | Thành công |
| 1 | Lỗi (router HITL, graph invalid, budget, node fail) |
| 42 | Gate chặn — cần operator decision |

## Danger levels

`low` (read-only) · `medium` (sửa file local) · `high` (deploy/rm/force-push) ·
`critical` (chi tiền / xóa data). Nodes danger high/critical nên khai `gate`.

## Ví dụ

```bash
mk auto "fix bug login chậm trên mobile" --dry-run
mk auto "viết spec cho tính năng checkout" --dry-run
mk auto "deploy to production"              # → gate → exit 42
mk auto "deploy to production" --resume --decision approve
```

## Model routing

Mọi node dispatch qua `src/mk7/core/dispatch.py` → `models.py` role →
gateway OmniRoute. Agents `sonnet`/`opus` hiện resolve `claude-opus-4-8[1m]`
(1M context). Strategist = qwen3.8-max (Stali, paid cuối).
