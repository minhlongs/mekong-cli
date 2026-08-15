# Plugin Deployment Guide

**Last Updated**: 2026-06-22  
**Status**: Stable  
**Audience**: Plugin developers, DevOps engineers  
**Prerequisites**: Completed [Plugin Developer Onboarding](../plugin-developer-onboarding.md)

---

## Overview

This guide covers best practices for deploying Mekong CLI plugins to production environments. Mekong CLI plugins can be deployed to:

- **Cloudflare Workers** (recommended for most plugins)
- **Standalone servers** (for plugins with special system requirements)
- **Local development** (for testing and iteration)

## Deployment Options Comparison

| Feature | Cloudflare Workers | Standalone Server | Local Development |
|---------|-------------------|-------------------|-------------------|
| **Scalability** | Automatic, global | Manual scaling | Single machine |
| **Cost** | Pay-as-you-go, generous free tier | Fixed server costs | Free |
| **Performance** | Edge-located, <50ms latency | Depends on hosting | N/A |
| **Isolation** | Strong sandbox | Configurable | N/A |
| **Use Cases** | Most plugins | Heavy compute, custom binaries | Testing, debugging |

## Option 1: Cloudflare Workers Deployment

Cloudflare Workers is the recommended deployment target for Mekong CLI plugins. Workers provide:

- Zero infrastructure management
- Global edge network deployment
- Automatic scaling from 0 to millions of requests
- Built-in DDoS protection and WAF
- Generous free tier (100,000 requests/day)

### Prerequisites

1. **Cloudflare account** with Workers paid plan ($5/month minimum)
2. **Wrangler CLI** installed:
   ```bash
   npm install -g wrangler
   ```
3. **API token** with `Account > Workers & Pages > Edit` permission
4. **Plugin built** and validated (see [Plugin Development Guide](../plugin-developer-guide.md))

### Configuration

Create `wrangler.toml` in your plugin root:

```toml
name = "my-mekong-plugin"
main = "dist/worker.js"
compatibility_date = "2026-01-01"

# Environment variables (use wrangler secret for sensitive values)
[vars]
MEKONG_PLUGIN_ID = "com.example.myplugin"
MEKONG_PLUGIN_ENV = "production"

# Bindings for D1, KV, R2 if needed
[[d1_databases]]
binding = "DB"
database_name = "my-plugin-db"
database_id = "your-database-id"

[[kv_namespaces]]
binding = "CACHE"
id = "your-kv-namespace-id"
preview_id = "your-preview-kv-id"

# Secrets (set via wrangler secret put)
# MEKONG_API_KEY, DATABASE_URL, etc.
```

### Build Process

Mekong plugins must be bundled into a single JavaScript file compatible with Cloudflare Workers runtime.

#### For JavaScript/TypeScript Plugins:

```bash
# Install build dependencies
npm install --save-dev esbuild @cloudflare/workers-types

# Create production bundle
npx esbuild src/plugin.ts \
  --bundle \
  --platform=browser \
  --target=es2020 \
  --format=esm \
  --outfile=dist/worker.js \
  --minify \
  --sourcemap

# Verify bundle size (max 1MB for Workers)
ls -lh dist/worker.js
```

#### For Python Plugins (via Pyodide):

Mekong CLI Python plugins use Pyodide runtime on Workers:

```bash
# Package Python plugin
./scripts/package-pyodide.sh \
  --source src/plugin.py \
  --output dist/worker.js \
  --dependencies requirements.txt

# The script:
# 1. Downloads Pyodide
# 2. Installs Python dependencies in Pyodide environment
# 3. Packages .py file + dependencies into single JS bundle
```

#### Example `package-pyodide.sh`:

```bash
#!/bin/bash
set -e

SOURCE=$1
OUTPUT=$2
DEPS=$3

# Build Pyodide
docker run --rm -v $(pwd):/work -w /work pyodide/pyodide:latest \
  python -m pyodide_build \
  --source $SOURCE \
  --output $OUTPUT \
  --requirements $DEPS
```

### Deployment Steps

1. **Login to Cloudflare**:
   ```bash
   wrangler login
   ```

