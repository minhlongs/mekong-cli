# agent-core

Seed-phase agent kernel for the Mekong solo-platform.

Provides a minimal, dogfoodable BaseAgent with persistent memory (SQLite +
optional ChromaDB vector store), an LLM client that speaks Anthropic-compat
Messages API against `mekongd` (see `../mekongd/`), and a small tool registry
(browser, file_system, execute).

Maps to Phase 1 ("Hạt giống") + Phase 2 ("Feedback loop & retention") of the
DeepSeek solo-platform design. Forest / multi-tenant primitives (gateway,
worker pool, per-user isolation) live in `../agent-forest/`.

## Install

```bash
cd packages/agent-core
poetry install                  # core only (SQLite memory)
poetry install --with vector    # adds ChromaDB for semantic recall
```

## Quickstart

```bash
# 1. mekongd must be running (see packages/mekongd/README.md)
export MEKONGD_URL=http://127.0.0.1:8765

# 2. Ask the CEO agent to plan + Developer to execute
poetry run agent-core run "Tạo một landing page giới thiệu dịch vụ AI consulting"
```

Outputs land in `./outputs/`. Memory lives in `~/.agent-core/`.

## CLI reference

| Command | Purpose |
|---------|---------|
| `run "<goal>"` | CEO plans, Developer executes the first step. Single-pass. |
| `orchestrate "<goal>" -r N` | Full pipeline CEO → Dev → Tester → Reviewer. `N >= 2` enables Ops + Analyst + bounded feedback retry. |
| `report` | Signal breakdown by model (good/bad ratio). `--cost` adds cloud spend. `--hours N` windows. `--notes N` appends recent note tail. |
| `signal good\|bad [note]` | Send Pillar 3 feedback signal to mekongd. |
| `history [--limit N] [--json]` | Inspect persisted FeedbackSession rounds (table or JSON). |
| `prune --keep N [--all]` | Delete old memory rows, keep newest N. Default targets `feedback_session`; `--all` covers every agent_id. |
| `status [--json]` | Snapshot: memory root, retention config, last round, rows per agent_id. |
| `forest-status --url URL [--json]` | Query `agent-forest` gateway `/healthz` + `/metrics`; print queue depth, workers alive, last heartbeat. |
| `eval --dataset PATH [--offline] [--json]` | Offline-eval harness (Giai đoạn 3.3.A). Exits 1 on ≥5% regression vs baseline. |
| `experiment --user ID --name NAME [--variants X,Y] [--json]` | A/B hash-bucket assignment (Giai đoạn 3.4.B Statsig-style). |
| `doctor [--mekongd-url URL] [--forest-url URL] [--json]` | Holistic triage: env + memory + connectivity + package versions. Best-effort exit 0. |

## Environment variables

| Variable | Purpose |
|----------|---------|
| `MEKONGD_URL` | Anthropic-compat LLM backend base URL. |
| `AGENT_CORE_OUTPUTS` | Sandbox dir for artifact writes (default `./outputs`). |
| `AGENT_CORE_PROMPT_SIGNAL` | `1` to auto-prompt good/bad after `run`. Also triggered by `--signal` flag. |
| `AGENT_CORE_SESSION_RETENTION` | If set to `>=1`, auto-prune `feedback_session` after each `orchestrate` run. Default `0` = unbounded. |

## Self-heal feedback loop

`orchestrate -r N` (for `N >= 2`) wraps the pipeline with `FeedbackLoop`:

1. CEO → Developer → Tester → Reviewer (produces `PipelineReport`).
2. OpsAgent rates health (`info` / `warn` / `critical`).
3. AnalystAgent reads prior sessions from SeedMemory + current round → `{summary, recommendations, trend}`.
4. Retry if Reviewer says `revise`/`block`, OR tests fail, OR Ops is `warn`/`critical`. Analyst's recommendations are appended to the goal for the next round.
5. Bounded by `N`; each round persisted into `feedback_session` memory.

## Layout

```
src/agent_core/
├── memory.py         # SQLite + (optional) ChromaDB; prune + counts helpers
├── llm_client.py     # Anthropic-compat client for mekongd
├── base_agent.py     # think → act → observe loop
├── orchestrator.py   # CEO → Dev → Tester → Reviewer
├── feedback_loop.py  # + Ops + Analyst + bounded retry + session persist
├── forest_client.py  # httpx client for agent-forest /healthz + /metrics
├── formatters.py     # CLI table formatters
├── cli.py            # typer entry point (11 commands)
├── evals.py          # offline-eval harness (run + regression detection)
├── experiments.py    # SHA-256 hash-based A/B bucket assignment
├── agents/
│   ├── ceo.py
│   ├── developer.py
│   ├── tester.py
│   ├── reviewer.py
│   ├── ops.py
│   ├── analyst.py
│   └── tool_agent.py
└── tools/
    ├── browser.py
    ├── file_system.py
    └── execute.py
```
