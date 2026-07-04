# Mekong CLI - Deployment Summary

**Status:** ✅ Complete | **Last Updated:** 2026-06-20 | **Task:** #60 Setup CI/CD Pipelines

---

## Overview

This document summarizes the CI/CD infrastructure for Mekong CLI, including deployment procedures, quality gates, and automation setup.

## CI/CD Architecture

### Pipeline Stages

```
Push → Verify → Stage (API only) → Approve (manual) → Prod Deploy → Smoke Test → Notify
```

- **Verify**: Code quality, linting, type checking, unit tests, coverage thresholds
- **Stage**: Automatic deployment to staging environment (API on all non-main branches)
- **Approve**: Manual approval gate for production deployments (main branch only)
- **Prod Deploy**: Deploy to production with rollback capability
- **Smoke Test**: Post-deployment health checks
- **Notify**: Slack notifications for all deployment events

### Environments

| Environment | API URL | Dashboard URL | Deployment Trigger |
|-------------|---------|---------------|-------------------|
| Staging | `https://mekong-api.workers.dev` | `https://staging.mekong-ide.pages.dev` | All pushes to `staging` or `feat/*` branches |
| Production | Same URL (Worker env var) | `https://mekong-ide.pages.dev` | Push to `main` (manual approval required) |

### Services

- **API**: Cloudflare Workers (Python/FastAPI via `workers-playground`)
- **Dashboard**: Next.js 15 (App Router) → Cloudflare Pages
- **Additional Workers**: Notification, Scheduler, etc. (configurable in `deploy-cf.yml`)

---

## GitHub Actions Workflows

### 1. `.github/workflows/deploy-cf.yml` (Enhanced)

Main deployment pipeline with staging → production flow.

**Jobs:**
- `verify`: Matrix job running lint, typecheck, build for both dashboard and API
- `deploy-api-staging`: Automatic deploy to staging (trigger: staging/feat branches)
- `deploy-api-production`: Manual approval required (trigger: main branch)
- `deploy-dashboard`: Deploy to Cloudflare Pages (staging/production based on branch)
- `deploy-existing-workers`: Deploy additional workers
- `health-check`: Verify all services healthy after deployment
- `rollback-on-failure`: Automated rollback if any job fails

**Required Secrets:**
- `CF_API_TOKEN`: Cloudflare API token with Workers/Pages edit permissions
- `CF_ACCOUNT_ID`: Cloudflare account ID
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications (optional but recommended)

**Example Slack Notification:**
```
✅ API production deployment
Commit: abc123def
View: https://github.com/longtho638-jpg/mekong-cli/commit/abc123def
```

### 2. `.github/workflows/release.yml` (New)

Automated release pipeline triggered by `v*` tags.

**Trigger:** `git tag v1.2.3 && git push origin v1.2.3`

**Jobs:**
1. `generate-changelog`: Uses `mikepenz/release-changelog-builder-action` with config at `.github/release-changelog-config.json`
2. `build-python`: Builds Python distribution via Poetry
3. `build-typescript`: Builds and packs npm tarball
4. `create-release`: Creates GitHub release with changelog and assets
5. `publish-pypi`: Optional PyPI publish (only if `publish-pypi` job runs)
6. `publish-npm`: Optional npm publish
7. `notify`: Slack notification with release status

**Required Secrets:**
- `PYPI_API_TOKEN`: PyPI API token for package publishing
- `NPM_TOKEN`: npm auth token for package publishing

**Changelog Categories:**
- 🚀 Features
- 🐛 Bug Fixes
- 🔧 Improvements
- 📚 Documentation
- 🧪 Testing
- 🔨 Build & CI
- 🔒 Security
- 💥 Breaking Changes

### 3. `.github/workflows/smoke-tests.yml` (New)

Runs automatically after `deploy-cf.yml` completes successfully.

**Trigger:** `workflow_run` event (deploy-cf.yml succeeded)

**Steps:**
- Install pytest + dependencies
- Run `tests/smoke/test_deployed_services.py`
- Notify Slack with results

**Environment Variables:**
- `API_BASE_URL`: Override API health endpoint
- `DASHBOARD_URL`: Override dashboard homepage

---

## CI Helper Scripts

### `ci/helpers/coverage-threshold.sh`

Enforces minimum coverage percentage from `coverage.xml`.

**Usage:** `coverage-threshold.sh <coverage.xml> <threshold_percent>`

**Example:**
```sh
coverage-threshold.sh coverage.xml 85
```

**Exit Codes:**
- `0`: Coverage meets or exceeds threshold
- `1`: Coverage below threshold (fails CI)

---

### `ci/helpers/run-gate.sh`

Shared gate runner with timing and exit code capture.

**Usage:** `run-gate.sh <gate-name> <command>`