2. **Set required secrets** (never commit these):
   ```bash
   wrangler secret put MEKONG_API_KEY
   wrangler secret put DATABASE_URL
   wrangler secret put WEBHOOK_SECRET
   ```

   Input the secret values when prompted (they're encrypted at rest).

3. **Deploy to production**:
   ```bash
   # First deployment (may take 2-3 minutes)
   wrangler deploy

   # Output:
   # ✨ Success! Deployed to https://my-mekong-plugin.your-account.workers.dev
   ```

4. **Verify deployment**:
   ```bash
   # Test health endpoint
   curl https://my-mekong-plugin.your-account.workers.dev/health

   # Expected response:
   # {"status":"healthy","plugin":"com.example.myplugin","version":"1.0.0"}
   ```

5. **Configure custom domain** (optional):
   ```bash
   # In Cloudflare dashboard:
   # Workers & Pages → my-mekong-plugin → Triggers → Custom Domain
   # Add domain: plugin.example.com
   ```

6. **Register with Mekong CLI** (if not auto-discovered):
   ```bash
   mekong plugin register \
     --id com.example.myplugin \
     --url https://plugin.example.com \
     --version 1.0.0
   ```

### Environment Configuration

#### Production Environment Variables

Set via `wrangler secret put` (encrypted) or `wrangler.toml [vars]` (unencrypted, for non-sensitive values):

| Variable | Required | Description |
|----------|----------|-------------|
| `MEKONG_PLUGIN_ID` | Yes | Plugin manifest ID |
| `MEKONG_PLUGIN_ENV` | No | Environment name (production/staging) |
| `MEKONG_API_KEY` | Yes* | API key for plugin marketplace communication |
| `DATABASE_URL` | If using DB | Database connection string |
| `CACHE_TTL` | No | Cache time-to-live in seconds (default: 300) |
| `LOG_LEVEL` | No | Logging verbosity (info, warn, error, debug) |

*Required if plugin communicates with plugin marketplace or other plugins.

#### Configuration Binding (Alternative)

For complex configurations, use D1 database or KV store:

```toml
[[d1_databases]]
binding = "CONFIG_DB"
database_name = "plugin-config"
database_id = "${env:CONFIG_DB_ID}"

# Access in plugin code:
# const config = await CONFIG_DB.prepare("SELECT * FROM config WHERE plugin = ?").bind(PLUGIN_ID).first();
```

### Security Hardening for Production

1. **Enable Subresource Integrity (SRI)**:
   ```toml
   # In wrangler.toml
   [site]
   bucket = "./public"
   # Workers automatically includes SRI hashes for bundled code
   ```

2. **Configure CORS properly**:
   ```javascript
   // In plugin code
   export default {
     async fetch(request, env) {
       if (request.method === 'OPTIONS') {
         return Response.json({}, {
           headers: {
             'Access-Control-Allow-Origin': 'https://mekong.cli',
             'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
             'Access-Control-Allow-Headers': 'Content-Type,Authorization'
           }
         });
       }
       // ... normal handling
     }
   }
   ```

3. **Rate limiting**:
   ```javascript
   // Use Cloudflare's built-in rate limiting
   // Configure in Cloudflare dashboard: Security → Rate limiting rules
   // Rule: 100 requests per minute per IP for your-worker.your-account.workers.dev
   ```

4. **IP allowlisting** (if plugin only serves Mekong CLI):
   ```javascript
   const ALLOWED_IPS = ['104.18.34.193', '172.67.134.225']; // Mekong CLI IP ranges (check docs for current)

   export default {
     async fetch(request, env) {
       const ip = request.headers.get('CF-Connecting-IP');
       if (!ALLOWED_IPS.includes(ip)) {
         return new Response('Forbidden', { status: 403 });
       }
       // ... continue
     }
   }
   ```

### Monitoring & Observability

#### Health Checks

Expose a health check endpoint that Mekong CLI can poll:

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/health') {
      // Check database connectivity, external API health, etc.
      const health = {
        status: 'healthy',
        plugin: env.MEKONG_PLUGIN_ID,
        version: '1.0.0',
        timestamp: new Date().toISOString(),
        checks: {
          database: await checkDatabase(),
          external_api: await checkExternalAPI()
        }
      };

      const isHealthy = Object.values(health.checks).every(check => check === 'ok');
      return Response.json(health, {
        status: isHealthy ? 200 : 503,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    // ... regular request handling
  }
};
```

#### Logging

Cloudflare Workers logs to `console.log()`, `console.warn()`, `console.error()`:

```javascript
export default {
  async fetch(request, env) {
    console.log(`[${env.MEKONG_PLUGIN_ID}] Request: ${request.method} ${request.url}`);

    try {
      const result = await handleRequest(request, env);
      console.log(`[${env.MEKONG_PLUGIN_ID}] Response: ${result.status}`);
      return result;
    } catch (error) {
      console.error(`[${env.MEKONG_PLUGIN_ID}] Error:`, error);
      return new Response('Internal Server Error', { status: 500 });
    }
  }
};
```

View logs:

```bash
# Real-time logs
wrangler tail

# Filter by log level
wrangler tail --format json | jq 'select(.level == "ERROR")'
```

#### Metrics & Telemetry

The plugin health monitoring system expects plugins to expose metrics:

```javascript
export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === '/metrics') {
      const metrics = `
        # HELP plugin_requests_total Total number of requests
        # TYPE plugin_requests_total counter
        plugin_requests_total{plugin="${env.MEKONG_PLUGIN_ID}"} ${env.REQUEST_COUNT || 0}

        # HELP plugin_errors_total Total number of errors
        # TYPE plugin_errors_total counter
        plugin_errors_total{plugin="${env.MEKONG_PLUGIN_ID}"} ${env.ERROR_COUNT || 0}

        # HELP plugin_response_time_ms Average response time in milliseconds
        # TYPE plugin_response_time_ms gauge
        plugin_response_time_ms{plugin="${env.MEKONG_PLUGIN_ID}"} ${env.AVG_RESPONSE_TIME || 0}
      `;

      return new Response(metrics, {
        headers: { 'Content-Type': 'text/plain; version=0.0.4' }
      });
    }

    // ... regular handling
  }
};
```

See [Plugin Health Monitoring Operations Guide](../plugin-health-monitoring-operations.md) for complete metrics specification.

### CI/CD Pipeline

Example GitHub Actions workflow for Cloudflare Workers deployment:

```yaml
name: Deploy Plugin to Cloudflare Workers

