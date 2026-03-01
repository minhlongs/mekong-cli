# Core Engine & Agent System — Research Report
Date: 2026-03-01 | Researcher: aa12023b73c860dee

---

## 1. Plan-Execute-Verify (PEV) Pattern

**Flow:** `goal → RecipePlanner.plan() → Recipe{steps} → RecipeOrchestrator.run_from_recipe() → [execute_step + verify] per step → OrchestrationResult`

**NLU pre-routing (shortcut):** Before planning, `IntentClassifier.classify(goal)` fires. If confidence > 0.7 → `SmartRouter` tries to match an existing `.md` recipe → skip planning entirely.

**Planning modes:**
- LLM mode: calls `llm_client.generate_json(prompt)` → JSON task array
- Rule-based fallback: pattern matches on "implement", "fix", "deploy", "git X", etc.

**Execution modes per step (step.params["type"]):**
- `shell` — subprocess.run, retry with `max_attempts`, partial capture
- `llm` — calls `LLMClient.chat()`, truncates to 2000 chars output
- `api` — requests.request(method, url, json, headers)

**Self-healing:** Failed shell steps → LLM generates corrected command → one retry. Uses `RetryPolicy.is_retryable(stderr, exit_code)` to gate eligibility.

**Rollback:** On step failure with `enable_rollback=True`, iterates completed steps reversed, runs `step.params["rollback"]` shell command. Requires recipe author to embed rollback cmd in step params.

**Verification criteria per step** (generated or embedded in params["verification"]):
```python
VerificationCriteria: exit_code, file_exists[], file_not_exists[],
  output_contains[], output_not_contains[], custom_checks[]
```
Custom checks: shell command string or `{"command": str, "expected_output": str}`.

**Quality gates** (`verify_quality_gates`): Binh Pháp checks on stdout — no TODO/FIXME, no console.log, no `: any`, no vuln keywords. Run against any ExecutionResult.

---

## 2. Recipe System

**Format:** Markdown with YAML frontmatter (`---\nname: X\nagent: Y\n---`) + `## Step N: Title` headers.

**Parser:** `RecipeParser` — regex splits on `## Step N:` pattern. Frontmatter parsed as simple `key: value` lines (not full YAML). No nested structures. `parse_string()` for inline recipes.

**Registry:** `RecipeRegistry.scan()` — scans `recipes/` dir for `.md` files. Supports tag-based `search(query)`.

**Recipe generation:** `RecipeGenerator.from_goal_pattern()` — template-based `.md` output, saved to `recipes/auto/`. Validates via basic step-count check.

---

## 3. LLM Client Architecture

**Priority chain:** GEMINI_API_KEY (google-genai SDK) → ANTIGRAVITY_PROXY_URL (OpenAI-compat REST) → OPENAI_API_KEY → offline mode.

**Circuit breaker:** `ProviderHealth` per provider — 3 consecutive failures → 60s cooldown. `_get_ordered_providers()` skips unhealthy; if all unhealthy → try all anyway.

**Portkey-inspired features:**
- `HookPipeline` with PRE_REQUEST / POST_REQUEST / ON_ERROR phases
- `LLMCache` — LRU cache keyed by (messages, model, temperature)
- Status-code routing: HTTP 400 → immediate return; 429/5xx → failover to next provider

**Vertex/Gemini path:** Uses `google.genai.Client`, extracts `response.text` (fallback to `candidates[0].content.parts[0].text`). Retries 3x with full jitter backoff on 429/503/timeout.

**API:** `chat(messages, model, temperature, max_tokens, json_mode)` → `LLMResponse{content, model, usage, raw}`. Helpers: `generate(prompt)`, `generate_json(prompt)`.

---

## 4. Agent Architecture

**AgentBase (ABC):**
```python
plan(input: str) -> List[Task]      # abstract
execute(task: Task) -> Result        # abstract
verify(result: Result) -> bool       # overridable, default: result.success
run(input: str) -> List[Result]      # main loop: plan → [execute+verify+retry]
```
`max_retries=3` per task. `TaskStatus`: PENDING → RUNNING → SUCCESS/RETRY/FAILED.

**Concrete agents:**

| Agent | Real ops? | Notes |
|-------|-----------|-------|
| GitAgent | Yes | subprocess git, cwd param, 60s timeout |
| FileAgent | Yes | subprocess find/grep, path traversal protection, stats via rglob |
| ShellAgent | Yes | BLOCKED_COMMANDS/BLOCKED_PATTERNS safety check, 30s/120s timeout |
| LeadHunter | Simulated | Placeholder outputs — needs Clearbit/Hunter.io |
| ContentWriter | Simulated | Placeholder — needs LLM calls |
| RecipeCrawler | Simulated | Placeholder — needs GitHub API |

**Agent routing in planner:** `AGENT_KEYWORDS` dict maps agents to keyword lists. Keyword scoring → top agent attached to all tasks.

---

## 5. Orchestrator Key Design

**Imports:** Uses `ExecutionHistory` (event sourcing), `RetryPolicy` (Temporal-inspired), `WorkflowState` (state machine with step transitions), optional `SwarmDispatcher`.

**Event kinds:** WORKFLOW_STARTED/COMPLETED/FAILED, STEP_SCHEDULED/COMPLETED/FAILED, ROLLBACK_STARTED/COMPLETED, SELF_HEAL_ATTEMPTED/SUCCEEDED.

