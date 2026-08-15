# Load Testing Framework

Comprehensive performance testing framework for Mekong IDE, covering API load testing, frontend performance, and Python benchmarks.

## Overview

The load testing framework uses:

| Tool | Purpose | Use Case |
|------|---------|----------|
| **k6** | API load & stress testing | Simulate user traffic, find breaking points |
| **lighthouse-ci** | Frontend performance | Core Web Vitals, accessibility, SEO |
| **pytest-benchmark** | Python code benchmarks | Catch regressions in critical functions |

## Quick Start

### Prerequisites

```bash
# Install k6 (API load testing)
brew install k6                    # macOS
# OR: sudo apt-get install k6     # Ubuntu
# OR: curl -s https://raw.githubusercontent.com/k6io/k6/master/install.sh | bash

# Install lighthouse-ci (frontend performance)
npm install -g @lhci/cli

# Install pytest-benchmark (Python benchmarks)
pip install pytest-benchmark
```

### Run All Load Tests

```bash
# Using Make (recommended)
make load-test

# Or manually
cd load-tests && ./run-all-tests.sh
```

### Run Specific Tests

```bash
# API load test (20 VUs, 1 minute)
make load-test-api
# OR: load-tests/run-load-tests.sh health 20 1m

# Frontend performance
make load-test-frontend

# Python benchmarks
make load-test-benchmark

# Stress test (200 VUs)
load-tests/run-load-tests.sh stress 100 3m

# Spike test (sudden traffic burst)
load-tests/run-load-tests.sh spike 100 1m
```

## Test Scenarios

### 1. Health Check (`health-check.js`)

Tests baseline infrastructure capacity with the `/healthz` endpoint.

**Metrics:**
- Response time (p95 < 200ms, p99 < 500ms)
- Success rate (> 99%)

**Usage:**
```bash
load-tests/run-load-tests.sh health 10 30s
```

### 2. Mission API (`mission-api.js`)

Tests mission creation and retrieval endpoints, simulating typical user behavior.

**Metrics:**
- Mission creation latency (p95 < 1000ms)
- Mission retrieval latency (p95 < 500ms)
- Success rate (> 95%)

**Usage:**
```bash
load-tests/run-load-tests.sh missions 20 1m
```

### 3. Auth API (`auth-api.js`)

Tests authentication endpoints under load.

**Metrics:**
- Login latency (p95 < 500ms)

**Usage:**
```bash
load-tests/run-load-tests.sh auth 30 1m
```

### 4. Full Suite (`full-suite.js`)

Mixed traffic pattern simulating real usage with:
- 40% mission creation
- 30% mission retrieval
- 15% health checks
- 15% detailed health

**Usage:**
```bash
load-tests/run-load-tests.sh full 50 2m
```

### 5. Spike Test (`spike-test.js`)

Rapid traffic ramp-up to test system resilience.

**Pattern:**
```
0 RPS → 10 RPS (5s) → 50 RPS (10s) → 200 RPS (15s) → 0 RPS
```

**Usage:**
```bash
load-tests/run-load-tests.sh spike 100 2m
```

### 6. Stress Test (`stress-test.js`)

Gradual load increase to find breaking point.

**Pattern:**
```
10 VUs → 50 (1m) → 100 (2m) → 150 (2m) → 200 (2m) → 0
```

**Usage:**
```bash
load-tests/run-load-tests.sh stress 200 8m
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | API base URL |
| `FRONTEND_URL` | `http://localhost:3000` | Frontend URL |
| `API_KEY` | `test-key` | Test API key |
| `TENANT_ID` | `test-tenant-001` | Test tenant ID |
| `VUS` | varies by test | Number of virtual users |
| `DURATION` | varies by test | Test duration (e.g., 30s, 1m, 2m) |

**Example:**
```bash
BASE_URL=https://api-staging.mekongmind.com \
API_KEY=staging-test-key \
VUS=100 \
load-tests/run-load-tests.sh full
```

## Frontend Performance Testing

Uses Lighthouse CI to measure:

| Metric | Target | Description |
|--------|--------|-------------|
| Performance | ≥ 80% | Core Web Vitals combined |
| Accessibility | ≥ 90% | WCAG compliance |
| Best Practices | ≥ 90% | Modern web standards |
| SEO | ≥ 80% | Search engine optimization |
| FCP | < 1800ms | First Contentful Paint |
| LCP | < 2500ms | Largest Contentful Paint |
| CLS | < 0.1 | Cumulative Layout Shift |
| TBT | < 200ms | Total Blocking Time |

**Run:**
```bash
FRONTEND_URL=https://staging.mekongmind.com \
make load-test-frontend
```

Reports are saved to `load-tests/reports/lighthouse/`.

## Python Benchmarks