on:
  push:
    branches: [main]
    tags: ['v*']
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: Validate manifest
        run: |
          python3 scripts/validate-manifest.py plugin.json

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Install Wrangler
        run: npm install -g wrangler
      - name: Deploy to Workers
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
        run: |
          wrangler deploy --minify
```

### Rollback Procedures

If a deployment introduces issues:

```bash
# Option 1: Rollback to previous version using wrangler
wrangler rollback

# Option 2: Manually redeploy previous version
git checkout v1.0.0
wrangler deploy
git checkout main

# Option 3: Use Cloudflare dashboard
# Workers & Pages → your plugin → Versions → Deploy previous
```

See [Rollback Procedures](../rollback-procedures.md) for comprehensive rollback strategies.

## Option 2: Standalone Server Deployment

Use standalone servers for plugins that require:

- System-level access (e.g., custom binaries, hardware)
- Persistent large-scale storage
- Specialized networking (VPN, private network)
- Long-running background processes

### Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 1 core | 2+ cores |
| **Memory** | 512 MB | 2+ GB |
| **Storage** | 1 GB | 10+ GB SSD |
| **OS** | Ubuntu 22.04+ | Ubuntu 24.04 LTS |
| **Network** | 1 Gbps | 10 Gbps |

### Docker Deployment

Build Docker image:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy plugin code
COPY . .

# Expose port
EXPOSE 8080

# Run plugin server
CMD ["python", "-m", "mekong_plugin.server", "--host", "0.0.0.0", "--port", "8080"]
```

Build and push:

```bash
docker build -t your-registry/com.example.myplugin:1.0.0 .
docker push your-registry/com.example.myplugin:1.0.0
```

Run with docker-compose:

```yaml
version: '3.8'
services:
  plugin:
    image: your-registry/com.example.myplugin:1.0.0
    environment:
      - MEKONG_PLUGIN_ID=com.example.myplugin
      - MEKONG_PLUGIN_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Start:

```bash
docker-compose up -d
docker-compose logs -f
```

### Systemd Service

For direct server deployment (no Docker):

```ini
# /etc/systemd/system/mekong-plugin.service
[Unit]
Description=Mekong Plugin: com.example.myplugin
After=network.target postgresql.service

