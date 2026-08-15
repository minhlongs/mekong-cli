# agent-forest — Phase 2 Forest (Rừng)

Multi-tenant orchestration on top of [`agent-core`](../agent-core): FastAPI gateway +
Redis task queue + worker pool that dispatches CEO/Developer agents through
[`mekongd`](../mekongd).

Each request from an authenticated user is enqueued, picked up by a worker, and executed
with `AGENT_CORE_OUTPUTS` pinned to `outputs/{user_id}/` so artifacts stay tenant-scoped.

## Install

```bash
cd packages/agent-forest
poetry install
```

## Env

| Var | Required | Default | Purpose |
|-----|----------|---------|---------|
| `JWT_SECRET_KEY` | yes (unless `FOREST_TESTING=1`) | – | HS256 signing key |
| `REDIS_URL` | no | `redis://localhost:6379` | Broker |
| `FOREST_OUTPUTS` | no | `./outputs` | Sandbox root |
| `FOREST_USERS_YAML` | no | built-in `founder1/founder2` | YAML-backed user list (legacy) |
| `FOREST_DB_PATH` | no | unset (YAML path active) | SQLite-backed user store (Giai đoạn 3.1) |
| `FOREST_FEEDBACK_ROUNDS` | no | `1` | Self-heal rounds (`>=2` → full loop) |
| `FOREST_RATE_LIMIT_PER_MINUTE` | no | `60` | Per-bearer rate cap |
| `FOREST_WEBHOOK_TIMEOUT` | no | `5` | POST timeout (s) |
| `FOREST_WORKER_EXECUTOR` | no | `subprocess` | `subprocess` \| `docker` |
| `FOREST_SIGNALS_ENABLED` | no | `1` | Set `0` to disable worker→mekongd signal emission |
| `MEKONGD_URL` | no | `http://127.0.0.1:8765` | Inherited by agent-core + signals target |

## Quickstart

Two terminals:

```bash
# terminal 1 — gateway
export JWT_SECRET_KEY=$(openssl rand -hex 32)
poetry run agent-forest gateway

# terminal 2 — worker
export JWT_SECRET_KEY=$JWT_SECRET_KEY
poetry run agent-forest worker
```

Then:

```bash
curl -s localhost:8000/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"founder1","password":"founder1-dev"}'
# → {"access_token":"...","token_type":"bearer"}

curl -s localhost:8000/task \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"Write hello.txt saying Hi from forest"}'
```

## Auth backends

Two user stores ship in-tree; pick via env:

| Backend | Activate via | Register users via | Notes |
|---------|-------------|--------------------|-------|
| YAML (legacy) | `FOREST_USERS_YAML=/path/users.yaml` *or* unset | Edit YAML by hand | Good for dev / CI seeds |
| SQLite | `FOREST_DB_PATH=/var/lib/forest/users.db` | `agent-forest register-user` CLI *or* `POST /auth/register` | Giai đoạn 3.1 — runtime signup |

### Bootstrap SQLite users

```bash
export FOREST_DB_PATH=./data/users.db

# Interactive (typer prompts + hides input)
poetry run agent-forest register-user alice

# Non-interactive (CI scripts)
poetry run agent-forest register-user bob --password "$PWD_FROM_SECRET_MANAGER"
```

### HTTP signup (when SQLite backend active)

```bash
curl -s localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"newfounder","password":"min-8-chars"}'
# → 201 {"access_token":"...", "token_type":"bearer"}
```

On the YAML backend, `/auth/register` returns **501 Not Implemented**.

### Migrating YAML → SQLite

1. Set `FOREST_DB_PATH` and restart gateway + worker.
2. Re-create each existing YAML user via `agent-forest register-user`.
3. Delete `FOREST_USERS_YAML` env and the YAML file.

(No automated migration script — the two stores are intentionally independent.)

## Ops endpoints

- `GET /healthz` — `{"status":"ok","service":"agent-forest"}`
- `GET /status` — JSON snapshot consumed by `agent-core forest-status`
- `GET /metrics` — Prometheus text exposition (queue depth, workers alive, last heartbeat)

Inspect from CLI:

```bash
agent-core forest-status --url http://localhost:8000
agent-core forest-status --url http://localhost:8000 --json  # for scripts
```

## Feedback signals (Giai đoạn 3.2)

**3.2.A — Worker auto-emit.** Every completed job emits a `good` / `bad`
signal to `mekongd /v1/signals` with note prefix `forest/{user_id}/{job_id}`.
Closes Pillar 3 (Feedback Loop) at the multi-tenant layer.

**3.2.B — User feedback endpoint.**

```bash
curl -s -X POST localhost:8000/task/$JOB_ID/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"rating":"good","note":"output was spot-on"}'
# → 202 {"job_id":"job_...","rating":"good","forwarded":true}
```

The rating is forwarded as a mekongd signal with note suffix `#user` so
operator dashboards can distinguish user-driven from worker-auto signals.
Owner-only: 404 when the job is missing or belongs to another user.

- Transport is best-effort — mekongd outages never fail user requests.
- Disable worker auto-emit with `FOREST_SIGNALS_ENABLED=0` (user endpoint
  still stores the rating).
- Inspect with `agent-core report --hours 1` or `/v1/signals/recent`.

## Security — prompt_guard (Giai đoạn 4.4.1)

Server-side first-line defense on `POST /task` — regex-only, no LLM round-trip, no network. Rejects with HTTP 400.

- **24 patterns** in `agent_forest.gateway.prompt_guard`:
  - 13 injection: `ignore previous instructions`, `forget everything`, `<|im_start|>`, `you are now`, `sudo`, `<script`, `javascript:`, etc.
  - 14 dangerous-code: `rm -rf`, `DROP TABLE`, `eval(`, `os.system`, `subprocess.`, `passthru(`, `fs.unlink`, `fs.rmdir`, etc.
- **`sanitize_input`** strips NUL + control chars, caps at 10k (Pydantic rejects >8k first).
- **Observability loop:**
  - Counter `agent_forest_prompt_guard_rejections_total{reason="injection"|"dangerous"}` on `/metrics`
  - Alert `AgentForestPromptGuardSurge` fires at `> 0.1 rej/s` for 5m (warning)
  - Grafana panel (id=12) splits rate by reason label, thresholds match alert
- **Tier-2 LLM guard (Llama-Guard) deferred per YAGNI** — server regex is cheap first line, real defense is worker-sandbox (Firecracker/gVisor).

## Deviations from DeepSeek blueprint

- **No Docker-in-Docker by default.** Per-user isolation is path-based (`outputs/{user_id}/`)
  with a subprocess sandbox. Set `FOREST_WORKER_EXECUTOR=docker` to enable DinD.
- **Single-attempt webhooks.** No retry; timeout enforced.
- **No Temporal supervisor yet.** Workflow durability relies on Redis + webhook callback.
- **Giai đoạn 4.4.1 complete** (prompt_guard above). 4.4.2/4.4.3 Firecracker+gVisor sandbox deferred — require host VM binaries.

## Tests

```bash
FOREST_TESTING=1 poetry run pytest
```

Uses `fakeredis` — no daemon needed. Gateway tests hit `TestClient`.
