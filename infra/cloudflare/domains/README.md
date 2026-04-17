# Cloudflare Domain Consolidation

Authoritative config for all Mekong-ecosystem domains hosted on Cloudflare.
Platform: CF Pages + CF Workers only. Vercel BANNED 2026-03-27.

## Architecture

```
agencyos.network          → CF Pages (agencyos-site, Astro monolith)
  /docs/*                   merged from mekong-docs
  /dashboard/*              merged from raas-dashboard
api.agencyos.network      → CF Workers (mekong-engine, Hono)
sophia.agencyos.network   → CF Workers (sophia-worker)
cashclaw.cc               → CF Pages (algo-trader project)
wellnexus.vn              → CF Pages (wellnexus project)
ide.mekongmind.com        → CF Pages (mekong-ide-landing)
mekongmind.com            → CF Pages (project TBD — gap, see PHASE_LOG.md)

Legacy redirects (301, all verified live):
  app.agencyos.network      → agencyos.network/dashboard/
  dashboard.agencyos.network → agencyos.network/dashboard/
  docs.agencyos.network     → agencyos.network/docs/
  landing.agencyos.network  → agencyos.network/
```

## Files

| File | Purpose |
|------|---------|
| `production-domains.yaml` | Source of truth — all domains, status, CF project names |
| `redirects.yaml` | 301 map: active (verified) + pending (needs CF dashboard) |
| `security-headers.yaml` | HSTS, CSP, X-Frame-Options spec for CF Transform Rules |
| `deploy.sh` | Manual deploy helper (use only for hotfixes; prefer git push → GH Actions) |
| `verify.sh` | Smoke test — curl all endpoints, exit 0 if green |
| `PHASE_LOG.md` | What was done in Phase B4, action items, smoke test results |

## Quick Verify

```bash
bash infra/cloudflare/domains/verify.sh
# or fast mode (skip gap domains):
bash infra/cloudflare/domains/verify.sh --fast
```

## Quick Deploy (emergency only)

```bash
export CLOUDFLARE_API_TOKEN=<token>   # CF API token, never commit
export CLOUDFLARE_ACCOUNT_ID=<id>
bash infra/cloudflare/domains/deploy.sh agencyos-site
```

## Open Action Items

1. **HSTS missing on agencyos.network** — enable in CF Dashboard > SSL/TLS > Edge Certificates > HSTS
2. **mekongmind.com timeout** — identify CF Pages project name (`wrangler pages project list`)
3. **Always Use HTTPS** — verify ON for cashclaw.cc + wellnexus.vn
4. **CORS update** — mekong-engine Workers must allow `agencyos.network`, remove old subdomain origins
5. **mekong-landing Vercel decommission** — repo homepage still points to Vercel URL

See `PHASE_LOG.md` for full details and rollback procedure.
