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
| `FOREST_USERS_YAML` | no | built-in `founder1/founder2` | User list |
| `FOREST_RATE_LIMIT_PER_MINUTE` | no | `60` | Per-bearer rate cap |
| `FOREST_WEBHOOK_TIMEOUT` | no | `5` | POST timeout (s) |
| `MEKONGD_URL` | no | `http://127.0.0.1:8765` | Inherited by agent-core |

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

## Deviations from DeepSeek blueprint

- **No Docker-in-Docker.** Per-user isolation is path-based (`outputs/{user_id}/`)
  with a subprocess sandbox. Docker isolation deferred to Phase 3.
- **Mock users via YAML.** Postgres-backed auth lands in Phase 3 (Đất).
- **Single-attempt webhooks.** No retry; timeout enforced.

## Tests

```bash
FOREST_TESTING=1 poetry run pytest
```

Uses `fakeredis` — no daemon needed. Gateway tests hit `TestClient`.
