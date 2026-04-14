# Cloudflare Workers Deployment Pipeline Audit

**Report ID:** scout-cf-workers-260319-0049
**Date:** 2026-03-19
**Scope:** wrangler.toml, build configs, publish workflows

---

## Executive Summary

| Component | Status | Issues |
|-----------|--------|--------|
| wrangler.toml configs | ✅ Configured | Minor: inconsistent compatibility_date |
| Build scripts | ✅ Configured | All packages have build commands |
| CI/CD pipelines | ✅ GitHub Actions | 2 workflows: engine + landing |
| Deploy commands | ✅ wrangler deploy | Documented across codebase |
| Secrets management | ⚠️ Manual | Requires manual `wrangler secret put` |

---

## 1. wrangler.toml Configurations

### 1.1 mekong-engine (Production Worker)

**Path:** `packages/mekong-engine/wrangler.toml`

```toml
name = "mekong-engine"
main = "src/index.ts"
compatibility_date = "2024-12-01"
compatibility_flags = ["nodejs_compat"]
account_id = "f691e83094f776311a1bfe3f8b126f1c"

[vars]
ENVIRONMENT = "production"
DEFAULT_LLM_MODEL = "@cf/meta/llama-3.1-8b-instruct"
FB_VERIFY_TOKEN = "mekong_verify"

[[d1_databases]]
binding = "DB"
database_name = "mekong-raas-db"
database_id = "a0aa4f88-da5b-4616-84aa-7e559e37c91c"
migrations_dir = "migrations"

[[kv_namespaces]]
binding = "RATE_LIMIT_KV"
id = "982a12a5ea414244988a51d743eb14e7"

[ai]
binding = "AI"

[triggers]
crons = ["*/30 * * * *"]
```

**Bindings:**
- D1 Database: `mekong-raas-db` (a0aa4f88-da5b-4616-84aa-7e559e37c91c)
- KV Namespace: `RATE_LIMIT_KV` (982a12a5ea414244988a51d743eb14e7)
- Workers AI: Enabled
- R2 Buckets: Configured but commented out

**Secrets Required (set manually):**
- `LLM_API_KEY`
- `SERVICE_TOKEN`
- `POLAR_WEBHOOK_SECRET`

---

### 1.2 raas-dashboard (Static Site)

**Path:** `packages/raas-dashboard/wrangler.toml`

```toml
name = "raas-dashboard"
compatibility_date = "2024-09-23"

[site]
bucket = "./dist"

[env.production]
name = "raas-dashboard"
```

**Build Output:** `dist/`
**Deploy Type:** Workers Static Site

---

### 1.3 raas-landing (Pages)

**Path:** `packages/raas-landing/wrangler.toml`

```toml
name = "raas-landing"
compatibility_date = "2024-01-01"
pages_build_output_dir = "dist"

[site]
bucket = "./dist"
```

**Build Output:** `dist/`
**Deploy Type:** Cloudflare Pages

---

### 1.4 mekong-docs (Pages)

**Path:** `packages/mekong-docs/wrangler.toml`

```toml
name = "mekong-docs"
compatibility_date = "2024-09-23"
pages_build_output_dir = "dist"

[env.production]
name = "mekong-docs"
```

**Build Output:** `dist/`
**Deploy Type:** Cloudflare Pages

---

### 1.5 frontend/landing (Pages)

**Path:** `frontend/landing/wrangler.toml`

```toml
name = "agencyos-landing"
compatibility_date = "2026-03-01"
compatibility_flags = ["nodejs_compat"]
pages_build_output_dir = "out"
```

**Build Output:** `out/`
**Deploy Type:** Cloudflare Pages

---

### 1.6 Well Project Workers (apps/well/)

| Worker | Path |
|--------|------|
| Main App | `apps/well/wrangler.toml` |
| API | `apps/well/api/wrangler.toml` |
| Frontend | `apps/well/frontend/wrangler.toml` |
| quota-middleware | `apps/well/workers/quota-middleware/wrangler.toml` |
| roi-analytics-worker | `apps/well/workers/roi-analytics-worker/wrangler.toml` |
| roi-digest-worker | `apps/well/workers/roi-digest-worker/wrangler.toml` |
| raas-gateway-worker | `apps/well/workers/raas-gateway-worker/wrangler.toml` |

---

### 1.7 Algo Trader Workers (apps/algo-trader/)

| Worker | Path |
|--------|------|
| Main App | `apps/algo-trader/wrangler.toml` |
| Dashboard | `apps/algo-trader/dashboard/wrangler.toml` |

---

## 2. Build Configurations

### 2.1 mekong-engine

**package.json scripts:**
```json
{
  "dev": "wrangler dev",
  "deploy": "wrangler deploy",
  "test": "vitest run",
  "typecheck": "tsc --noEmit",
  "db:migrate": "wrangler d1 migrations apply mekong-db --local",
  "db:migrate:prod": "wrangler d1 migrations apply mekong-db"
}
```

**Entry Point:** `src/index.ts` (Hono-based router)
**Dependencies:** hono, zod, @mekong/cli-core
**Dev Dependencies:** wrangler ^3.99.0, typescript, vitest

---

### 2.2 Static Site Packages (Astro-based)

| Package | dev | build | preview |
|---------|-----|-------|---------|
| raas-dashboard | `astro dev` | `astro build` | `astro preview` |
| raas-landing | `astro dev` | `astro build` | `astro preview` |
| mekong-docs | `astro dev` | `astro build` | `astro preview` |
| frontend/landing | `astro dev` | `astro build` | - |

---

## 3. CI/CD Pipelines

