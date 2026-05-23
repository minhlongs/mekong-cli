# Agentic Workflow Patterns — Research Report (2025-2026)

**Date:** 2026-05-23 | **Scope:** Multi-agent orchestration, memory, tool use/MCP, production reliability

---

## 1. Multi-Agent Orchestration

### Winning Patterns

| Pattern | When | Scale |
|---------|------|-------|
| **Supervisor** (80% market) | Default choice, clear delegation | < 5 agents |
| **Hierarchical** (2-tier) | Complex features, code-heavy | 5–20 agents |
| **DAG-based** (LangGraph) | Complex reasoning, visual debug | > 20 agents |

**Supervisor** dominates: orchestrator owns context → spawns isolated subagents → collects summaries. Fresh context per agent wins over shared state.

### Root Causes of Failure (ranked)

| Cause | % | Fix |
|-------|---|-----|
| Lost state on handoff | 40% | Checkpoint protocol (state JSON per step) |
| File conflicts (parallel) | 30% | Git worktrees + ownership matrix |
| Stale agent context | 15% | Force-refresh at decision points |
| Tool timeouts | 10% | Timeout + fallback routing |
| Task misclassification | 5% | P2 prompt contract validation |

### Critical Practices

- **P2 Prompt Contract**: structured objective + output format + tool scope + escalation rules. 15–25% performance lift; misclassification drops 22% → 4%.
- **Git Worktrees**: each agent isolated worktree, shared `.git`. Eliminates silent file overwrites. Tested ~50 concurrent agents on M1 16GB.
- **Checkpoint/Resume**: agent saves state JSON at every step → next agent reads checkpoint → resumes from exact point. Zero context repetition.
- **Pre-merge conflict check**: `git merge-tree` before final merge prevents 30% of integration failures.

### Framework Comparison

| Framework | Best For | Weakness |
|-----------|----------|----------|
| **LangGraph** (62% adoption) | Complex reasoning, visual debug | Python-first, steep curve |
| **OpenAI Agents SDK** | Chat handoffs, simple pipelines | Proprietary, API-bound |
| **Claude Code Teams** | Research + review, feature teams | 5–10 agent ceiling, quota-hungry |
| **CrewAI** | Linear workflows, content gen | 54% success vs LangGraph 62% |
| **Google ADK** | Cloud-first, MCP-heavy | Early adoption risk |

---

## 2. Memory & Context Management

### Three-Tier Architecture (Industry Standard)

| Tier | What | Storage |
|------|------|---------|
| **Episodic** | Raw interaction history + timestamps | Vector DB + event logs |
| **Semantic** | Extracted facts & profiles | Structured DB + embeddings |
| **Procedural** | Reusable task patterns | Workflow DB + examples |

Automatic consolidation (episodic → semantic) standard. Mem0's April 2026 release improved temporal reasoning by +29.6 points via single-pass hierarchical extraction.

### Context Window Management

**2025 shift**: agent-controlled compression > external summarization.

- **Letta (MemGPT)**: agents manage own memory via tool calls — move to archive, fetch on demand, prune low-signal
- **Compression**: summarization (10-50x but lossy), compaction (faster, better fidelity), JIT loading (smart retrieval)
- **Context rot**: degrades reasoning 3-5x; aggressive culling required

### Multi-Agent State Safety

