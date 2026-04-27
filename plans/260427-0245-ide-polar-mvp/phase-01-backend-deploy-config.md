# Phase 01: Backend Gateway Deploy

**Priority:** P0 — Blocking everything
**Status:** ☐ Pending
**Effort:** 1-2 ngày

## Context Links

- `src/gateway.py` — FastAPI gateway entry (port 8000 default)
- `src/api/polar_webhook.py` — Webhook receiver (367 lines)
- `src/api/gateway_mission_routes.py` — `/v1/missions` POST endpoint
- `apps/ide-ui/wrangler.toml` — existing CF Worker config (frontend only)

## Overview

`api.mekong.dev` HTTP 000 — không có endpoint công khai. Polar không thể gửi webhook, IDE không thể submit mission. Phase này deploy `src/gateway.py` lên Cloudflare Workers (hoặc Fly.io fallback) với public URL.

## Key Insights

- FastAPI app runs on uvicorn — không thể chạy trực tiếp CF Worker Python (Workers Python beta hạn chế).
- Hai option:
  - **A. CF Worker + Pyodide** — experimental, ~50MB cold start, không khuyến nghị MVP.
  - **B. Fly.io** — full Python runtime, free tier 256MB, cold start ~2s. Khuyến nghị.
- Polar webhook chỉ cần HTTP 200 trong 30s → Fly.io thoả.
- Mission stream (SSE) cần persistent connection → Fly.io tốt hơn Workers.

**Quyết định MVP:** Fly.io.

## Requirements

### Functional
- Public URL `api.mekong.dev` resolve HTTP 200 ở `/healthz`
- POST `/webhook/polar` accept Polar HMAC-signed body, trả 200 nếu signature valid
- POST `/v1/missions` create mission, GET `/v1/missions/{id}/stream` SSE
- CORS allow `https://ide.mekongmind.com` + `https://www.mekongmind.com`
- All env vars loaded from Fly.io secrets (không hardcode)

### Non-Functional
- Cold start < 5s
- Healthcheck endpoint cho Fly.io scaler
- Structured JSON logs to stderr (Fly.io aggregates)
- Graceful shutdown trên SIGTERM (in-flight missions complete)

## Architecture

```
Polar.sh ──HMAC POST──► api.mekong.dev/webhook/polar
                              │
                              ▼ Fly.io us-west-1
                       ┌──────────────┐
                       │ src/gateway  │  uvicorn :8000
                       │ (FastAPI)    │
                       └──────┬───────┘
                              │
ide.mekongmind.com ──fetch──► /v1/missions (POST)
                       └─SSE──► /v1/missions/{id}/stream
```

## Related Code Files

### Modify
- `src/gateway.py` — add `/healthz` endpoint, ensure CORS origins from env
- `pyproject.toml` — verify all runtime deps in `[tool.poetry.dependencies]` (not just dev)

### Create
- `fly.toml` (root) — Fly.io app config
- `Dockerfile` (root) — Python 3.11 slim + uvicorn + src/
- `.dockerignore` — exclude `.venv/`, `__pycache__/`, `tests/`, `apps/`, `mekong/daemon/`
- `.github/workflows/deploy-gateway.yml` — push main → fly deploy

### Delete
- None

## Implementation Steps

1. **Dockerfile** — multi-stage build, install poetry deps, copy `src/`, expose 8000.
2. **fly.toml** — app `mekong-gateway`, primary region `sjc`, internal port 8000, healthcheck `/healthz`.
3. **`/healthz` endpoint** — return `{"status": "ok", "version": "6.0.0"}`. Add to `src/gateway.py`.
4. **CORS env** — `CORS_ORIGINS` comma-separated env var, default to current hardcoded list.
5. **Fly secrets** — `flyctl secrets set JWT_SECRET=REDACTED=... POLAR_WEBHOOK_SECRET=... DATABASE_URL=...`.
6. **DNS** — CNAME `api.mekong.dev` → `mekong-gateway.fly.dev`. Verify TLS auto-provisioned.
7. **GitHub Actions** — workflow runs on push to `main`, calls `flyctl deploy --remote-only` with `FLY_API_TOKEN` secret.
8. **Smoke test** — `curl https://api.mekong.dev/healthz` returns 200.

## Todo List

- [ ] Write `Dockerfile` (multi-stage, ~50MB final)
- [ ] Write `fly.toml` (region sjc, healthcheck, autoscale=1)
- [ ] Add `/healthz` endpoint to `src/gateway.py`
- [ ] Refactor CORS origins to env var
- [ ] Test Docker build locally — `docker build -t test .`
- [ ] Fly.io account: create app `mekong-gateway`
- [ ] Set Fly secrets (JWT_SECRET=REDACTED, POLAR_WEBHOOK_SECRET, etc.)
- [ ] Configure DNS CNAME for `api.mekong.dev`
- [ ] Deploy: `flyctl deploy`
- [ ] Verify `curl https://api.mekong.dev/healthz` → 200
- [ ] Add `.github/workflows/deploy-gateway.yml`
- [ ] Test push-to-deploy by trivial commit

## Success Criteria

- `curl https://api.mekong.dev/healthz` → HTTP 200, JSON body
- `curl -X POST https://api.mekong.dev/webhook/polar` returns 401 (signature missing) — proves endpoint reachable
- GH Actions workflow runs green on push to `main`
- Cold start < 5s (measured via fly logs)

## Risk Assessment

| Risk | Likelihood | Mitigation |
|---|---|---|
| Fly.io free tier limits | Med | Track usage; upgrade if revenue justifies |
| Docker image > 200MB | Low | Multi-stage build, only `src/` not full repo |
| DNS propagation delay | High | Allow 1-2h after CNAME set; use Fly direct URL during testing |
| Secrets leak via logs | Med | Code review for `print(env)` patterns; use `os.getenv` not f-string |

## Security Considerations

- HTTPS only (Fly auto-TLS)
- Secrets never in repo (`.env` gitignored, Fly.io secrets API)
- CORS allowlist strict — no `*` origin
- Rate limit POST `/v1/missions` (existing middleware in `src/middleware/`)

## Next Steps

- Phase 02 (Polar dashboard setup) can begin in parallel — independent of deploy.
- Phase 03 (license gating) blocks until Phase 01 + 02 done.