### 3.1 Deploy Mekong Engine (GitHub Actions)

**File:** `.github/workflows/deploy-cloudflare.yml`

**Triggers:**
- Push to `main` or `master` (paths: `packages/mekong-engine/**`)
- Manual workflow dispatch

**Pipeline:**
```yaml
1. test-engine job:
   - pnpm install (root workspace)
   - TypeScript check (continue-on-error: true)
   - Run tests (continue-on-error: true)

2. deploy job:
   - Needs: test-engine
   - pnpm install (root workspace)
   - wrangler deploy (via cloudflare/wrangler-action@v3)
   - Smoke test: curl /health endpoint
```

**Environment Variables Required:**
- `CLOUDFLARE_API_TOKEN` (GitHub Secret)
- `CLOUDFLARE_ACCOUNT_ID` (GitHub Secret)

**Smoke Test:**
```bash
curl -sI "https://mekong-engine.${CLOUDFLARE_ACCOUNT_ID}.workers.dev/health"
```

---

### 3.2 Deploy Landing (GitHub Actions)

**File:** `.github/workflows/deploy-landing.yml`

**Triggers:**
- Push to `main` or `master` (paths: `frontend/landing/**`)

**Pipeline:**
```yaml
1. deploy job:
   - Node 22
   - npm ci (frontend/landing)
   - npm run build
   - wrangler pages deploy frontend/landing/out --project-name=agencyos-landing
```

---

## 4. Deploy Commands Summary

| Target | Command | Working Dir |
|--------|---------|-------------|
| mekong-engine | `wrangler deploy` | `packages/mekong-engine/` |
| mekong-engine (local) | `wrangler dev` | `packages/mekong-engine/` |
| raas-dashboard | `wrangler deploy` | `packages/raas-dashboard/` |
| raas-landing | `wrangler deploy` | `packages/raas-landing/` |
| mekong-docs | `wrangler deploy` | `packages/mekong-docs/` |
| frontend/landing | `wrangler deploy` or `git push` | `frontend/landing/` |

---

## 5. Infrastructure Scaffold

**Script:** `mekong/infra/scaffold.sh`

**Usage:**
```bash
bash mekong/infra/scaffold.sh <project-name> <scale>
# Scales: solo | startup | scale
```

**Scales:**
| Scale | Components |
|-------|------------|
| solo | Frontend only (CF Pages) |
| startup | Frontend + Edge API (CF Pages + CF Workers) |
| scale | Frontend + Edge API + Backend (all CF Workers) |

---

## 6. Secrets Management

**Current State:** Manual via `wrangler secret put`

**Required Secrets:**
| Secret | Purpose | Location |
|--------|---------|----------|
| `CLOUDFLARE_API_TOKEN` | CI/CD auth | GitHub Secrets |
| `CLOUDFLARE_ACCOUNT_ID` | Account ID | GitHub Secrets |
| `LLM_API_KEY` | External LLM provider | Wrangler secrets |
| `SERVICE_TOKEN` | Internal auth | Wrangler secrets |
| `POLAR_WEBHOOK_SECRET` | Payment webhooks | Wrangler secrets |

**Set Secrets:**
```bash
wrangler secret put LLM_API_KEY
wrangler secret put SERVICE_TOKEN
wrangler secret put POLAR_WEBHOOK_SECRET
```

---

## 7. Issues & Recommendations

### Issues Found

| Issue | Severity | Location |
|-------|----------|----------|
| Inconsistent compatibility_date | Low | Multiple wrangler.toml files |
| No automated testing in CI (continue-on-error: true) | Medium | deploy-cloudflare.yml |
| Manual secrets management | Medium | All Workers |
| RaaS Gateway lacks CI/CD | Medium | apps/raas-gateway/ |
| R2 buckets commented out | Low | mekong-engine/wrangler.toml |

### Recommendations

1. **Standardize compatibility_date** - Use latest date across all Workers
2. **Remove continue-on-error** from CI tests - Tests should block deploy
3. **Implement secrets scanning** - Add pre-commit hook to prevent secret commits
4. **Add RaaS Gateway CI** - Create GitHub Actions workflow
5. **Enable R2 buckets** - Uncomment and configure if storage needed
6. **Add deployment verification** - Automated smoke tests post-deploy

---

## 8. Quick Start Commands

```bash
# Local development
cd packages/mekong-engine && pnpm dev

# Deploy to production
cd packages/mekong-engine && pnpm deploy

# Run tests
cd packages/mekong-engine && pnpm test

# Type check
cd packages/mekong-engine && pnpm typecheck

# Database migrations (local)
cd packages/mekong-engine && pnpm db:migrate

# Database migrations (production)
cd packages/mekong-engine && pnpm db:migrate:prod

# Check deployment status
wrangler deployments list --name mekong-engine
```

---

## 9. Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│  GitHub Push (main/master)                              │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────▼───────────┐
        │  GitHub Actions       │
        │  - Install pnpm       │
        │  - Type check         │
        │  - Run tests          │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  Wrangler Deploy      │
        │  (cloudflare/wrangler-│
        │   action@v3)          │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  Cloudflare Workers   │
        │  - D1 Database        │
        │  - KV Namespace       │
        │  - Workers AI         │
        │  - Cron Triggers      │
        └───────────┬───────────┘
                    │
        ┌───────────▼───────────┐
        │  Smoke Test           │
        │  curl /health         │
        └───────────────────────┘
```

---

**Unresolved Questions:**
- Should R2 buckets be enabled for mekong-engine?
- Is there a plan to add CI/CD for RaaS Gateway?
- Should tests be mandatory (not continue-on-error) in CI?