**Example:**
```sh
run-gate.sh "G1 - Validation" "mypy src/ && black --check src/"
```

**Features:**
- Prints start/end timestamps
- Captures and returns command exit code
- Used by `gates.yml` for quality gate orchestration

---

### `ci/helpers/post-deploy-smoke.sh` (New)

Post-deployment health check with retry logic.

**Usage:** `post-deploy-smoke.sh <service> <url>`

**Example:**
```sh
post-deploy-smoke.sh api "https://mekong-api.workers.dev/healthz"
```

**Behavior:**
- Retries up to 30 times with 1-second interval
- Checks for HTTP 200
- Validates JSON response if applicable
- Exits `0` on success, `1` on failure
- Integrated into `deploy-cf.yml` health-check job

---

### `ci/helpers/rollback.sh` (New)

Automated rollback to previous deployment commit.

**Usage:** `rollback.sh <service> <environment> [previous_commit]`

**Examples:**
```sh
# Auto-detect previous commit from git history
rollback.sh api production

# Rollback to specific commit
rollback.sh dashboard production abc123def
```

**Supported Services:**
- `api`: Cloudflare Workers deployment
- `dashboard`: Cloudflare Pages deployment

**Process:**
1. Find previous deployment commit (if not provided)
2. Checkout that version in service directory
3. Reinstall dependencies and rebuild
4. Deploy to specified environment
5. Run post-rollback smoke test

**Git History Pattern:** Looks for commits with messages like `deploy: api` or `Deploy api`

---

## Smoke Tests

### `tests/smoke/test_deployed_services.py`

Python pytest tests for deployed service health.

**Tests:**
- `test_api_health`: Verifies `/healthz` returns HTTP 200
- `test_api_health_json_response`: Validates JSON response format
- `test_dashboard_homepage`: Checks dashboard loads with HTML content
- `test_dashboard_assets`: Validates static Next.js assets are accessible

**Run Locally:**
```bash
export API_BASE_URL=https://mekong-api.workers.dev
export DASHBOARD_URL=https://mekong-ide.pages.dev
pytest tests/smoke/test_deployed_services.py -v
```

---

## Quality Gates (G1-G5)

The project uses `gates.yml` to orchestrate quality checks:

| Gate | Purpose | Scripts | Threshold |
|------|---------|---------|-----------|
| G1 | Validation | black, isort, mypy | 0 errors |
| G2 | Security | bandit, safety, pip-audit | 0 vulnerabilities |
| G3 | Quality | pytest with coverage | ≥85% |
| G4 | Dependency Audit | dependabot, npm audit | No critical |
| G5 | Deploy Readiness | All above passed | — |

**Enforcement:** `gates.yml` runs sequentially, any failure blocks merge/deploy.

---

## Deployment Flow

### Automated (Staging)

1. Developer pushes to `staging` or `feat/*` branch
2. `deploy-cf.yml` triggers automatically
3. `verify` job runs lint/tests for both services
4. If verification passes:
   - API deploys to staging via `wrangler deploy --env staging`
   - Dashboard deploys to staging Pages branch
5. `health-check` verifies endpoints respond
6. Slack notification sent to `#deployments`

### Manual Approval (Production)

1. Developer opens PR to `main` and merges
2. Push to `main` triggers `deploy-cf.yml`
3. `verify` job runs for both services
4. **Manual approval step** for `deploy-api-production` job (GitHub Environments)
5. After approval:
   - API deploys to production with `--env production`
   - Dashboard deploys to production Pages (main branch)
   - Previous commit recorded in `.deploy-commit` for rollback
6. `health-check` runs smoke tests
7. If health check fails → `rollback-on-failure` triggers automatically
8. Slack notification sent to `#deployments`

### Release (Tagged)

1. Maintainer creates and pushes a `v*` tag
2. `release.yml` triggers
3. Changelog generated from PR titles since last tag
4. Python and TypeScript packages built
5. GitHub Release created with changelog + assets
6. Optional PyPI/npm publish (if secrets configured)
7. Slack notification to `#releases`

---

## Required Secrets

| Secret | Used By | Purpose | Where to Set |
|--------|---------|---------|--------------|
| `CF_API_TOKEN` | deploy-cf.yml | Cloudflare API authentication | GitHub → Settings → Secrets and variables → Actions |
| `CF_ACCOUNT_ID` | deploy-cf.yml | Cloudflare account identifier | Same as above |
| `SLACK_WEBHOOK_URL` | deploy-cf.yml, release.yml, smoke-tests.yml | Deployment notifications | Same as above |
| `PYPI_API_TOKEN` | release.yml | Publish to PyPI | Same as above |
| `NPM_TOKEN` | release.yml | Publish to npm | Same as above |
| `API_BASE_URL` | smoke-tests.yml (optional) | Override API endpoint | Same as above |
| `DASHBOARD_URL` | smoke-tests.yml (optional) | Override dashboard URL | Same as above |

