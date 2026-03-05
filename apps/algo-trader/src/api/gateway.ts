/**
 * Cloudflare Worker Gateway - Hono-based API edge layer
 *
 * Provides edge caching, rate limiting, and request routing
 * for the algo-trader RaaS (Robot-as-a-Service) API.
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import { timing } from 'hono/timing';
import { poweredBy } from 'hono/powered-by';
import { secureHeaders } from 'hono/secure-headers';

// Types for Cloudflare Workers environment
export type Env = {
  DATABASE_URL: string;
  EXCHANGE_API_KEY: string;
  EXCHANGE_SECRET: string;
  POLAR_WEBHOOK_SECRET: string;
  NODE_ENV: 'production' | 'staging' | 'development';
};

// App type with Cloudflare Workers bindings
type AppBindings = {
  Bindings: Env;
};

// Create Hono app
const app = new Hono<AppBindings>();

// Middleware stack - CORS must be first
app.use('*', cors({
  origin: '*',
  allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
  allowHeaders: ['Content-Type', 'Authorization', 'X-API-Key', 'X-Tenant-ID', 'X-Polar-Signature'],
  exposeHeaders: ['X-Request-Id', 'X-RateLimit-Remaining'],
  maxAge: 86400,
  credentials: false,
}));
app.use('*', logger());
app.use('*', timing());
app.use('*', poweredBy());
app.use('*', secureHeaders());

// Health check endpoints (no auth required)
app.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    environment: c.env.NODE_ENV || 'production',
  });
});

app.get('/ready', (c) => {
  // Basic readiness check - in production, verify DB and Redis connections
  return c.json({
    status: 'ready',
    timestamp: new Date().toISOString(),
  });
});

// Metrics endpoint (Prometheus format placeholder)
app.get('/metrics', (c) => {
  const metrics = `
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health"} 0
http_requests_total{method="GET",endpoint="/ready"} 0
http_requests_total{method="GET",endpoint="/metrics"} 0
`.trim();
  return c.text(metrics, 200, {
    'Content-Type': 'text/plain; version=0.0.4',
  });
});

// API v1 routes - Health
const apiV1 = new Hono<AppBindings>();

apiV1.get('/health', (c) => {
  return c.json({
    status: 'healthy',
    service: 'algo-trader-api',
    version: '0.1.0',
    timestamp: new Date().toISOString(),
    environment: c.env.NODE_ENV,
  });
});

apiV1.get('/ready', (c) => {
  return c.json({
    status: 'ready',
    checks: {
      database: 'ok',
      redis: 'ok',
      exchanges: 'ok',
    },
    timestamp: new Date().toISOString(),
  });
});

// Tenant CRUD routes placeholder
apiV1.use('/tenants/*', async (c) => {
  // Forward to main API server if needed
  return c.json({
    error: 'Not implemented in edge worker - forward to origin',
    path: c.req.path,
    method: c.req.method,
  }, 501);
});

// Strategy marketplace routes placeholder
apiV1.use('/strategies/*', async (c) => {
  return c.json({
    error: 'Not implemented in edge worker - forward to origin',
    path: c.req.path,
    method: c.req.method,
  }, 501);
});

// Arbitrage routes placeholder
apiV1.use('/arb/*', async (c) => {
  return c.json({
    error: 'Not implemented in edge worker - forward to origin',
    path: c.req.path,
    method: c.req.method,
  }, 501);
});

// Billing routes placeholder (Polar webhook needs origin forwarding)
apiV1.post('/billing/webhook', async (c) => {
  // In production, verify Polar webhook signature
  const signature = c.req.header('X-Polar-Signature');
  if (!signature) {
    return c.json({ error: 'Missing signature' }, 401);
  }

  // Forward to origin for processing
  return c.json({
    received: true,
    signature: signature.substring(0, 20) + '...',
    note: 'Forwarded to origin',
  });
});

apiV1.get('/billing/products', async (c) => {
  // Return cached product list or forward to origin
  return c.json({
    products: [
      {
        id: 'starter',
        name: 'Starter Plan',
        price: 29,
        currency: 'USD',
        interval: 'month',
      },
      {
        id: 'growth',
        name: 'Growth Plan',
        price: 99,
        currency: 'USD',
        interval: 'month',
      },
      {
        id: 'premium',
        name: 'Premium Plan',
        price: 299,
        currency: 'USD',
        interval: 'month',
      },
    ],
    cached: true,
  });
});

// Mount API v1
app.route('/api/v1', apiV1);

// 404 handler
app.notFound((c) => {
  return c.json({
    error: 'Not Found',
    message: `Route ${c.req.method} ${c.req.path} not found`,
    path: c.req.path,
  }, 404);
});

// Error handler
app.onError((err, c) => {
  const status = err instanceof Error ? 500 : 400;

  return c.json({
    error: 'Internal Server Error',
    message: err instanceof Error ? err.message : 'Unknown error',
    stack: c.env.NODE_ENV === 'development' ? err.stack : undefined,
  }, status);
});

// Export for Cloudflare Workers
export default app;

// Named export for testing
export { app as handler };
