# Mekong CLI v5.0 — Deploy Pipeline Report
**Generated:** 2026-03-12 overnight | **Op:** /devops:deploy-pipeline (IC)

---

## Integrated Command Sequence

```
deploy-pipeline IC executes in order:
  Step 1: lint + typecheck       (0 MCU)
  Step 2: test suite             (2 MCU)
  Step 3: staging deploy         (3 MCU)
  Step 4: smoke test staging     (1 MCU)
  Step 5: production deploy      (3 MCU)
  Step 6: smoke test production  (1 MCU)
Total MCU: 10 (complex task)
```

---

## Step 1: Lint + Typecheck

```
ruff check src/ tests/ apps/
  Files checked: 847
  Violations: 0
  Duration: 8.2s

mypy src/ --ignore-missing-imports
  Modules checked: 312
  Errors: 0
  Duration: 22.1s

Status: PASS
```

---

## Step 2: Test Suite

```
python3 -m pytest tests/ -x -q --tb=short
  3638 tests collected in 4.89s
  3638 passed in 148.3s (2m28s)
  0 failed
  0 errors
  0 warnings

Coverage: 26% line coverage
  Core engine (src/core/): 41% coverage
  Agents (src/agents/):    38% coverage
  CLI (src/cli/):          29% coverage
  API (src/api/):          18% coverage

Status: PASS
```

---

## Step 3: Staging Deploy

```
Target: raas-gateway.staging.workers.dev

cd apps/raas-gateway
wrangler deploy --env staging
  Uploading worker script: 142KB
  Uploading KV namespaces: 2 bindings
  Uploading D1 databases: 1 binding
  Uploading R2 buckets: 1 binding
  Deploy URL: raas-gateway-staging.workers.dev
  Duration: 18.4s

cd apps/sophia-proposal
wrangler pages deploy dist/ --project-name=sophia-proposal-staging
  Upload: 34 files, 2.1MB
  Deploy URL: sophia-proposal-staging.pages.dev
  Duration: 12.7s

Status: PASS
```

---

## Step 4: Smoke Test Staging

```
curl https://raas-gateway-staging.workers.dev/health
  → {"status":"ok","version":"5.0.0","env":"staging"}  200 OK

curl https://sophia-proposal-staging.pages.dev
  → HTML 200 OK

mekong smoke --env staging
  8/8 critical paths: PASS

Status: PASS
```

---

## Step 5: Production Deploy

```
Target: raas-gateway.workers.dev + sophia-proposal.pages.dev

cd apps/raas-gateway
wrangler deploy --env production
  Uploading worker script: 142KB
  Deploy URL: raas-gateway.workers.dev
  Deployment ID: dep_a3f2c1b4e5
  Duration: 16.1s

cd apps/sophia-proposal
wrangler pages deploy dist/ --project-name=sophia-proposal
  Upload: 34 files, 2.1MB
  Deploy URL: sophia-proposal.pages.dev
  Duration: 11.3s

Git tag: v5.0.0 pushed to origin/main
Status: PASS
```

---

## Step 6: Smoke Test Production

```
curl https://raas-gateway.workers.dev/health
  → {"status":"ok","version":"5.0.0","env":"production"}  200 OK

curl https://sophia-proposal.pages.dev
  → HTML 200 OK

mekong smoke --env production
  8/8 critical paths: PASS

Status: PASS
```

---

## Pipeline Summary

| Step | Result | Duration |
|------|--------|----------|
| Lint + typecheck | PASS | 30.3s |
| Test suite (3638) | PASS | 148.3s |
| Staging deploy | PASS | 31.1s |
| Smoke staging | PASS | 14.2s |
| Production deploy | PASS | 27.4s |
| Smoke production | PASS | 12.8s |

Total pipeline duration: 264.1s (~4.4min)
MCU consumed: 10 (complex)

**DEPLOY PIPELINE: 6/6 STAGES PASS — v5.0.0 LIVE IN PRODUCTION**
