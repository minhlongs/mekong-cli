# Sentry Error Tracking Setup

This document describes the Sentry error tracking and performance monitoring setup for Mekong CLI.

## Architecture

Sentry is configured across all layers of the stack:

| Component | Sentry SDK | Configuration |
|-----------|------------|---------------|
| Python Gateway (FastAPI) | `sentry-sdk` | `src/core/sentry_init.py` |
| Python Dashboard API | `sentry-sdk` | `src/core/sentry_init.py` + `SentryContextMiddleware` |
| Next.js Frontend | `@sentry/nextjs` | `sentry.client.config.ts`, `sentry.server.config.ts` |

## Environment Variables

### Backend (Python)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `SENTRY_DSN` | Sentry project DSN | Yes for production | `https://xxx@o0.ingest.sentry.io/0` |
| `ENVIRONMENT` | Deployment environment | No (default: development) | `production`, `staging`, `development` |
| `APP_VERSION` | Release version | No (default: 0.0.0) | `3.3.0` |
| `MEKONG_ENV` | Mekong environment (overrides ENVIRONMENT) | No | `production` |

### Frontend (Next.js)

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN (public) | Yes for production | `https://xxx@o0.ingest.sentry.io/0` |
| `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | Environment | No (default: development) | `production` |
| `NEXT_PUBLIC_SENTRY_RELEASE` | Release version | No | `3.3.0+gabc123` |

## Configuration Details

### Python Backend

The Sentry initialization is in `src/core/sentry_init.py`. Features:

- **PII Scrubbing**: Automatic removal of sensitive data (passwords, tokens, emails, API keys)
- **Tenant Context**: User and tenant information attached to all events
- **Performance Monitoring**: Distributed tracing with 10% sample rate in production
- **Logging Integration**: Logs captured as breadcrumbs (ERROR level sent as events)
- **Environment Detection**: Uses `MEKONG_ENV` or `ENVIRONMENT` to determine environment

Sample rates by environment:
- `production`: traces 10%, profiles 5%
- `staging`: traces 20%, profiles 10%
- `development`: traces 100%, profiles 100%

#### User Context

User context is set by:
- **Gateway**: `license_gate` dependency sets user from JWT claims
- **Dashboard**: `SessionMiddleware` + `SentryContextMiddleware` reads `request.state.user`

### Frontend (Next.js)

The frontend uses `@sentry/nextjs` with separate client and server configs:

- **Client**: Captures React errors, unhandled promise rejections
- **Server**: Captures SSR and API route errors

Configuration files:
- `sentry.client.config.ts`: Browser error handling
- `sentry.server.config.ts`: Server-side error handling
- `next.config.mjs`: Enabled via `sentry` property

#### Error Boundary

The `ErrorBoundary` component wraps the entire app in `app/layout.tsx`:
- Catches React component errors
- Shows a user-friendly fallback UI
- Reports errors to Sentry with event ID displayed

## Deploying to Production

### 1. Create Sentry Project

1. Go to [Sentry.io](https://sentry.io) and create an account
2. Create a new project for each component:
   - `mekong-gateway` (Python/FastAPI)
   - `mekong-dashboard` (Next.js frontend)
3. Copy the DSN for each project

### 2. Configure Backend

Add to production environment (e.g., systemd service, Docker env, or Cloudflare Workers):

```bash
SENTRY_DSN=https://your-dsn@o0.ingest.sentry.io/0
ENVIRONMENT=production
APP_VERSION=3.3.0  # or your current version
```

For Cloudflare Workers deployment, add to `wrangler.toml`:

```toml
[vars]
SENTRY_DSN = "https://your-dsn@o0.ingest.sentry.io/0"
ENVIRONMENT = "production"
```

### 3. Configure Frontend

Add to `.env.local` (or production environment):

```bash
NEXT_PUBLIC_SENTRY_DSN=https://your-dsn@o0.ingest.sentry.io/0
NEXT_PUBLIC_SENTRY_ENVIRONMENT=production
```

### 4. Verify Setup

Test that Sentry is working:

```bash
# Python backend test
python3 -c "from src.core.sentry_init import init_sentry; init_sentry(); import sentry_sdk; sentry_sdk.capture_message('Sentry test from Mekong Gateway')"

# Frontend: trigger an error in browser console:
#   throw new Error('Test Sentry error');
#   // or use Sentry.captureException(new Error('Test'))
```

Check the Sentry dashboard for incoming events.

## Security Considerations

### PII Scrubbing

Both backend and frontend automatically scrub:
- Authorization headers
- Cookies
- API keys and tokens
- Passwords
- Email addresses (masked: `ab***@domain.com`)
- Credit card numbers

### GDPR Compliance

- Set `send_default_pii=False` (default) - no IP addresses or user data sent unless explicitly set
- User email masking protects user identity
- Can disable Sentry entirely by omitting `SENTRY_DSN`

### Rate Limiting

Sample rates are configurable via environment:
- Reduce `traces_sample_rate` to lower costs in production
- Set `profiles_sample_rate` to 0 to disable performance profiling

## Troubleshooting

### Events Not Appearing in Sentry

1. Check DSN is correctly set and reachable
2. Verify network connectivity to `sentry.io`
3. Check that the event wasn't filtered by PII scrubbing
4. Ensure `SENTRY_DSN` is not set to empty string or test DSN

### High Volume of Events

Adjust sample rates:
- Python: Modify `_get_sample_rates()` in `sentry_init.py`
- Frontend: Set `tracesSampleRate` lower in config files

### Performance Impact

- SDK initialization: ~50ms at startup
- Event capture: async, non-blocking
- Tracing: adds ~5-10ms overhead per transaction

## Release Tracking

Releases are automatically tracked using `APP_VERSION`. To get full release health:

1. Configure source maps upload for frontend:
   ```bash
   pnpm --filter mekong-dashboard sentry-upload-source-maps
   ```

2. Use consistent version format: `MAJOR.MINOR.PATCH+git.sha`

## Support

For issues with Sentry integration:
1. Check logs for Sentry initialization messages
2. Verify the Sentry SDK version (`pip show sentry-sdk`, `pnpm list @sentry/nextjs`)
3. Consult [Sentry Python docs](https://docs.sentry.io/platforms/python/) and [Next.js docs](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
