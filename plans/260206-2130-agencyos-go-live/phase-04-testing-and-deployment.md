# Phase 4: Testing & Deployment

## Context
Final quality assurance and deployment orchestration before Go-Live.

## Testing Strategy

### 1. Unit & Integration Tests
- [ ] **Engine (Node):**
    - Run `npm test` in `apps/engine` and `apps/worker`.
    - Ensure 100% pass rate.
- [ ] **API (Python):**
    - Run `pytest` in `tests/`.
    - Specifically `tests/test_content_writer.py`, `tests/test_lead_hunter.py`.

### 2. End-to-End Test
- [ ] Create a `tests/e2e` script that:
    1.  Uses `mekong` CLI to submit a task.
    2.  Verifies the task reaches the Engine API.
    3.  Verifies the Worker processes it.
    4.  Verifies the result is returned to the CLI.

## Deployment Orchestration

### 1. Docker Builds
- [ ] Build Engine: `docker build -t agency-engine apps/engine`.
- [ ] Build Worker: `docker build -t agency-worker apps/worker`.
- [ ] Verify image sizes and security (trivy scan).

### 2. Docker Compose Environment
- [ ] Configure `infrastructure/.env.prod`.
- [ ] Run `docker-compose -f infrastructure/docker-compose.yml up -d`.
- [ ] Verify Healthchecks:
    - Redis: `docker inspect --format='{{json .State.Health}}' agency_redis`.
    - Postgres: `docker inspect --format='{{json .State.Health}}' agency_postgres`.

### 3. Tunneling (Cloudflare)
- [ ] Verify `tunnel` service in docker-compose.
- [ ] Ensure `TUNNEL_TOKEN` is set.
- [ ] Verify public URL accessibility.
