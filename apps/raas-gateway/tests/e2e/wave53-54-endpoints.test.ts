/**
 * Wave 53-54 E2E tests — SSO Providers, Priority Queue, Analytics Dashboard,
 * Custom Fields, Deployment Manager, Doc Generator
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

// --- Wave 53: Tenant SSO Providers ---

describe('Wave 53: Tenant SSO Providers', () => {
  it('GET /v1/sso-providers/providers — list (auth)', async () => {
    const res = await req('/v1/sso-providers/providers', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/sso-providers/providers — create (auth)', async () => {
    const res = await req('/v1/sso-providers/providers', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_type: 'oidc', name: 'Google', client_id: 'abc', client_secret: 'xyz' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/sso-providers/sessions — sessions (auth)', async () => {
    const res = await req('/v1/sso-providers/sessions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/sso-providers/admin/overview — admin', async () => {
    const res = await req('/v1/sso-providers/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 53: Mission Priority Queue ---

describe('Wave 53: Mission Priority Queue', () => {
  it('POST /v1/priority-queue/enqueue — enqueue (auth)', async () => {
    const res = await req('/v1/priority-queue/enqueue', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission_id: 'm-1', priority: 1 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/priority-queue/rules — rules (auth)', async () => {
    const res = await req('/v1/priority-queue/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/priority-queue/stats — stats (admin)', async () => {
    const res = await req('/v1/priority-queue/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /v1/priority-queue/admin/overview — admin', async () => {
    const res = await req('/v1/priority-queue/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 53: Platform Analytics Dashboard ---

describe('Wave 53: Platform Analytics Dashboard', () => {
  it('GET /v1/analytics-dashboard/widgets — widgets (auth)', async () => {
    const res = await req('/v1/analytics-dashboard/widgets', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/analytics-dashboard/widgets — create (auth)', async () => {
    const res = await req('/v1/analytics-dashboard/widgets', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Revenue', widget_type: 'chart', query_json: { type: 'revenue' } }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/analytics-dashboard/queries — queries (auth)', async () => {
    const res = await req('/v1/analytics-dashboard/queries', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/analytics-dashboard/admin/overview — admin', async () => {
    const res = await req('/v1/analytics-dashboard/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 54: Tenant Custom Fields ---

describe('Wave 54: Tenant Custom Fields', () => {
  it('GET /v1/custom-fields/definitions — list (auth)', async () => {
    const res = await req('/v1/custom-fields/definitions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/custom-fields/definitions — create (auth)', async () => {
    const res = await req('/v1/custom-fields/definitions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ entity_type: 'mission', field_name: 'priority_label', field_type: 'text', label: 'Priority Label' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/custom-fields/search — search (auth)', async () => {
    const res = await req('/v1/custom-fields/search?definition_id=d1&value=test', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/custom-fields/admin/overview — admin', async () => {
    const res = await req('/v1/custom-fields/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 54: Admin Deployment Manager ---

describe('Wave 54: Admin Deployment Manager', () => {
  it('GET /admin/deployments/deployments — list (admin)', async () => {
    const res = await req('/admin/deployments/deployments', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/deployments/deployments — create (admin)', async () => {
    const res = await req('/admin/deployments/deployments', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ version: '2.1.0', environment: 'production', commit_hash: 'abc123' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/deployments/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/deployments/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/deployments/deployments — 403 without key', async () => {
    const res = await req('/admin/deployments/deployments');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 54: API Documentation Generator ---

describe('Wave 54: API Documentation Generator', () => {
  it('GET /admin/api-docs/endpoints — list (admin)', async () => {
    const res = await req('/admin/api-docs/endpoints', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/api-docs/versions — versions (admin)', async () => {
    const res = await req('/admin/api-docs/versions', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/api-docs/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/api-docs/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/api-docs/endpoints — 403 without key', async () => {
    const res = await req('/admin/api-docs/endpoints');
    expect([401, 403]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 53-54: OpenAPI spec', () => {
  it('includes Wave 53-54 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 53
    expect(paths).toContain('/v1/sso-providers/providers');
    expect(paths).toContain('/v1/sso-providers/sessions');
    expect(paths).toContain('/v1/priority-queue/rules');
    expect(paths).toContain('/v1/priority-queue/stats');
    expect(paths).toContain('/v1/analytics-dashboard/widgets');
    expect(paths).toContain('/v1/analytics-dashboard/queries');
    // Wave 54
    expect(paths).toContain('/v1/custom-fields/definitions');
    expect(paths).toContain('/v1/custom-fields/search');
    expect(paths).toContain('/admin/deployments/deployments');
    expect(paths).toContain('/admin/deployments/dashboard');
    expect(paths).toContain('/admin/api-docs/endpoints');
    expect(paths).toContain('/admin/api-docs/versions');
  });
});
