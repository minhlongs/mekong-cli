# Tech Lead Report — Mekong CLI
*Role: Tech Lead | Date: 2026-03-11*

---

## Architecture Overview

Mekong CLI is built around the PEV (Plan → Execute → Verify) engine, a three-phase
orchestration loop that maps directly to how LLMs decompose and execute goals.

```
Goal Input
    │
    ▼
┌─────────────┐
│  PLANNER    │  src/core/planner.py
│  LLM decomposes goal into ordered steps with rollback hints
└──────┬──────┘
       │ StepList
       ▼
┌─────────────┐
│  EXECUTOR   │  src/core/executor.py
│  Runs: shell / LLM-generate / API / file / parallel
└──────┬──────┘
       │ ExecutionResult
       ▼
┌─────────────┐
│  VERIFIER   │  src/core/verifier.py
│  Checks: exit codes / test pass / type check / LLM assessment
└──────┬──────┘
       │ pass/fail
       ▼
┌─────────────────────┐
│  ORCHESTRATOR       │  src/core/orchestrator.py
│  PEV loop, rollback │  reverses completed steps via step.params.rollback
└─────────────────────┘
```

---

## Key Design Decisions

### 1. Universal LLM via 3-Variable Interface
```bash
LLM_BASE_URL + LLM_API_KEY + LLM_MODEL
```
Any OpenAI-compatible endpoint works. Fallback chain in `src/core/llm_client.py`:
OpenRouter → DashScope → DeepSeek → Anthropic → OpenAI → Google → Ollama → Offline.

**Why:** Vendor lock-in is the #1 reason developer tools die. Universal interface
ensures Mekong CLI works when any single provider has an outage or price hike.

### 2. Rollback-First Step Design
Every planner step carries a `rollback` param. Orchestrator reverses completed steps
in LIFO order on failure. This is the core reliability guarantee.

**Trade-off:** Rollback adds complexity to step definitions. Not all operations are
truly reversible (e.g., sent emails, API calls). Document non-reversible steps clearly.

### 3. Agent Registry Pattern
`src/agents/__init__.py` exports `AGENT_REGISTRY` dict — CLI looks up agents by string
key. Clean separation between agent discovery and agent implementation.

**Extensibility:** Adding a new agent = create `src/agents/my_agent.py` + register in
`AGENT_REGISTRY`. No changes to core engine.

### 4. Cloudflare-Only Infrastructure
All deployment targets are Cloudflare: Workers, Pages, D1, KV, R2, Queues.
Zero vendor split means zero cross-provider latency and $0 cost at current scale.

**Risk:** CF vendor lock-in. Mitigation: adapter pattern in `mekong/adapters/` allows
swapping infra layer. The `llm-providers.yaml` pattern should be replicated for infra.

---

## LLM Router Patterns

Current implementation in `src/core/llm_client.py`:

```python
# Fallback chain (simplified)
providers = [
    ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1"),
    ("DASHSCOPE_API_KEY", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    ("DEEPSEEK_API_KEY", "https://api.deepseek.com"),
    ("ANTHROPIC_API_KEY", "https://api.anthropic.com/v1"),
    ("OPENAI_API_KEY", "https://api.openai.com/v1"),
    ("GOOGLE_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/"),
    ("OLLAMA_BASE_URL", "{OLLAMA_BASE_URL}/v1"),
]
```

**Improvement opportunity:** Add latency-aware routing — prefer fastest responding
provider in real-time rather than static fallback order.

---

## PEV Engine Extensibility Points

| Extension Point | Interface | Current Implementations |
|----------------|-----------|------------------------|
| Step type | `executor.py` dispatch | shell, llm, api, file, parallel |
| Verification check | `verifier.py` check list | exit_code, test_output, type_check, llm_assess |
| Agent | `AgentBase.plan/execute/verify` | LeadHunter, ContentWriter, RecipeCrawler, GitAgent, FileAgent, ShellAgent |
| LLM provider | `llm_client.py` fallback chain | 8 providers + OfflineProvider |
| Command | `.agencyos/commands/*.md` | 289 commands |
| Contract | `factory/contracts/*.json` | 176 contracts |

---

## Technical Debt Assessment

### P0 — Fix immediately
- `test_file_stats` scans entire repo: mock `os.walk` or scope to `tests/fixtures/`
- Untracked `src/jobs/cloudflare-*.ts` files: integrate or remove

### P1 — Next sprint
- Missing type hints in agents layer (AgentBase subclasses)
- `ExecutionResult` dataclass needs `__post_init__` validation
- No retry logic in `llm_client.py` — add exponential backoff

### P2 — Backlog
- `planner.py` LLM prompt is not versioned — add prompt version field to steps
- Parallel execution in executor lacks timeout per step
- No structured logging — add `structlog` for JSON log output

---

## Architecture Decision Records (Proposed)

Future ADRs to document:
1. ADR-001: Why PEV over ReAct/Chain-of-Thought
2. ADR-002: Why Cloudflare over AWS/GCP
3. ADR-003: Why MCU credits over pure subscription
4. ADR-004: Why MIT license over AGPL for monetization

---

## Code Review Standards

For PRs to `src/core/`:
1. New step types must have rollback handler or explicit `rollback: null` with reason
2. All LLM calls must go through `llm_client.py` — no direct `httpx`/`requests` to LLM APIs
3. `ExecutionResult` must be the return type for all executor methods
4. Tests required for any new verification check type
5. File size < 200 lines — split if needed

---

## Next Technical Priorities

- [ ] Add `pytest-mock` and fix `test_file_stats` slowness
- [ ] Add retry + backoff to `llm_client.py`
- [ ] Integrate `src/jobs/cloudflare-*.ts` into CF adapter layer
- [ ] Version prompt templates in planner
- [ ] Add `structlog` for structured JSON logging
