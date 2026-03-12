# Deployment Operations — Mekong CLI v5.0.0
**Date:** 2026-03-11 | **Commands covered:** deploy, deploy-staging, deploy-prod, devops-deploy-pipeline, devops-rollback

---

## Infrastructure Summary

| Layer | Platform | Trigger | Workflow |
|-------|----------|---------|---------|
| Landing (frontend) | Cloudflare Pages | `git push main` (paths: `frontend/landing/**`) | `deploy-landing.yml` |
| Mekong Engine (API) | Cloudflare Workers | `git push main` (paths: `packages/mekong-engine/**`) | `deploy-cloudflare.yml` |
| Backend API | Fly.io (`agencyos-gateway`) | `fly deploy` or Docker | `fly.toml` |
| Python CLI | PyPI | GitHub Release published | `publish-pypi.yml` |
| NPM Packages | npmjs.org | GitHub Release published | `publish-packages.yml` |

All deploys via `git push` only. Direct `vercel --prod` or manual Fly push without CI are discouraged.

---

## Deploy Pipelines

### 1. Cloudflare Pages — Landing (`deploy-landing.yml`)

```
git push main (frontend/landing/** changed)
         │
         ▼
GH Actions: ubuntu-latest, Node 22
  → npm ci
  → npm run build
  → wrangler pages deploy frontend/landing/out
    --project-name=agencyos-landing
```

**Secrets required:**
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

**No staging step** — deploys directly to production Pages project.

---

### 2. Cloudflare Workers — Mekong Engine (`deploy-cloudflare.yml`)

```
git push main (packages/mekong-engine/** changed)
         │
         ▼
Job: test-engine
  → pnpm install
  → tsc --noEmit       (continue-on-error)
  → vitest run         (continue-on-error)
         │
         ▼
Job: deploy (needs: test-engine)
  → pnpm install
  → wrangler deploy    (via cloudflare/wrangler-action@v3)
         │
         ▼
Smoke test (if deploy succeeded):
  → sleep 10
  → curl GET /health → expect HTTP 200
  → logs result (non-blocking if custom domain not set)
```

**Secrets required:**
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

**Note:** TypeScript check and tests both `continue-on-error: true` — deploy proceeds even on failures.

---

### 3. Fly.io — Backend API

**Config: `fly.toml`**
```toml
app = "agencyos-gateway"
primary_region = "sin"           # Singapore

[build]
  dockerfile = "Dockerfile"      # python:3.12-slim

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"
  auto_start_machines = true
  min_machines_running = 1

[[vm]]
  memory = "512mb"
  cpu_kind = "shared"
  cpus = 1

[mounts]
  source = "agencyos_data"
  destination = "/data"           # SQLite persistence
```

**Dockerfile HEALTHCHECK:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

**Deploy commands:**
```bash
# Deploy current code
fly deploy -a agencyos-gateway

# Deploy with specific image
fly deploy --image registry.fly.io/agencyos-gateway:<tag>

# Scale machines
fly scale count 1 -a agencyos-gateway

# View status
fly status -a agencyos-gateway

# Stream logs
fly logs -a agencyos-gateway
```

---

### 4. PyPI Release (`publish-pypi.yml`)

```
GitHub Release published
         │
         ▼
GH Actions: Python 3.11, Poetry
  → pip install poetry
  → poetry build
  → poetry publish
    (POETRY_PYPI_TOKEN_PYPI from secret)
```

---

### 5. NPM Release (`publish-packages.yml`)

```
GitHub Release published (or workflow_dispatch)
         │
         ▼
Matrix: [core, agents]
  → npm publish --provenance --access public
    (NODE_AUTH_TOKEN from secret)

Guard job: confirms only packages/core + packages/agents published
  (apps/openclaw-worker and antigravity-proxy NEVER published)
```

---

## Infrastructure Scaffold

New projects provisioned via:
```bash
# Frontend only (solo/side project)
bash mekong/infra/scaffold.sh myproject solo

# Frontend + edge API (startup MVP)
bash mekong/infra/scaffold.sh myproject startup

# Full stack (frontend + edge API + backend Workers)
bash mekong/infra/scaffold.sh myproject scale
```