**Persistence:** `history.persist(workflow_id)` after each run. Telemetry written to `.mekong/telemetry/execution_trace.json`.

**Memory recording:** `MemoryStore.record(MemoryEntry{goal, status, duration_ms, error_summary, recipe_used})` after each `run_from_goal`.

**Progress callback:** Used by WebSocket endpoint — called after each step with `StepResult` + running `OrchestrationResult`.

---

## 6. Memory & Telemetry

**MemoryStore:**
- Primary: YAML at `.mekong/memory.yaml`, max 500 entries (FIFO eviction)
- Optional mirror: `packages.memory.memory_facade` → Mem0/Qdrant vector backend
- `query()`: vector semantic search if available, substring fallback
- `suggest_fix()`: summarizes last 5 failure error_summaries

**Telemetry:**
- `TelemetryCollector`: single JSON trace to `.mekong/telemetry/execution_trace.json`
- `TieredTelemetryStore`: 3-tier Netdata-inspired storage (14/90/365 days)
- Dual-write to Langfuse (`packages.observability.observability_facade`) if installed

---

## 7. Gateway (FastAPI)

**Endpoints summary:**
- `POST /cmd` — sync PEV execution (token auth via `MEKONG_API_TOKEN`)
- `WS /ws` — streaming PEV via WebSocket + `asyncio.to_thread()`
- `POST /nlu/parse`, `/recipes/generate|validate|auto`
- `/swarm/*`, `/schedule/*`, `/memory/*`
- `/governance/check|audit`, `/autonomous/consciousness`, `POST /halt`
- `/api/agi/health|metrics` — proxy to Tôm Hùm port 9090

**Dashboard:** HTML served at `/` — "Washing Machine" one-button UI, presets from `gateway_config.json`.

**Human summary:** Bilingual EN/VI `HumanSummary` attached to all command responses.

---

## 8. CLI Commands (Typer)

| Command | Action |
|---------|--------|
| `mekong cook <goal>` | Full PEV pipeline |
| `mekong plan <goal>` | Plan-only, display table |
| `mekong run <recipe.md>` | Execute existing recipe |
| `mekong debug <issue>` | Defaults dry-run, `--execute` runs |
| `mekong ask <question>` | Plan alias |
| `mekong gateway` | Start FastAPI server |
| `mekong dash` | Interactive one-button menu |
| `mekong evolve` | Self-improvement cycle |
| `mekong halt` / `autonomous resume` | Governance control |
| `mekong swarm *` | Multi-node orchestration |
| `mekong schedule *` | Cron-style recurring goals |
| `mekong memory *` | Execution history |

---

## 9. Dependencies (pyproject.toml)

- **Runtime core:** typer 0.9, rich 13.7, fastapi 0.109, uvicorn, pydantic 2.5, requests 2.31, httpx
- **Optional:** google-generativeai (Gemini), python-telegram-bot, mem0/qdrant (vector), langfuse (observability)
- **Python requirement:** `^3.9` (README says 3.11+, pyproject says 3.9 — minor discrepancy)
- **Dev:** pytest 7.4, pytest-asyncio, pytest-cov, black, ruff, mypy, httpx

**Test suite:** 113 test files across `tests/`, `tests/backend/`, `tests/integration/`, `tests/e2e/`. Core tests: `test_agent_orchestrator.py`, `test_agent_chains.py`, `test_agent_memory.py`.

---

## 10. DNA — What to Keep vs Refactor for Open Source

**Keep (core DNA):**
- PEV triadic pattern: `planner → orchestrator → verifier` separation is clean
- `AgentBase` abstract class: simple, extensible, 3-method contract
- `ExecutionResult` dataclass: lingua franca across executor/verifier/orchestrator
- `RecipeParser`: Markdown-as-recipe format is unique and portable
- `LLMClient` multi-provider + circuit breaker + LRU cache
- `VerificationCriteria` with custom shell checks: powerful extensibility

**Refactor for open source:**
- `LeadHunter`, `ContentWriter`, `RecipeCrawler` — all simulated; mark as examples or implement with real APIs
- `gateway.py` — 740 lines, too large. Split: auth, routes, swarm, schedule into separate routers
- `main.py` — 1187 lines, violates 200-line rule. Extract sub-app groups to `src/cli/`
- Rename `AGENT_KEYWORDS` snake_case keyword lists — use more structured routing config
- `RecipeParser.parse_frontmatter` — naive `split(":")` breaks on values with colons; use `yaml.safe_load`
- Version string mismatch: `main.py` says `v1.0.0`, pyproject says `2.2.0`, README badge says `v2.2.0`
- `FileAgent.file_stats` uses `rglob` over entire repo — slow (~2.5min noted in memory); needs depth limit

---

## Unresolved Questions

1. `packages/memory/memory_facade.py` and `packages/observability/` — are these internal packages shipped with mekong-cli or external? Not confirmed from codebase scan.
2. `RetryPolicy.is_retryable()` and `WorkflowState` — not read; behavior of retry gate for self-healing unknown beyond signature.
3. `SmartRouter.route()` — recipe path resolution logic not analyzed; unclear if it uses fuzzy matching or exact NLU intent→recipe mapping.
4. `src/core/governance.py` — action classification (ALLOW/BLOCK/REQUIRE_APPROVAL) not analyzed; autonomy safety posture unknown.
5. Test coverage % — 113 test files exist but no `--cov` report seen; actual coverage for core PEV loop unverified.
