# Deployment Guide — Mekong CLI

**Date:** 2026-03-11
**Scope:** CF Workers + CF Pages + GitHub Actions pipelines

---

## 1. Deployment Architecture

```
git push → GitHub Actions → multiple parallel deploy jobs
    │
    ├── ci.yml         — Backend (Python) + Frontend (Landing) + Security
    ├── deploy-cloudflare.yml  — Mekong Engine → CF Workers
    ├── deploy-landing.yml     — Landing page → CF Pages
    └── publish-pypi.yml       — Python package → PyPI
```

All deploys gated on `main` / `master` branch. No direct deploy commands — git push only.

---

## 2. Environments

| Layer | Platform | Trigger | URL Pattern |
|-------|----------|---------|-------------|
| CF Workers (Engine) | Cloudflare Workers | push to main (packages/mekong-engine/**) | mekong-engine.*.workers.dev |
| CF Pages (Landing) | Cloudflare Pages | push to main (frontend/landing/**) | agencyos.network |
| RaaS Gateway | Cloudflare Workers | `wrangler deploy` from apps/raas-gateway/ | raas.agencyos.network |
| PyPI Package | PyPI | tag push | pip install mekong-cli |

No staging environment explicitly defined in workflows. Deploy is straight to production on merge to main.

---

## 3. CI/CD Pipeline: ci.yml

### Job 1: Backend (Python)
```yaml
python-version: "3.12"
steps:
  1. pip install -r requirements.txt + ruff + pytest + httpx + pytest-cov
  2. pip install -e .
  3. mekong --help  (verify CLI entry point, continue-on-error)
  4. ruff check src/ tests/  (lint — blocking)
  5. ruff format --check  (format — continue-on-error)
  6. pytest tests/ --ignore=e2e,integration,unit,benchmarks,backend
     --cov=src --cov-fail-under=80  (continue-on-error, so non-blocking)
```

### Job 2: AGI Benchmarks
```yaml
needs: backend
python-version: "3.12"
pytest tests/benchmarks/test_agi_tasks.py -v --tb=short
```

### Job 3: Security Audit
```yaml
tools: bandit + safety
bandit -r src/ -ll --exit-zero     (never fails build)
safety check -r requirements.txt --ignore 70612  (never fails build)
grep for hardcoded secrets (exits 1 if found)
```

### Job 4: Frontend (Landing)
```yaml
node: 22
cd frontend/landing && npm ci && npm run build
```

---

## 4. Cloudflare Workers Deploy: deploy-cloudflare.yml

```yaml
trigger: push to main, paths: packages/mekong-engine/**
jobs:
  test-engine:
    - pnpm install
    - npx tsc --noEmit  (continue-on-error)
    - npx vitest run    (continue-on-error)

  deploy:
    needs: test-engine
    if: github.ref == refs/heads/main
    - cloudflare/wrangler-action@v3
      workingDirectory: packages/mekong-engine
      command: deploy
    - smoke test: curl health endpoint (HTTP 200 check)
```

Secrets required: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`

---

## 5. RaaS Gateway Deploy (Manual via Wrangler)

The `apps/raas-gateway/` Cloudflare Worker is deployed manually (not via CI):

```bash
# From apps/raas-gateway/
cd apps/raas-gateway
wrangler deploy

# Local dev
wrangler dev

# Required secrets (set via Cloudflare dashboard or wrangler CLI)
wrangler secret put SERVICE_TOKEN
wrangler secret put BRIDGE_URL
wrangler secret put TELEGRAM_BOT_TOKEN
```

No automated CI/CD for gateway — deploy is developer-triggered.

---

## 6. Python Package: publish-pypi.yml

```yaml
trigger: tag push (v*.*.*)
steps:
  - python -m build
  - twine upload dist/*
secrets: PYPI_TOKEN
```

---

## 7. Required GitHub Secrets

| Secret | Used In | Purpose |
|--------|---------|---------|
| CLOUDFLARE_API_TOKEN | deploy-cloudflare.yml | Wrangler deploy auth |
| CLOUDFLARE_ACCOUNT_ID | deploy-cloudflare.yml | CF account routing |
| PYPI_TOKEN | publish-pypi.yml | PyPI upload auth |
| TELEGRAM_BOT_TOKEN | wrangler secret | Gateway Telegram auth |
| SERVICE_TOKEN | wrangler secret | Gateway → engine auth |

---

## 8. Health Check URLs

| Service | Health Endpoint |
|---------|----------------|
| CF Worker (Engine) | `GET /health` → HTTP 200 |
| RaaS Gateway | `GET /health` → `{"status":"ok","version":"2.0.0"}` |
| Local Orchestrator | `http://127.0.0.1:9192/health` |

Smoke test in `deploy-cloudflare.yml` polls health endpoint after deploy with 10s delay.

---

## 9. Rollback Procedure

No automated rollback configured. Manual rollback options:

**Cloudflare Workers:**
```bash
# List recent deployments
wrangler deployments list

# Rollback to specific deployment
wrangler rollback <deployment-id>
```

**Git revert:**
```bash
git revert HEAD
git push origin main
# Triggers new CI/CD pipeline → redeploy previous code
```

**PyPI:** Cannot unpublish. Pin version in requirements.txt to last known good.

---

## 10. Pre-Deploy Checklist

Before merging to main:
- [ ] `python3 -m pytest tests/ -q --tb=short` — all pass locally
- [ ] `ruff check src/ tests/` — no errors
- [ ] `python3 -m py_compile src/core/*.py` — no compile errors
- [ ] No `.env` files staged (`git status`)
- [ ] No hardcoded secrets in diff (`git diff HEAD`)
- [ ] CF Workers: `wrangler dev` tested locally if gateway changed
- [ ] Version bump in `setup.py` / `pyproject.toml` if releasing to PyPI

---

## 11. Known Deploy Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| No staging environment | HIGH | Test on separate CF subdomain |
| Security job is continue-on-error | MEDIUM | Make secret scan blocking |
| RaaS Gateway deploy is manual | MEDIUM | Add to CI/CD |
| pytest --cov-fail-under=80 non-blocking | MEDIUM | Make blocking at lower threshold |
| No DB migration step in pipeline | LOW | CLI has no DB (stateless) |