### Setting Secrets

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `CF_API_TOKEN` | Value: your Cloudflare API token
4. Repeat for all required secrets

**Cloudflare API Token Permissions:**
- Account: Workers & Pages — Edit
- Account: Resources — Read
- Zone: Zone — Read (if using custom domain)

---

## Rollback Procedures

### Manual Rollback

```bash
# Rollback API to previous deployment
ci/helpers/rollback.sh api production

# Rollback dashboard
ci/helpers/rollback.sh dashboard production

# Or specify a particular commit
ci/helpers/rollback.sh api production abc123def
```

### Automatic Rollback

If `health-check` fails after production deployment, the `rollback-on-failure` job triggers automatically:

1. Checks out the previous commit from `.deploy-commit` (or git history)
2. Re-deploys the last known good version
3. Runs smoke tests on rollback
4. Sends alert to Slack

**Note:** Rollback is best-effort. Always verify the service is healthy after triggering.

---

## Monitoring & Alerting

### Current Setup

- **Deployment Notifications**: Slack `#deployments` channel
- **Health Checks**: Integrated into deploy pipeline (30s timeout, 30 retries)
- **Rollback Alerts**: Slack notification if automatic rollback triggers

### Future Enhancements

- [ ] Grafana dashboard with deployment metrics
- [ ] PagerDuty integration for critical failures
- [ ] Performance regression detection
- [ ] Canary deployments with gradual rollout

---

## Common Issues & Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| Stale Workers KV | 500 errors, cache misses | `wrangler kv key delete --namespace-id <id> --key <key>` |
| Wrangler version mismatch | Deploy fails with schema error | `npm install -g wrangler@latest` |
| Missing secrets | `undefined variable` errors in workflow | Add missing secret in GitHub Settings → Actions |
| Slow propagation | 404 after deploy | Wait 30-60s for Cloudflare global propagation |
| Permission denied | `ci/helpers/*.sh` fails locally | `chmod +x ci/helpers/*.sh` |
| Type errors in CI | Mypy/flake8 fail | `mypy src/ && black src/` locally before pushing |
| Coverage below threshold | G3 gate fails | `pytest --cov=src` to see current coverage |

---

## Deployment Verification

### Verify CI/CD Setup

```bash
# 1. Check helper scripts exist and are executable
ls -la ci/helpers/*.sh
# Should show: coverage-threshold.sh, post-deploy-smoke.sh, rollback.sh, run-gate.sh

# 2. Verify workflows
ls -la .github/workflows/ | grep -E "deploy-cf|release|smoke"
# Should show: deploy-cf.yml, release.yml, smoke-tests.yml

# 3. Validate YAML syntax (optional)
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/deploy-cf.yml'))"
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"

# 4. Check release changelog config
cat .github/release-changelog-config.json | python3 -m json.tool > /dev/null
```

### Test Smoke Script Locally

```bash
# Test API health (should return 200)
ci/helpers/post-deploy-smoke.sh api "https://mekong-api.workers.dev/healthz"

# Test dashboard homepage
ci/helpers/post-deploy-smoke.sh dashboard "https://mekong-ide.pages.dev"
```

---

## Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| CI Helper Scripts | ✅ Complete | 4 scripts created and executable |
| Staging Pipeline | ✅ Complete | Auto-deploy on feat/* and staging branches |
| Production Pipeline | ✅ Complete | Manual approval gate |
| Smoke Tests | ✅ Complete | pytest suite + GitHub workflow |
| Release Automation | ✅ Complete | Changelog → Build → Release → Publish |
| Slack Notifications | ✅ Complete | Integrated in all deploy/release workflows |
| Rollback Procedures | ✅ Complete | Automated on failure + manual script |
| Quality Gates | ✅ Existing | G1-G5 enforced in gates.yml |
| Documentation | ✅ Complete | This document + inline comments |

---

## Next Steps

- [ ] Configure required GitHub Secrets (CF_API_TOKEN, SLACK_WEBHOOK_URL, etc.)
- [ ] Test staging deployment by pushing to `staging` branch
- [ ] Verify smoke tests pass in CI
- [ ] Create first release by tagging: `git tag v1.0.0 && git push origin v1.0.0`
- [ ] Set up monitoring dashboard (Grafana/Datadog) for production metrics
- [ ] Document runbook for on-call engineers (see `docs/runbook.md`)

---

## References

- GitHub Actions: <https://docs.github.com/en/actions>
- Cloudflare Workers: <https://developers.cloudflare.com/workers/>
- Conventional Commits: <https://www.conventionalcommits.org/>
- Mekong CLI Architecture: `docs/system-architecture.md`
