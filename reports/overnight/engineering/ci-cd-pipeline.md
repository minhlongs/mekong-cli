# CI/CD Pipeline Analysis — Mekong CLI

**Date:** 2026-03-11
**Scope:** All GitHub Actions workflows, pipeline stages, release flow

---

## 1. Workflow Inventory

```
.github/workflows/
├── ci.yml                    — Main: lint + test + security + frontend build
├── test.yml                  — Secondary test runner (lower threshold)
├── deploy-cloudflare.yml     — CF Workers engine deploy
├── deploy-landing.yml        — CF Pages landing deploy
├── security-hardening.yml    — 5-job security attestation
├── publish-pypi.yml          — PyPI package release
├── e2e-tests.yml             — End-to-end test suite
├── pr-auto-review.yml        — Automated PR review
├── issue-triage.yml          — Issue auto-labeling
├── factory-validate.yml      — Factory contracts validation
├── docsops.yml               — Documentation operations
├── nightly-reconciliation.yml— Nightly billing reconciliation
├── stale-cleanup.yml         — Stale PR/issue cleanup
├── jules-cleanup.yml         — Jules agent cleanup
├── daily-repo-status.md      — Daily repo health (locked)
├── tom-hum-test.md           — Tôm Hùm test (locked)
├── publish-packages.yml      — Multi-package publish
├── social-auth-kit-tests.yml — Social auth kit CI
├── 84tea-ci.yml              — 84tea app CI
├── agencyos-landing-ci.yml   — AgencyOS landing CI
├── algo-trader-ci.yml        — Algo trader CI
├── algo-trader-deploy.yml    — Algo trader deploy
└── cc-cli.yml                — CC CLI workflow
```

24 workflow files total. Primary ones for mekong-cli core: `ci.yml`, `test.yml`, `deploy-cloudflare.yml`, `security-hardening.yml`, `publish-pypi.yml`.

---

## 2. Primary CI Pipeline (ci.yml)

**Triggers:** push to main/master, PR opened/synchronized

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   backend   │     │  security   │     │  frontend   │
│  (Python)   │     │  (bandit +  │     │  (Node 22)  │
│             │     │   safety)   │     │             │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│  benchmarks │  (needs: backend)
│  (AGI tasks)│
└─────────────┘
```

### backend job (Python 3.12, ubuntu-latest, timeout: 10min)

```yaml
1. checkout@v4
2. setup-python@v5 (3.12, pip cache)
3. pip install -r requirements.txt + ruff + pytest + anyio + httpx + pytest-cov
4. pip install -e .
5. mekong --help                                    [continue-on-error]
6. ruff check src/ tests/                           [BLOCKING]
7. ruff format --check src/ tests/                  [continue-on-error]
8. pytest tests/ (ignore: backend/e2e/integration/unit/benchmarks)
   --cov=src --cov-fail-under=80                    [continue-on-error]
```

Blocking gates: **ruff lint only**. Test failures and format violations are non-blocking.

### benchmarks job (Python 3.12, needs: backend)

```yaml
pytest tests/benchmarks/test_agi_tasks.py -v --tb=short
```

Runs AGI benchmark suite after backend passes.

### security job (ubuntu-latest, timeout: 5min, runs in parallel)

```yaml
1. bandit -r src/ -ll --exit-zero                  [non-blocking]
2. safety check -r requirements.txt --ignore 70612  [non-blocking]
3. grep for hardcoded secrets                       [BLOCKING if found]
```

### frontend job (Node 22, runs in parallel)

```yaml
cd frontend/landing && npm ci && npm run build
```

---

## 3. Secondary Test Pipeline (test.yml)

**Triggers:** push to main/master, PR to main/master
**Python:** 3.11 (different from ci.yml's 3.12 — version matrix gap)

```yaml
1. pip install requirements + pytest + ruff + httpx
2. pip install -e .
3. ruff check src/ tests/                           [BLOCKING]
4. pytest tests/ (ignore: backend/e2e/integration/unit)
   --cov-fail-under=15                              [lower threshold]
