# PEV Engine — Setup Guide

**PEV** = Plan → Execute → Verify. The Python engine at the core of Mekong CLI.

---

## Quickstart

### Prerequisites

- Python 3.9–3.12
- `pip` or a virtualenv manager

### Install dependencies

```bash
# Create virtualenv
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install all deps
pip install -r requirements.txt
```

### Configure environment

```bash
cp .env.example .env
# Edit .env and set at minimum:
#   JWT_SECRET (generate below)
#   LLM_API_KEY or one of the provider-specific keys
```

Generate a secure JWT_SECRET:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
# or
openssl rand -hex 32
```

Paste the output into `.env`:

```
JWT_SECRET=<generated-value>
```

### Verify imports

```bash
# Core PEV orchestrator
python3 -c "from src.core.orchestrator.runner import RecipeOrchestrator; print('PEV OK')"

# JWT edge auth
python3 -c "from src.core.auth_jwt import decode_jwt; print('JWT OK')"

# Env validator
python3 -c "from src.auth.env_validator import validate_startup_env; print('validator OK')"
```

### Run tests

```bash
# JWT security tests (52 tests)
TESTING=true python3 -m pytest tests/test_auth_jwt_security.py -v

# JWT_SECRET enforcement tests
TESTING=true python3 -m pytest tests/auth/test_jwt_secret_required.py -v

# Full auth test suite
TESTING=true python3 -m pytest tests/auth/ -v

# Full suite
TESTING=true python3 -m pytest tests/ -q
```

---

## Production Requirements

### JWT_SECRET

| Env | Behavior |
|-----|----------|
| `AUTH_ENVIRONMENT=dev` (default) | JWT_SECRET auto-generated per session if not set. Warn logged. |
| `AUTH_ENVIRONMENT=staging` | JWT_SECRET **required**, min 32 bytes. Startup fails if absent. |
| `AUTH_ENVIRONMENT=production` | JWT_SECRET **required**, min 32 bytes. Startup fails if absent. |

**Minimum:** 32 bytes (256 bits). Use `token_urlsafe(32)` or `openssl rand -hex 32`.

**Never** commit JWT_SECRET to git. It belongs in `.env` (gitignored) or your secret manager.

### Required env vars for production

```bash
AUTH_ENVIRONMENT=production
JWT_SECRET=<32+ bytes>          # REQUIRED — fail-fast if missing
LLM_API_KEY=<provider-key>      # Required for PEV task execution
```

### Optional but recommended

```bash
JWT_ACCESS_EXPIRY_MINUTES=30    # Default: 30
JWT_REFRESH_EXPIRY_DAYS=7       # Default: 7
SENTRY_DSN=<dsn>                # Error tracking
POLAR_API_KEY=<key>             # MCU billing
```

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'opentelemetry'`

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

These are required for the telemetry layer inside `src/core/telemetry/`.

### `RuntimeError: JWT_SECRET environment variable is required`

Set `JWT_SECRET` in your `.env` file:

```bash
echo "JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env
```

Or for CI pipelines, set the `JWT_SECRET` environment variable in your CI secrets.

### `RuntimeError: JWT_SECRET is too short`

The secret must be at least 32 bytes. Re-generate:

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### Poetry not available on M1 Max

The project uses a plain `venv` + `pip` on M1 Max (Python 3.12 from Homebrew).
Poetry is optional for local dev — use `requirements.txt` directly:

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Architecture Reference

```
src/core/orchestrator/    PEV runner, step executor, rollback
src/core/planner.py       LLM task decomposition
src/core/executor.py      Shell / LLM / API execution
src/core/verifier.py      Quality gates
src/core/telemetry/       OTel + Prometheus instrumentation
src/auth/env_validator.py Startup env check (JWT_SECRET guard)
src/auth/session_manager.py  JWT secret resolution + min-bytes guard
src/core/auth_jwt.py      Edge-side JWT decode (no secret needed)
```
