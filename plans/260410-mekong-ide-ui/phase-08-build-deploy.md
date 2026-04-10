---
phase: 8
title: "Build + Deploy to CF Pages"
status: completed
effort: 2h
depends_on: [1, 2, 3, 4, 5, 6, 7]
---

# Phase 8: Build + Deploy to CF Pages

## Context
- Static export via `next.config.ts` `output: 'export'`
- Deploy to Cloudflare Pages (Vercel BANNED)
- GitHub Actions CI/CD pipeline

## Files to Create/Modify

```
apps/mekong-ide/
├── wrangler.toml                      # CF Pages config (optional, for wrangler deploy)
├── .env.production                    # NEXT_PUBLIC_API_URL=https://api.mekongmind.com

.github/workflows/
├── mekong-ide-deploy.yml              # CI: build + deploy to CF Pages
```

## Implementation Steps

1. **Verify static export** — Run `cd apps/mekong-ide && pnpm build`. Confirm `out/` directory contains all routes as static HTML. Fix any dynamic route issues (all routes must be statically exportable).

2. **Create `.env.production`**:
   ```
   NEXT_PUBLIC_API_URL=https://api.mekongmind.com
   ```

3. **Create `wrangler.toml`** (for manual deploys):
   ```toml
   name = "mekong-ide"
   compatibility_date = "2026-04-10"

   [site]
   bucket = "./out"
   ```

4. **Add build script to root package.json**:
   ```json
   "build:ide": "cd apps/mekong-ide && pnpm build"
   ```

5. **Create GitHub Actions workflow** `mekong-ide-deploy.yml`:
   ```yaml
   name: Deploy Mekong IDE
   on:
     push:
       branches: [main]
       paths: ['apps/mekong-ide/**']
   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: pnpm/action-setup@v4
         - uses: actions/setup-node@v4
           with: { node-version: 22, cache: pnpm }
         - run: pnpm install --frozen-lockfile
         - run: pnpm --filter mekong-ide build
         - uses: cloudflare/wrangler-action@v3
           with:
             command: pages deploy apps/mekong-ide/out --project-name=mekong-ide
             apiToken: ${{ secrets.CF_API_TOKEN }}
             accountId: ${{ secrets.CF_ACCOUNT_ID }}
   ```

6. **Test local build**:
   ```bash
   cd apps/mekong-ide
   pnpm build
   npx serve out  # verify at localhost:3000
   ```

7. **Manual first deploy** (to create CF Pages project):
   ```bash
   cd apps/mekong-ide
   wrangler pages project create mekong-ide
   wrangler pages deploy out --project-name=mekong-ide
   ```

8. **Verify production**:
   ```bash
   curl -sI https://mekong-ide.pages.dev | head -1
   # Expect: HTTP/2 200
   ```

9. **Custom domain** (future): Add `ide.mekongmind.com` via CF Pages custom domain settings.

## Build Optimization

- Ensure `images.unoptimized: true` in next.config (required for static export)
- Bundle size target: < 500KB gzipped (no heavy deps — no Monaco, no chart library beyond recharts if needed)
- Code splitting: each route lazy-loaded automatically by Next.js App Router

## Verification Checklist

```bash
# Full verification pipeline
cd apps/mekong-ide
pnpm build                    # Build succeeds
ls out/                       # Static files exist
npx serve out -l 3000         # Local preview works
wrangler pages deploy out --project-name=mekong-ide  # Deploy
curl -sI https://mekong-ide.pages.dev | head -1      # HTTP 200
```

## Success Criteria
- [x] `pnpm build` produces `out/` with all routes (6 routes: /, /engine, /ide, /tasks, /trading, /_not-found)
- [x] Bundle < 500KB gzipped (First Load JS: ~102-114KB per route)
- [ ] CF Pages deploy succeeds (requires CLOUDFLARE_API_TOKEN + CF_ACCOUNT_ID secrets)
- [ ] Production URL returns HTTP 200 (post-deploy verification)
- [x] All routes accessible via direct URL (static export — all ○ Static)
- [x] GitHub Actions workflow triggers on push to main (.github/workflows/deploy-ide.yml)
