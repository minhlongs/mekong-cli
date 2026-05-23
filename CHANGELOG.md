# Changelog

All notable changes to this project will be documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `GET /metrics` — Prometheus text format endpoint for MCU/PEV/uptime gauges
- CSRF middleware (double-submit cookie, env-gated `CSRF_ENABLED=1`)
- Rate-limit gateway middleware wiring existing `RateLimiter` (`RATE_LIMIT_ENABLED=1`)
- Dependabot configuration for pip and GitHub Actions dependencies
- `GET /healthz` — lightweight liveness probe for load balancers

### Changed
- MCUBilling migrated from in-memory dict to SQLite WAL via CreditStore
- License gate changed to fail-closed (default `LICENSE_GATE_ENFORCE=1`)
- Coverage config: removed `*/raas/*` and `*/llm_client.py` from omit list

### Fixed
- JSONL append race conditions via `fcntl` advisory locking (8 files)
- Gateway CORS: explicit origin whitelist replaces wildcard
- Gateway: Swagger UI disabled in production
- Gateway: bare `except` narrowed to specific exception types
- Database health check added to `/health` endpoint

### Security
- `poetry.lock` committed to pin transitive dependencies
- CORS `allow_headers` restricted to known headers
- `.gitignore` no longer excludes `poetry.lock`

## [6.0.0] - 2026-05-10

### Added
- 342+ CLI commands across 6 organizational layers
- PEV Engine (Plan-Execute-Verify) orchestration loop
- MCU Billing with Polar.sh webhook integration
- VN Hub: kế toán, thuế, Zalo OA, VietQR webhook
- Agent layer: GitAgent, FileAgent, ShellAgent, LeadHunter, ContentWriter
- Universal LLM router with 7-provider fallback chain
- 3-layer Cloudflare-only infrastructure templates
