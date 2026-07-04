# 2-Guard Deploy Pipeline

Production deployment pipeline: Git + Cloudflare = 2 guards, zero risk.

## Architecture

```
/idea -> code -> push (branch)
   |
   GUARD 1: CI (build + test + lint + type-check)
   |  (bắt buộc pass trước merge)
   v
PR -> merge -> main
   |
   GUARD 2: Deploy
   |  1. Cloudflare Preview deploy
   |  2. Smoke test on preview URL
   |  3. Auto-promote to production
   |  4. Verify production
   v
Production live
```

## Workflow File

`.github/workflows/deploy-2-guard.yml` — luôn đồng bộ từ `mekong/constitution/rules/`

## Branch Protection

- `main` branch: REQUIRED
- Settings:
  - Require PR with 1 approval
  - Require status checks: `guard-1-ci`, `guard-2-deploy`
  - Require linear history
  - Enforce for admins

## GitHub Secrets Required

| Secret | Source |
|--------|--------|
| `CLOUDFLARE_API_TOKEN` | Cloudflare dashboard |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare dashboard |
| `CF_SUBDOMAIN` | Cloudflare Workers subdomain |

## Sophia AI Factory Reference

- Production: `https://sophia.agencyos.network`
- Deploy method: CF Workers via wrangler
- Workflow file: `.github/workflows/deploy-2-guard.yml`
