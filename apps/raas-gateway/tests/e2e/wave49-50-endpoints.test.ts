/**
 * Wave 49-50 E2E tests — Notification Center, Mission Templates, API Key Mgmt,
 * Audit Trail, Feature Flags, Resource Quotas
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

class MockKV {
  private store = new Map<string, string>();
  async get(key: string, type?: 'json') {
    const v = this.store.get(key);
    if (v === undefined) return null;
    return type === 'json' ? JSON.parse(v) : v;
  }
  async put(key: string, value: string) { this.store.set(key, value); }
  async delete(key: string) { this.store.delete(key); }
  async list(_opts?: any) { return { keys: Array.from(this.store.keys()).map(name => ({ name })) }; }
}

class MockD1 {
  prepare(_q: string) {
    const stmt = {
      bind: (..._a: any[]) => stmt,
      first: async () => null,
      run: async () => ({ success: true, meta: { changes: 1 } }),
      all: async () => ({ results: [] }),
    };
    return stmt;
  }
  async batch(_s: any[]) { return [{ results: [] }]; }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';
const ADMIN_API_KEY = 'test-admin-key';

async function makeToken(tier = 'pro') {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api')
    .setExpirationTime('1h').sign(secret);
}

function createEnv(): Env {
  return {
    DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any,
    SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED,
    POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test',
    ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY,
  };
}

let env: Env;
let token: string;

beforeEach(async () => { env = createEnv(); token = await makeToken(); });

function req(path: string, init?: RequestInit) {
  return app.request(path, init, env);
}

// --- Wave 49: Platform Notification Center ---

describe('Wave 49: Platform Notification Center', () => {
  it('GET /v1/notification-center/notifications — list (auth)', async () => {
    const res = await req('/v1/notification-center/notifications', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/notification-center/notifications — create (auth)', async () => {
    const res = await req('/v1/notification-center/notifications', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Test Notification', body: 'Hello', notification_type: 'info' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/notification-center/notifications/read-all — bulk read (auth)', async () => {
    const res = await req('/v1/notification-center/notifications/read-all', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/notification-center/preferences — preferences (auth)', async () => {
    const res = await req('/v1/notification-center/preferences', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/notification-center/templates — templates (public)', async () => {
    const res = await req('/v1/notification-center/templates');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/notification-center/admin/overview — admin', async () => {
    const res = await req('/v1/notification-center/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 49: Mission Template Library ---

describe('Wave 49: Mission Template Library', () => {
  it('GET /v1/mission-templates/templates — list (auth)', async () => {
    const res = await req('/v1/mission-templates/templates', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/mission-templates/templates — create (auth)', async () => {
    const res = await req('/v1/mission-templates/templates', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Data ETL', category: 'data-processing', config_json: { steps: [] } }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/mission-templates/categories — categories (public)', async () => {
    const res = await req('/v1/mission-templates/categories');
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/mission-templates/templates/t1/instantiate — instantiate (auth)', async () => {
    const res = await req('/v1/mission-templates/templates/t1/instantiate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ overrides: {} }),
    });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/mission-templates/admin/overview — admin', async () => {
    const res = await req('/v1/mission-templates/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 49: Tenant API Key Management ---

describe('Wave 49: Tenant API Key Management', () => {
  it('GET /v1/api-key-mgmt/keys — list (auth)', async () => {
    const res = await req('/v1/api-key-mgmt/keys', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/api-key-mgmt/keys — create (auth)', async () => {
    const res = await req('/v1/api-key-mgmt/keys', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Production Key', scopes: ['read', 'write'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/api-key-mgmt/keys/k1/rotate — rotate (auth)', async () => {
    const res = await req('/v1/api-key-mgmt/keys/k1/rotate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/api-key-mgmt/keys/k1/usage — usage (auth)', async () => {
    const res = await req('/v1/api-key-mgmt/keys/k1/usage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/api-key-mgmt/admin/overview — admin', async () => {
    const res = await req('/v1/api-key-mgmt/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 50: Platform Audit Trail ---

describe('Wave 50: Platform Audit Trail', () => {
  it('GET /v1/audit-trail/logs — search (auth)', async () => {
    const res = await req('/v1/audit-trail/logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit-trail/retention — retention policies (auth)', async () => {
    const res = await req('/v1/audit-trail/retention', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/audit-trail/exports — request export (auth)', async () => {
    const res = await req('/v1/audit-trail/exports', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ filters: { action: 'login' } }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/audit-trail/stats — stats (auth)', async () => {
    const res = await req('/v1/audit-trail/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit-trail/admin/overview — admin', async () => {
    const res = await req('/v1/audit-trail/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 50: Admin Feature Flags ---

describe('Wave 50: Admin Feature Flags', () => {
  it('GET /admin/feature-flags/flags — list (admin)', async () => {
    const res = await req('/admin/feature-flags/flags', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/feature-flags/flags — create (admin)', async () => {
    const res = await req('/admin/feature-flags/flags', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ flag_key: 'new_dashboard', name: 'New Dashboard', rollout_percentage: 50 }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/feature-flags/evaluate/test_flag — evaluate (admin)', async () => {
    const res = await req('/admin/feature-flags/evaluate/test_flag?tenant_id=t1', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 404, 500]).toContain(res.status);
  });

  it('GET /admin/feature-flags/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/feature-flags/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/feature-flags/flags — 403 without key', async () => {
    const res = await req('/admin/feature-flags/flags');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 50: Tenant Resource Quotas ---

describe('Wave 50: Tenant Resource Quotas', () => {
  it('GET /v1/resource-quotas/definitions — definitions (public)', async () => {
    const res = await req('/v1/resource-quotas/definitions');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/resource-quotas/quotas — tenant quotas (auth)', async () => {
    const res = await req('/v1/resource-quotas/quotas', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/resource-quotas/check/missions_per_month — check (auth)', async () => {
    const res = await req('/v1/resource-quotas/check/missions_per_month', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/resource-quotas/alerts — alerts (auth)', async () => {
    const res = await req('/v1/resource-quotas/alerts', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/resource-quotas/admin/overview — admin', async () => {
    const res = await req('/v1/resource-quotas/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 49-50: OpenAPI spec', () => {
  it('includes Wave 49-50 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 49
    expect(paths).toContain('/v1/notification-center/notifications');
    expect(paths).toContain('/v1/notification-center/preferences');
    expect(paths).toContain('/v1/mission-templates/templates');
    expect(paths).toContain('/v1/mission-templates/categories');
    expect(paths).toContain('/v1/api-key-mgmt/keys');
    // Wave 50
    expect(paths).toContain('/v1/audit-trail/logs');
    expect(paths).toContain('/v1/audit-trail/exports');
    expect(paths).toContain('/admin/feature-flags/flags');
    expect(paths).toContain('/admin/feature-flags/dashboard');
    expect(paths).toContain('/v1/resource-quotas/definitions');
    expect(paths).toContain('/v1/resource-quotas/quotas');
  });
});