```

Threshold comparison:
- `ci.yml`: `--cov-fail-under=80` (continue-on-error → effectively 0%)
- `test.yml`: `--cov-fail-under=15` (actual enforced gate)

Effective minimum coverage enforced: **15%**

---

## 4. Deploy Pipeline: CF Workers (deploy-cloudflare.yml)

**Triggers:** push to main, paths `packages/mekong-engine/**`

```
test-engine ──► deploy ──► smoke-test
```

```yaml
test-engine:
  - pnpm install
  - npx tsc --noEmit         [continue-on-error]
  - npx vitest run            [continue-on-error]

deploy:
  needs: test-engine
  if: refs/heads/main
  - cloudflare/wrangler-action@v3
  - command: deploy
  - secrets: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ACCOUNT_ID

smoke-test:
  - sleep 10
  - curl health endpoint → HTTP 200 check
```

Both test gates are non-blocking — deploy proceeds even if tests fail.

---

## 5. Security Hardening Pipeline (security-hardening.yml)

**Triggers:** push to main/master, any PR

5 sequential jobs with final attestation:

```
secret-scanning
command-injection-scan
dependency-audit
     │
     ▼
attestation-report (needs: all 3)
     │
     ▼
security-gate (blocks merge if ATTESTATION_FAILED)
```

Outputs:
- JSON attestation artifact (90-day retention)
- SHA256 hash of attestation
- `ATTESTED_SECURE` or `ATTESTATION_FAILED` status

Security gate **does block** merge on attestation failure — strongest enforcement in the pipeline.

---

## 6. PyPI Release Pipeline (publish-pypi.yml)

**Trigger:** tag push matching `v*.*.*`

```yaml
- python -m build
- twine upload dist/*
secret: PYPI_TOKEN
```

No pre-publish test gate — publishes immediately on tag. Risk: broken release if tag pushed without running CI.

---

## 7. Pipeline Health Assessment

| Pipeline | Blocking Gates | Test Coverage Gate | Deploy Gate |
|----------|---------------|-------------------|-------------|
| ci.yml | ruff lint, secret grep | Non-blocking (80%) | N/A |
| test.yml | ruff lint | 15% enforced | N/A |
| deploy-cloudflare.yml | None (all continue-on-error) | None | smoke HTTP 200 |
| security-hardening.yml | secret grep, security-gate | N/A | N/A |
| publish-pypi.yml | None | None | None |

---

## 8. Pipeline Gaps & Issues

| Gap | Severity | Detail |
|-----|----------|--------|
| CF Workers deploy: test gates non-blocking | HIGH | TypeScript errors and vitest failures don't block deploy |
| PyPI release: no pre-publish test gate | HIGH | Tag → publish with no CI check |
| Coverage threshold gap | MEDIUM | ci.yml says 80% but continue-on-error makes it 0%; test.yml enforces 15% |
| Python version inconsistency | LOW | ci.yml uses 3.12, test.yml uses 3.11 |
| RaaS Gateway has no CI/CD | MEDIUM | Manual wrangler deploy, no automated pipeline |
| No staging environment | HIGH | Straight to production on main push |
| e2e-tests.yml excluded from main flow | MEDIUM | E2E never runs as part of merge gate |

---

## 9. Recommended Pipeline Improvements

1. **Make CF Workers test gates blocking** — remove `continue-on-error` from tsc + vitest
2. **Add test gate to PyPI publish** — run `pytest -q --tb=short` before `twine upload`
3. **Unify Python version** — use 3.12 in both ci.yml and test.yml
4. **Add RaaS Gateway CI** — lint JS + wrangler deploy in CI/CD
5. **Raise effective coverage gate** — set test.yml `--cov-fail-under=40` as interim target
6. **Add staging deploy job** — deploy to `staging.agencyos.network` on PR, production on merge
7. **Wire e2e-tests.yml into merge gate** — require E2E pass before merging to main

---

## 10. Release Flow (Current)

```
Feature branch → PR → ci.yml (lint gate) + security-hardening.yml
    → Merge to main
    → ci.yml backend + benchmarks + security + frontend (parallel)
    → deploy-cloudflare.yml (if packages/mekong-engine changed)
    → deploy-landing.yml (if frontend/landing changed)
    → git tag v*.*.* → publish-pypi.yml
```

No formal release checklist or changelog generation in pipeline. Changelog is maintained manually in `docs/project-changelog.md`.
