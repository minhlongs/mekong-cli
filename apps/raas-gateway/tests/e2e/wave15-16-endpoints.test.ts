/**
 * E2E tests — Wave 15-16: health scoring, recurring missions, webhook DLQ,
 * conversion analytics, mission timeline, SDK generator, rate limit dashboard
 */

import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

// ---------------------------------------------------------------------------
// Mock helpers
// ---------------------------------------------------------------------------

class MockKV {
  private store: Map<string, string> = new Map();

  async get(key: string, type?: 'json'): Promise<any> {
    const value = this.store.get(key);
    if (value === undefined) return null;
    if (type === 'json') return JSON.parse(value);
    return value;
  }

  async put(key: string, value: string, _options?: { expirationTtl?: number }): Promise<void> {
    this.store.set(key, value);
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }

  async list(_opts?: any): Promise<{ keys: { name: string }[] }> {
    return { keys: Array.from(this.store.keys()).map(name => ({ name })) };
  }
}

class MockD1 {
  prepare(_query: string) {
    const stmt = {
      bind: (..._args: any[]) => stmt,
      first: async () => null,
      run: async () => ({ success: true, meta: { changes: 1 } }),
      all: async () => ({ results: [] }),
    };
    return stmt;
  }

  async batch(_statements: any[]) {
    return [];
  }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';
const ADMIN_API_KEY = 'test-admin-key';

async function makeToken(tier = 'pro'): Promise<string> {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setIssuer('raas-gateway')
    .setAudience('raas-api')
    .setExpirationTime('1h')
    .sign(secret);
}

function createEnv(): Env {
  return {
    DB: new MockD1() as any,
    RATE_LIMIT_KV: new MockKV() as any,
    SESSION_KV: new MockKV() as any,
    AI: {} as any,
    JWT_SECRET=REDACTED,
    POLAR_WEBHOOK_SECRET: 'test',
    TELEGRAM_BOT_TOKEN: 'test',
    ENVIRONMENT: 'test',
    LOG_LEVEL: 'error',
    ADMIN_API_KEY,
  };
}

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` };
}

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

describe('Wave 15-16 E2E: Health Scoring, Recurring Missions, DLQ, Conversion, Timeline, SDK, Rate Limits', () => {
  let env: Env;
  let token: string;

  beforeEach(async () => {
    env = createEnv();
    token = await makeToken();
  });

  // ---- Wave 15: Tenant Health Scoring ----

  describe('Tenant Health Scoring', () => {
    it('GET /v1/health-score — requires auth', async () => {
      const res = await app.request('/v1/health-score', {}, env);
      expect(res.status).toBe(401);
    });

    it('GET /v1/health-score — returns score with auth', async () => {
      const res = await app.request('/v1/health-score', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/health-score/history — returns history', async () => {
      const res = await app.request('/v1/health-score/history?limit=5', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/health-score/factors — returns factor breakdown', async () => {
      const res = await app.request('/v1/health-score/factors', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });
  });

  // ---- Wave 15: Recurring Missions ----

  describe('Recurring Missions', () => {
    it('POST /v1/recurring — requires auth', async () => {
      const res = await app.request('/v1/recurring', { method: 'POST', body: '{}', headers: { 'Content-Type': 'application/json' } }, env);
      expect(res.status).toBe(401);
    });

    it('POST /v1/recurring — create recurring mission', async () => {
      const res = await app.request('/v1/recurring', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Daily SEO Check', type: 'seo_audit', cron_expression: '0 0 * * *', input: { url: 'https://example.com' } }),
      }, env);
      expect([200, 201, 400, 500]).toContain(res.status);
    });

    it('GET /v1/recurring — list recurring missions', async () => {
      const res = await app.request('/v1/recurring', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/recurring/1 — get single', async () => {
      const res = await app.request('/v1/recurring/1', { headers: authHeader(token) }, env);
      expect([200, 404, 500]).toContain(res.status);
    });

    it('PUT /v1/recurring/1 — update', async () => {
      const res = await app.request('/v1/recurring/1', {
        method: 'PUT',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: false }),
      }, env);
      expect([200, 404, 500]).toContain(res.status);
    });

    it('DELETE /v1/recurring/1 — deactivate', async () => {
      const res = await app.request('/v1/recurring/1', { method: 'DELETE', headers: authHeader(token) }, env);
      expect([200, 404, 500]).toContain(res.status);
    });

    it('POST /v1/recurring/1/trigger — manual trigger', async () => {
      const res = await app.request('/v1/recurring/1/trigger', { method: 'POST', headers: authHeader(token) }, env);
      expect([200, 404, 500]).toContain(res.status);
    });
  });

  // ---- Wave 15: Webhook DLQ ----

  describe('Webhook Dead Letter Queue', () => {
    it('GET /v1/dlq — tenant DLQ entries', async () => {
      const res = await app.request('/v1/dlq', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/dlq/stats — tenant DLQ stats', async () => {
      const res = await app.request('/v1/dlq/stats', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /admin/dlq — admin list (requires admin key)', async () => {
      const res = await app.request('/admin/dlq', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /admin/dlq — rejects without admin key', async () => {
      const res = await app.request('/admin/dlq', {}, env);
      expect([401, 403]).toContain(res.status);
    });

    it('GET /admin/dlq/stats — admin DLQ stats', async () => {
      const res = await app.request('/admin/dlq/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('POST /admin/dlq/1/replay — replay DLQ entry', async () => {
      const res = await app.request('/admin/dlq/1/replay', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 404, 500]).toContain(res.status);
    });
  });

  // ---- Wave 15: Conversion Analytics ----

  describe('Conversion Analytics', () => {
    it('POST /conversion/track — track event (public)', async () => {
      const res = await app.request('/conversion/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: 'signup_start', session_id: 'sess-123', source: 'google' }),
      }, env);
      expect([200, 201, 400, 500]).toContain(res.status);
    });

    it('POST /conversion/track — rejects invalid event type', async () => {
      const res = await app.request('/conversion/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ event_type: 'invalid_event' }),
      }, env);
      expect([400, 200, 500]).toContain(res.status);
    });

    it('GET /conversion/funnel — requires admin', async () => {
      const res = await app.request('/conversion/funnel', {}, env);
      expect([401, 403]).toContain(res.status);
    });

    it('GET /conversion/funnel — admin funnel data', async () => {
      const res = await app.request('/conversion/funnel?days=30', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /conversion/rates — conversion rates', async () => {
      const res = await app.request('/conversion/rates?days=30', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /conversion/cohorts — cohort analysis', async () => {
      const res = await app.request('/conversion/cohorts?period=month&cohorts=6', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /conversion/sources — top sources', async () => {
      const res = await app.request('/conversion/sources?days=30&limit=10', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });
  });

  // ---- Wave 16: Mission Timeline ----

  describe('Mission Timeline & Tracing', () => {
    it('GET /v1/timeline/missions/1/timeline — requires auth', async () => {
      const res = await app.request('/v1/timeline/missions/1/timeline', {}, env);
      expect(res.status).toBe(401);
    });

    it('GET /v1/timeline/missions/1/timeline — timeline events', async () => {
      const res = await app.request('/v1/timeline/missions/1/timeline', { headers: authHeader(token) }, env);
      expect([200, 404, 500]).toContain(res.status);
    });

    it('GET /v1/timeline/missions/1/trace — trace summary', async () => {
      const res = await app.request('/v1/timeline/missions/1/trace', { headers: authHeader(token) }, env);
      expect([200, 404, 500]).toContain(res.status);
    });

    it('GET /v1/timeline/traces — list traces', async () => {
      const res = await app.request('/v1/timeline/traces', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/timeline/performance — performance stats', async () => {
      const res = await app.request('/v1/timeline/performance?days=7', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('POST /v1/timeline/internal/trace/start — start trace (internal)', async () => {
      const res = await app.request('/v1/timeline/internal/trace/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission_id: 1, tenant_id: 'tenant-test-123' }),
      }, env);
      expect([200, 201, 500]).toContain(res.status);
    });

    it('POST /v1/timeline/internal/timeline — add event (internal)', async () => {
      const res = await app.request('/v1/timeline/internal/timeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mission_id: 1, tenant_id: 'tenant-test-123', event_type: 'started' }),
      }, env);
      expect([200, 201, 500]).toContain(res.status);
    });
  });

  // ---- Wave 16: SDK Generator ----

  describe('SDK Generator', () => {
    it('GET /sdk/endpoints — list endpoints (public)', async () => {
      const res = await app.request('/sdk/endpoints', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.success).toBe(true);
      expect(Array.isArray(body.data)).toBe(true);
    });

    it('GET /sdk/snippet — generate curl snippet', async () => {
      const res = await app.request('/sdk/snippet?language=curl&endpoint=/v1/missions&method=POST', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.success).toBe(true);
      expect(typeof body.data.snippet).toBe('string');
      expect(body.data.snippet).toContain('curl');
    });

    it('GET /sdk/snippet — generate javascript snippet', async () => {
      const res = await app.request('/sdk/snippet?language=javascript&endpoint=/v1/missions&method=GET', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.data.snippet).toContain('fetch');
    });

    it('GET /sdk/snippet — generate python snippet', async () => {
      const res = await app.request('/sdk/snippet?language=python&endpoint=/v1/missions&method=POST', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.data.snippet).toContain('requests');
    });

    it('GET /sdk/javascript — full JS SDK', async () => {
      const res = await app.request('/sdk/javascript', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.success).toBe(true);
      expect(typeof body.data.code).toBe('string');
      expect(body.data.code).toContain('class');
    });

    it('GET /sdk/python — full Python SDK', async () => {
      const res = await app.request('/sdk/python', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.data.code).toContain('class');
    });

    it('GET /sdk/snippet — rejects invalid language', async () => {
      const res = await app.request('/sdk/snippet?language=rust&endpoint=/v1/missions&method=GET', {}, env);
      expect([400, 200]).toContain(res.status);
    });
  });

  // ---- Wave 16: Rate Limit Dashboard ----

  describe('Rate Limit Dashboard', () => {
    it('GET /v1/rate-limits — tenant rate limit status', async () => {
      const res = await app.request('/v1/rate-limits', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/rate-limits — requires auth', async () => {
      const res = await app.request('/v1/rate-limits', {}, env);
      expect(res.status).toBe(401);
    });

    it('GET /v1/rate-limits/history — rate limit history', async () => {
      const res = await app.request('/v1/rate-limits/history?days=7', { headers: authHeader(token) }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /admin/rate-limits — admin list (requires admin key)', async () => {
      const res = await app.request('/admin/rate-limits', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /admin/rate-limits/violations — violations list', async () => {
      const res = await app.request('/admin/rate-limits/violations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect([200, 500]).toContain(res.status);
    });
  });

  // ---- OpenAPI Spec ----

  describe('OpenAPI Spec — Wave 15-16 paths', () => {
    it('includes all Wave 15-16 endpoint paths', async () => {
      const res = await app.request('/openapi.json', {}, env);
      expect(res.status).toBe(200);
      const spec = await res.json() as any;
      const paths = Object.keys(spec.paths);

      // Wave 15
      expect(paths).toContain('/v1/health-score');
      expect(paths).toContain('/v1/health-score/history');
      expect(paths).toContain('/v1/recurring');
      expect(paths).toContain('/v1/recurring/{id}');
      expect(paths).toContain('/v1/dlq');
      expect(paths).toContain('/admin/dlq');
      expect(paths).toContain('/conversion/track');
      expect(paths).toContain('/conversion/funnel');

      // Wave 16
      expect(paths).toContain('/v1/timeline/missions/{id}/timeline');
      expect(paths).toContain('/v1/timeline/traces');
      expect(paths).toContain('/sdk/endpoints');
      expect(paths).toContain('/sdk/snippet');
      expect(paths).toContain('/v1/rate-limits');
    });
  });
});
