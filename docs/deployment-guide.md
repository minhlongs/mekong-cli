# Deployment Guide: Mekong CLI RaaS

## Overview

Mekong CLI RaaS uses Cloudflare's serverless infrastructure:
- **Workers**: mekong-engine (API + PEV engine)
- **Pages**: raas-landing (marketing site)

## Environments

| Service | Production URL | Type | Status |
|---------|---------|------|--------|
| API Gateway | api.agencyos.network | CF Workers v5.0.0 | Active |
| Dashboard | app.agencyos.network | CF Pages | Active (signup/login ready) |
| Landing | agencyos.network | CF Pages | Active |
| Docs | docs.agencyos.network | CF Pages | Active |
| LLM Fallback | 192.168.11.111:11434 | Ollama (M1 Max) | Active |

**Legacy Endpoints (deprecated):**
- `mekong-engine-staging.*.workers.dev` → migrate to api.agencyos.network
- `raas-landing.pages.dev` → use agencyos.network instead

---

## 1. Prerequisites

### Install Wrangler

```bash
npm install -g wrangler
# or
pnpm add -g wrangler
```

### Authenticate

```bash
wrangler login
```

### Required Secrets

```bash
# Set via GitHub Secrets (not wrangler secret put for CI/CD)
# In GitHub Repo Settings → Secrets and variables → Actions:
# - CLOUDFLARE_API_TOKEN
# - CLOUDFLARE_ACCOUNT_ID
```

---

## 2. Local Deployment

### mekong-engine (Worker)

```bash
cd packages/mekong-engine

# Development (local)
wrangler dev

# Deploy to staging
wrangler deploy --env staging

# Deploy to production
wrangler deploy
```

### raas-landing (Pages)

```bash
cd packages/raas-landing

# Development
npm run dev

# Build
npm run build

# Deploy to staging
npx wrangler pages deploy dist --project-name=raas-landing-staging

# Deploy to production
npx wrangler pages deploy dist --project-name=raas-landing
```

---

## 3. CI/CD Deployment (GitHub Actions)

### Manual Deploy via Workflow Dispatch

1. Go to **Actions** → **Deploy Cloudflare**
2. Click **Run workflow**
3. Select environment: `staging` or `production`
4. Click **Run workflow**

### Automatic Deploy on Push

- Push to `main` → Auto-deploys to **staging**
- Manual dispatch required for **production**

### Rollback

1. Go to **Actions** → **Rollback Cloudflare**
2. Click **Run workflow**
3. Select environment and optionally specify version ID
4. Click **Run workflow**

---

## 4. Smoke Tests

### Health Endpoints

```bash
# Staging
curl -sI "https://mekong-engine-staging.<account>.workers.dev/health"

# Production
curl -sI "https://mekong-engine.agencyos.network/health"
```

### Expected Response

```
HTTP/2 200
content-type: application/json
```

---

## 5. Security Headers

Add to `wrangler.toml` or via `_headers` file for Pages:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

## 6. Rollback Runbook

### Via GitHub Actions (Recommended)

```bash
# Go to Actions → Rollback Cloudflare
# Select environment: staging or production
# Optionally specify version ID
```

### Via Wrangler CLI

```bash
cd packages/mekong-engine

# List deployments
wrangler deployments list --env staging
wrangler deployments list

# Rollback to specific version
wrangler rollback [version-id] --env staging
wrangler rollback [version-id]
```

### Pages Rollback

For Pages, redeploy the previous commit:

```bash
cd packages/raas-landing
git checkout <previous-commit>
npm run build
npx wrangler pages deploy dist --project-name=raas-landing-staging
```

---

## 7. Environment Variables

### Production (wrangler.toml)

```toml
[vars]
ENVIRONMENT = "production"
DEFAULT_LLM_MODEL = "@cf/meta/llama-3.1-8b-instruct"
```

### Staging (wrangler.toml)

```toml
[env.staging]
name = "mekong-engine-staging"
vars = { ENVIRONMENT = "staging" }
```

### Secrets (set via GitHub)

| Secret | Purpose |
|--------|---------|
| `CLOUDFLARE_API_TOKEN` | Wrangler deployment auth |
| `CLOUDFLARE_ACCOUNT_ID` | Account identifier |
| `LLM_API_KEY` | LLM provider key (set via `wrangler secret put`) |
| `NOWPAYMENTS_WEBHOOK_SECRET` | NOWPayments webhook verification |

---

## 8. Troubleshooting

### Deployment Fails

1. Check Wrangler logs: `wrangler deploy --dry-run`
2. Verify API token has correct permissions
3. Check account ID matches

### Health Check Fails

1. Wait 10-30s for propagation
2. Verify custom domain is configured
3. Check Worker logs: `wrangler tail --env staging`

### Rollback Issues

1. List available versions: `wrangler deployments list`
2. Check version is not already rolled back
3. For Pages, redeploy from git history