- **36.9%** of multi-agent failures from interagent misalignment (O'Reilly 2025)
- One corrupted state value poisoned **87%** of downstream decisions in 4 hours (Galileo simulation)
- **Fix**: multi-scope tagging (`app_id`, `org_id`, `user_id`, `agent_id`, `session_id`), strict scope enforcement, temporal isolation

### Storage Backend

**Winner: PostgreSQL + pgvector** — single store for structured facts (SQL) + semantic search (vector), native backup/replication, cost-effective.

### Notable Systems

| System | Best For | Tradeoff |
|--------|----------|----------|
| **Mem0** | Fast integration, SaaS | Less agent control; opaque consolidation |
| **Letta** | Enterprise, auditable | Slower integration; more agent redesign |
| **Zep** | Temporal reasoning, events | Overkill for stateless; requires ontology |

---

## 3. Tool Use & MCP Integration

### MCP State (May 2026)

- **13,000–14,000** production MCP servers; 97M monthly SDK downloads
- Governed by Linux Foundation (Agentic AI Foundation) — Anthropic, OpenAI, Google, Microsoft, AWS co-founders
- **Transport**: stdio (local, default), Streamable HTTP (remote, replaces SSE)

### Tool Design

- **Validator Pattern** (highest ROI): LLMs generate malformed JSON ~15-20% of the time. Schema validation → error feedback → self-correction achieves ~80% fix on first retry.
- **Structured results**: `{success, data, error, retryable}` enables agent decision-making
- **Granularity**: balance coarse (simpler LLM reasoning) vs fine-grained (precise, reusable)

### Security (Critical)

| Attack | Mitigation |
|--------|-----------|
| Confused Deputy (OAuth bypass) | Per-client consent before third-party auth |
| Token Passthrough | MCP server validates token claims, issues new token |
| SSRF (malicious URLs) | HTTPS only, block private IPs, egress proxies |
| Session Hijacking | Secure non-deterministic session IDs, bind to user |

**Reality**: 53% of public MCP servers use hard-coded secrets; only 8.5% use OAuth.

**April 2026 RCE**: OX Security disclosed RCE in all MCP SDKs (Python, TS, Java, Rust), impacting 150M+ downloads. Keep SDKs patched.

### Orchestration

- **Parallel execution**: 20–40% latency improvement for independent tasks
- **Graph-based planning (GAP)**: emerging; agents learn parallelization autonomously via RL
- **Supervisor agent**: orchestrator + N specialists; sweet spot 3–10 agents

---

## 4. Production Reliability

### Cost Control (70-80% savings possible)

- Small models 17-25× cheaper than frontier
- Route 60-80% of tasks to cheaper models; reserve frontier for complex reasoning
- Multi-model routing beats token budgets alone

### Error Handling

- **Idempotency mandatory**: every action must be safe to execute twice
- **Bounded iteration**: max 5 retries/subtask, max 20 total iterations/workflow
- **Circuit breaker**: trip after 3–5 consecutive failures; periodically test availability
- **Fallback chains**: primary → cached → 503

### Observability

- **OpenTelemetry** converged as standard in 2025 (LLM observability market $2.69B/2026 → projected $9.26B/2030)
- Trace: LLM calls, tool invocations, retrieval steps, planning decisions
- Notable: LangSmith (LangChain-native), Braintrust (CI/CD enforcement), Patronus AI (hallucination scoring)

### Rate Limiting (3-Layer Gateway)

| Layer | What |
|-------|------|
| 1 | Token bucket per (user, repo, model) |
| 2 | Circuit breakers on cost velocity, error rate, stuck loops |
| 3 | Fallback chains (primary → cached → 503) |

### HITL (Human-in-the-Loop)

- **> 85% confidence**: autonomous execution
- **60-85%**: escalate to humans
- **< 60%**: always escalate
- Target: 10-15% escalation rate in mature deployments

### Testing

Multi-pillar assessment, not task-centric:
- LLM instruction following, retrieval accuracy, tool selection, workflow execution, guardrail compliance
- Non-determinism requires multiple test runs per scenario
- Braintrust: auto-merge blocking on score drops

---

## Cross-Cutting Unresolved Questions

1. **Byzantine failures**: no framework addresses agents reporting wrong state; HITL is current workaround
2. **5M+ token workflows**: all frameworks hit wall at 2M tokens
3. **Consolidation frequency**: how often episodic → semantic? No consensus
4. **Cross-agent learning**: should one agent's insights be visible to others? Reuse vs isolation tradeoff unclear
5. **MCP stateless operation**: 2026 roadmap, no finalized spec yet
6. **Deterministic testing**: of probabilistic systems remains unsolved
7. **Cost prediction**: before deployment not standardized
8. **Circuit breaker tuning**: guidance varies (3? 5? 10? failures) by tool type

---

## Decision Matrix

| You Need | Start With |
|----------|-----------|
| Simple delegation (< 5 agents) | Supervisor + OpenAI Agents SDK |
| Complex code workflows | LangGraph + git worktrees |
| Enterprise memory | PostgreSQL + pgvector + multi-scope tagging |
| Tool integration | MCP servers + validator pattern |
| Cost control | Multi-model routing (cheap→expensive) |
| Observability | OpenTelemetry + LangSmith/Braintrust |
| Handoff reliability | Checkpoint/resume protocol + P2 prompt contracts |

---

*Sources: 60+ references across Anthropic, OpenAI, Google, LangChain, O'Reilly, ArXiv, n8n, Palo Alto Networks, Astrix Security, Mem0, Letta, Zep. Full source lists in individual research reports.*
