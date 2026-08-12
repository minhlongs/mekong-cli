# Dashboard Deployment Automation

This document describes the CI/CD pipeline for the Mekong IDE Dashboard.

## Overview

The dashboard (`apps/dashboard`) is automatically deployed to Cloudflare Pages using GitHub Actions.

### Environments

| Environment | Trigger | URL | Branch |
|-------------|---------|-----|--------|
| Production | Push to `main` | https://ide.mekongmind.com | `production` |
| Preview | Pull requests | `https://<deployment-id>.pages.dev` | PR head ref |

### Workflow

The deployment workflow (`.github/workflows/deploy-dashboard.yml`) performs:

1. **Checkout** - Pulls the repository code
2. **Setup Node.js** - Installs Node 22 with npm caching
3. **Install wrangler** - Installs Cloudflare wrangler CLI
4. **Install dependencies** - Runs `npm ci` in the dashboard directory
5. **Build** - Runs `npm run build` with required environment variables
6. **Deploy** - Uses `wrangler-action` to deploy to Cloudflare Pages
7. **Health Check** - Verifies the production deployment returns HTTP 200

### Required Secrets

The following secrets must be configured in the GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret | Description | Required for |
|--------|-------------|-------------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token with Pages edit permissions | All deployments |
| `CF_ACCOUNT_ID` | Cloudflare account ID | All deployments |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Build (can be set in CF Pages env too) |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | Build (can be set in CF Pages env too) |

#### Creating the Cloudflare API Token

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to `User Profile > API Tokens`
3. Create a new token with the following permissions:
   - `Account > Pages > Edit`
   - `Account > Pages > Read` (optional, for verification)
4. Copy the token and add it as `CLOUDFLARE_API_TOKEN` in GitHub secrets

#### Finding your Account ID

1. In Cloudflare Dashboard, go to `Overview`
2. The Account ID is shown in the right sidebar, or use: `https://dash.cloudflare.com/<account-id>`
3. Add it as `CF_ACCOUNT_ID` in GitHub secrets

### Cloudflare Pages Project

The dashboard is deployed to the Cloudflare Pages project named `mekong-ide` with custom domain `ide.mekongmind.com`.

#### Environment Variables in Cloudflare

For production, also set these in Cloudflare Pages (`Settings > Environment variables > Production`):

| Variable | Value | Notes |
|----------|-------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL | Same as GitHub secret |
| `SUPABASE_SERVICE_KEY` | Your Supabase service key | Same as GitHub secret |
| `POLAR_PRODUCT_STARTER` | Polar product ID (optional) | For checkout |
| `POLAR_PRODUCT_GROWTH` | Polar product ID (optional) | For checkout |
| `POLAR_PRODUCT_PRO` | Polar product ID (optional) | For checkout |
| `POLAR_WEBHOOK_SECRET` | Polar webhook secret (optional) | For webhook verification |

### Manual Deployment

For manual deployments outside of CI/CD:

```bash
cd apps/dashboard
npm install
npm run build
npx wrangler pages deploy .next --project-name mekong-ide --branch production
```

Or use the provided script:

```bash
./scripts/deploy-dashboard.sh
```

### Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| `CLOUDFLARE_API_TOKEN` not found | Secret missing in GitHub | Add the secret in repo settings |
| `CF_ACCOUNT_ID` invalid | Wrong account ID | Verify in Cloudflare Dashboard |
| Build fails with missing env vars | `NEXT_PUBLIC_SUPABASE_URL` not set | Add secret or set in CF Pages env |
| 522/525 error on custom domain | DNS not propagated | Wait 5-10 minutes after first deploy |
| Preview URL shows 404 | Branch name mismatch | Check Cloudflare Pages branch deployments config |

### Status Badge

Add this badge to your README:

```markdown
![Dashboard Deploy](https://github.com/longtho638-jpg/mekong-cli/actions/workflows/deploy-dashboard.yml/badge.svg?branch=main)
```