[Service]
Type=simple
User=mekong
Group=mekong
WorkingDirectory=/opt/mekong-plugins/com.example.myplugin
Environment="MEKONG_PLUGIN_ID=com.example.myplugin"
Environment="MEKONG_PLUGIN_ENV=production"
EnvironmentFile=/opt/mekong-plugins/com.example.myplugin/.env
ExecStart=/usr/bin/python3 -m mekong_plugin.server --host 127.0.0.1 --port 8080
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mekong-plugin
sudo systemctl start mekong-plugin
sudo systemctl status mekong-plugin
```

### Nginx Reverse Proxy

```nginx
upstream mekong_plugin_com_example_myplugin {
    server 127.0.0.1:8080;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name plugin.example.com;

    ssl_certificate /etc/letsencrypt/live/plugin.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/plugin.example.com/privkey.pem;

    location / {
        proxy_pass http://mekong_plugin_com_example_myplugin;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint (bypass proxy)
    location /health {
        proxy_pass http://127.0.0.1:8080/health;
        access_log off;
    }
}
```

## Option 3: Local Development Deployment

For testing and development, run the plugin locally:

```bash
# Install Mekong CLI plugin server
pip install mekong-plugin-server

# Or if developing plugin directly:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run development server with hot reload
mekong-plugin-server --host 127.0.0.1 --port 8080 --reload --debug

# Server auto-restarts when files change (uses watchdog)
```

Register with local Mekong CLI:

```bash
mekong plugin register \
  --id com.example.myplugin \
  --url http://localhost:8080 \
  --version 1.0.0 \
  --staging
```

## Environment Variables Reference

Complete list of environment variables supported by Mekong plugin runtime:

| Variable | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `MEKONG_PLUGIN_ID` | string | Yes | - | Plugin manifest ID |
| `MEKONG_PLUGIN_ENV` | string | No | development | Environment name |
| `MEKONG_API_KEY` | string | Conditional | - | API key for marketplace (required for production) |
| `MEKONG_PLUGIN_PORT` | integer | No | 8080 | Server listen port |
| `MEKONG_PLUGIN_HOST` | string | No | 127.0.0.1 | Server bind address |
| `DATABASE_URL` | string | If using DB | - | Database connection string |
| `LOG_LEVEL` | string | No | info | Logging level (debug, info, warn, error) |
| `CACHE_TTL` | integer | No | 300 | Cache time-to-live in seconds |
| `REDIS_URL` | string | If using Redis | - | Redis connection URL |
| `SENTRY_DSN` | string | Optional | - | Sentry DSN for error tracking |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | string | Optional | - | OpenTelemetry endpoint |

## Deployment Checklist

Before marking a plugin deployment as complete:

- [ ] Manifest validates against `factory/contracts/plugin-system/plugin-manifest-schema.json`
- [ ] All required secrets configured in deployment platform
- [ ] Health check endpoint returns `200 OK` with valid JSON
- [ ] `/metrics` endpoint exposes Prometheus metrics (if monitoring enabled)
- [ ] Rate limiting configured (Cloudflare dashboard or nginx)
- [ ] CORS headers set correctly for allowed origins
- [ ] SSL/TLS configured (automatic with Cloudflare Workers)
- [ ] Log aggregation configured (wrangler tail, Loki, Cloudflare Logpush)
- [ ] Error tracking configured (Sentry or similar)
- [ ] Load testing performed (see [Load Testing Guide](../load-testing.md))
- [ ] Security scan completed (see [Security Hardening Guide](../plugin-security-hardening.md))
- [ ] Documentation updated with deployment-specific details
- [ ] Plugin registered in Mekong CLI marketplace
- [ ] Team members have access to deployment platform and secrets

## Troubleshooting

### Worker fails to deploy with "Module not found" error

**Cause**: Missing or incorrect `main` path in `wrangler.toml`.

**Fix**: Verify `main` points to existing JavaScript file:

```bash
ls -lh dist/worker.js  # Should exist
```

Update `wrangler.toml`:

```toml
main = "dist/worker.js"  # Correct path
```

### Plugin unreachable after deployment

**Diagnosis**:

```bash
# 1. Check Worker status
wrangler whoami
wrangler deployments list

# 2. Test endpoint directly
curl -v https://your-plugin.your-account.workers.dev/health

# 3. Check Cloudflare dashboard for errors
# Workers & Pages → your plugin → Metrics → Errors
```

**Fix**: If Worker shows as "Disabled", re-deploy or check billing status.

### Health check failing

**Check**:

```bash
# View logs
wrangler tail

# Test health endpoint manually
curl https://your-plugin.your-account.workers.dev/health

# Check database connectivity in plugin code
# Ensure DATABASE_URL secret is set
wrangler secret list
```

**Fix**: Verify all required environment variables and bindings are configured.

### Performance issues

**Diagnosis**:

```bash
# Check response times
curl -w "\nTime: %{time_total}s\n" https://your-plugin.your-account.workers.dev/your-endpoint

# Check Worker metrics in Cloudflare dashboard
# Workers & Pages → your plugin → Metrics → Requests, Duration, Errors
```

**Optimization**:

- Enable caching with `Cache-Control` headers
- Use KV store for frequent reads
- Implement connection pooling for databases
- Review bundle size (keep under 1MB)

See [Performance Tuning Guide](../performance-tuning.md) for detailed optimization strategies.

### Secrets not available in Worker

**Problem**: `wrangler secret put` didn't set the secret correctly.

**Check**:

```bash
wrangler secret list
# Should show your secret names (values hidden)
```

**Fix**: Re-set the secret:

```bash
wrangler secret put MEKONG_API_KEY
# Paste value when prompted
```

Restart Worker after setting secrets:

```bash
wrangler deploy
```

## Cost Optimization

Cloudflare Workers pricing (as of 2026):

- **Free tier**: 100,000 requests/day
- **Paid plan**: $5/month minimum, then $0.30 per million requests beyond free tier
- **D1 database**: $0.20 per GB-month storage + $0.40 per million reads + $2.00 per million writes
- **KV store**: $0.20 per GB-month storage + $0.40 per million reads + $5.00 per million writes
- **R2 storage**: $0.015 per GB-month storage + egress at $0.01/GB

**Cost optimization tips**:

1. **Cache aggressively**: Use KV store and HTTP caching to reduce compute and database reads
2. **Bundle efficiently**: Smaller Worker bundle = faster cold starts = lower resource usage
3. **Optimize D1 queries**: Use indexes, avoid N+1 queries
4. **Batch operations**: Process multiple items in single database transaction
5. **Monitor usage**: Set up Cloudflare alerts for spend thresholds

See [Cost Optimization Checklist](../cost-optimization-checklist.md) for comprehensive guidance.

## Security Considerations

1. **Never commit secrets** to version control. Use `wrangler secret put`.
2. **Validate all inputs** from external requests; Workers sandbox is not a security boundary for your application logic.
3. **Implement authentication** if plugin exposes non-public endpoints.
4. **Use minimum required permissions** for Cloudflare API token.
5. **Enable audit logging** in Cloudflare dashboard (Workers → your Worker → Logs).
6. **Regularly rotate API keys** and review access logs.
7. **Apply security patches** to dependencies regularly (`npm audit`, `pip list --outdated`).

See [Plugin Security Hardening Guide](../plugin-security-hardening.md) for comprehensive security checklist.

## Post-Deployment Validation

After deployment, run the post-deployment validation checklist:

```bash
# 1. Health check
curl -f https://your-plugin.your-account.workers.dev/health

# 2. Metrics endpoint
curl https://your-plugin.your-account.workers.dev/metrics | grep plugin_requests_total

# 3. Test core functionality
mekong plugin invoke com.example.myplugin --test-command

# 4. Check logs for errors
wrangler tail --since 5m | grep -i error

# 5. Verify marketplace registration
mekong plugin list | grep com.example.myplugin
```

## Next Steps

- Configure monitoring and alerting: See [Plugin Health Monitoring Operations Guide](../plugin-health-monitoring-operations.md)
- Set up automated testing: See [Testing Guide](../testing-guide.md)
- Implement performance optimizations: See [Performance Tuning Guide](../performance-tuning.md)
- Review security best practices: See [Plugin Security Hardening Guide](../plugin-security-hardening.md)
- Contribute to plugin marketplace: See [Marketplace Monetization System](../marketplace-monetization-system.md)

## Related Documentation

- [Plugin Developer Guide](../plugin-developer-guide.md)
- [Plugin Manifest Format Reference](../plugin-manifest-format.md)
- [Plugin Health Monitoring Operations Guide](../plugin-health-monitoring-operations.md)
- [Rollback Procedures](../rollback-procedures.md)
- [Cloudflare Workers Deployment Guide](../cloudflare-deployment-guide.md)
- [Configuration Reference](../configuration-reference.md)

---

**Need help?** Contact the plugin team in `#plugin-dev` on Discord or email plugins@mekong.cli.