Critical Python functions are benchmarked to catch performance regressions:

- Health check endpoints
- Component status checks
- MCU billing operations
- Mission creation validation
- Database query performance

**Run benchmarks:**
```bash
make load-test-benchmark
# OR
.venv/bin/pytest tests/benchmarks/ --benchmark-only --benchmark-compare
```

Benchmark history is saved to `tests/benchmarks/.benchmarks/`.

## CI/CD Integration

Load tests run automatically:

- **On every PR** - Full suite with 20 VUs for 1 minute
- **Nightly at 2 AM UTC** - Full suite with production/staging targets
- **On deploy** - Smoke test with 5 VUs for 30s

### GitHub Actions Workflow

See `.github/workflows/load-testing.yml`. Key features:

- Multi-environment support (localhost, staging, production)
- Automatic threshold validation
- PR comment with results summary
- Artifact retention for 14 days

**Manual run:**
```bash
gh workflow run load-testing.yml -f environment=staging -f vus=50 -f duration=2m
```

## Reports

All test reports are saved to `load-tests/reports/`:

```
load-tests/reports/
├── k6-<test>-<timestamp>.json    # Raw k6 metrics (JSON)
├── k6-<test>-<timestamp>.html    # Interactive k6 report
└── lighthouse/
    └── report-<timestamp>/
        ├── lhci-report.json      # Lighthouse results
        └── *.html                # Visual reports
```

**View HTML reports:**
```bash
open load-tests/reports/k6-full-suite-*.html
```

## Interpreting Results

### k6 Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| `http_req_duration` (p95) | < 300ms | 300-500ms | > 500ms |
| `http_req_duration` (p99) | < 500ms | 500-1000ms | > 1000ms |
| `errors` (rate) | < 1% | 1-5% | > 5% |

### Lighthouse Scores

| Category | Good | Warning | Critical |
|----------|------|---------|----------|
| Performance | ≥ 80% | 70-80% | < 70% |
| Accessibility | ≥ 90% | 80-90% | < 80% |
| Best Practices | ≥ 90% | 80-90% | < 80% |
| SEO | ≥ 80% | 70-80% | < 70% |

### Python Benchmarks

Benchmark comparisons show percentage change from baseline. Regressions >5% should be investigated.

## Tuning for Production

### Staging Tests

Run with realistic production-like traffic:

```bash
# 100 concurrent users for 10 minutes
VUS=100 DURATION=10m load-tests/run-load-tests.sh full

# Spike test to 500 RPS
VUS=500 load-tests/run-load-tests.sh spike
```

### Production Canary

Gradual rollout with increasing load:

```bash
# 10% traffic (50 VUs)
VUS=50 load-tests/run-load-tests.sh health

# If good, 50% traffic (250 VUs)
VUS=250 load-tests/run-load-tests.sh full 5m

# If good, 100% traffic (500 VUs)
VUS=500 load-tests/run-load-tests.sh full 10m
```

## Threshold Configuration

Edit thresholds in each k6 test file's `options.thresholds`:

```javascript
export const options = {
  thresholds: {
    errors: ['rate<0.01'],                    // 1% max error rate
    api_latency: {
      p(95): '<300',                          // 95th percentile < 300ms
      p(99): '<800',                          // 99th percentile < 800ms
    },
  },
};
```

## Troubleshooting

### Tests fail with "API is not responding"

Start the API first:
```bash
make start-gateway
```

### k6 not found

Install k6 (see Prerequisites above).

### Lighthouse hangs

Ensure Chrome/Chromium is available. lighthouse-ci uses system Chrome or can use Puppeteer's bundled version:

```bash
npm install -g puppeteer
```

### High error rates in tests

Check:
1. API logs for errors: `tail -f logs/errors.log`
2. Database connectivity
3. Rate limiting configuration
4. API key validity

### Memory issues with long runs

Reduce `VUS` or increase sleep times in test scripts. Monitor memory:

```bash
# Check k6 memory usage
ps aux | grep k6
```

## Performance Budget

| Metric | Budget | Current |
|--------|--------|---------|
| API p95 latency | < 300ms | TBD |
| API p99 latency | < 800ms | TBD |
| API error rate | < 1% | TBD |
| Frontend LCP | < 2500ms | TBD |
| Frontend CLS | < 0.1 | TBD |

These budgets are enforced in CI. PRs that exceed budgets will fail.

## Adding New Tests

1. Create k6 script in `load-tests/k6/`
2. Add case in `run-load-tests.sh`
3. Update `run-all-tests.sh` if needed
4. Add thresholds relevant to your endpoint
5. Update this documentation

## References

- [k6 Documentation](https://k6.io/docs/)
- [Lighthouse CI](https://github.com/GoogleChrome/lighthouse-ci)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