Copies templates from `mekong/infra/templates/`:
- `cf-pages/` → static site with `wrangler.toml`
- `cf-workers/` → serverless API with `wrangler.toml`

Substitutes `{{PROJECT_NAME}}` throughout config files.

---

## Rollback Procedures

### CF Workers Rollback
```bash
# List deployments
wrangler deployments list --name mekong-engine

# Roll back to previous
wrangler rollback [deployment-id] --name mekong-engine
```

### CF Pages Rollback
```bash
# Via dashboard: Pages → Project → Deployments → select → Rollback
# Or force via git:
git revert HEAD
git push origin main
```

### Fly.io Rollback
```bash
# View release history
fly releases -a agencyos-gateway

# Roll back to specific version
fly deploy --image registry.fly.io/agencyos-gateway:<previous-tag>

# Emergency: cycle machines
fly scale count 0 -a agencyos-gateway
fly scale count 1 -a agencyos-gateway
```

### Application-Level Rollback (PEV Orchestrator)
The orchestrator (`src/core/orchestrator.py`) has built-in rollback:
- Reverses completed steps via `step.params.rollback` on verification failure
- CLI flags: `mekong cook --strict` (enforce), `mekong cook --no-rollback` (disable)
- Rollback sequence: reverse order of completed steps

---

## Deploy Checklist

### Pre-Deploy
- [ ] `make test` passes locally
- [ ] `make lint` clean
- [ ] No `.env` files staged: `git status | grep ".env"`
- [ ] `VERSION` file updated if releasing
- [ ] `CHANGELOG.md` updated

### Deploy (CF Pages / Workers)
```bash
git add -p          # stage specific changes only
git commit -m "feat/fix/chore: description"
git push origin main
# → GH Actions triggers automatically
```

### Post-Deploy Verification
```bash
# 1. Watch CI
gh run list -L 3 --json status,conclusion,name

# 2. CF Workers smoke test
curl -sI https://mekong-engine.<account>.workers.dev/health

# 3. Fly.io health
fly status -a agencyos-gateway
curl -sI https://agencyos-gateway.fly.dev/health

# 4. Full report format
echo "Deploy: ✅ | CI: ✅/❌ | CF Workers: HTTP [x] | Fly: HTTP [x]"
```

---

## Staging vs Production

| Environment | Platform | How to Deploy |
|-------------|----------|--------------|
| Local dev | `uvicorn` port 8000 | `make server` |
| CF Preview | CF Pages (branch) | `git push <branch>` (auto-preview URL) |
| Production (CF) | CF Pages + Workers main | `git push main` |
| Production (Fly) | `agencyos-gateway` | `fly deploy` |

**No explicit staging environment** for Fly.io — gap identified. Recommend creating `agencyos-gateway-staging` app on Fly for pre-prod validation.

---

## Security Gates in Deploy Pipeline

1. `security-hardening.yml` runs on every push (parallel to deploy):
   - Secret scanning via truffleHog
   - Pattern-based hardcoded secret detection
   - Command injection scan
2. `ci.yml` security job: Bandit SAST + Safety dependency check
3. `publish-packages.yml` guard: blocks proprietary package publishing

---

## Issues & Gaps

| Gap | Severity | Recommendation |
|-----|----------|---------------|
| `continue-on-error` on tests/typecheck before deploy | HIGH | Remove for CF Workers; block deploys on test failure |
| No staging Fly app | MEDIUM | Create `agencyos-gateway-staging`, deploy from `develop` branch |
| CF Pages has no staging step | LOW | Use branch previews (already auto-created by CF) |
| No deploy notification | LOW | Add Telegram/Discord webhook on deploy success/failure |
| Fly deploy not in GH Actions | MEDIUM | Add `fly-deploy.yml` workflow triggered on main push |

---

## Deploy Score: 7/10

Solid GitOps foundation with automated CF Pages + Workers deploys and smoke tests. Gaps: no staging for Fly backend, soft failures in pre-deploy tests, and no deploy notifications.
