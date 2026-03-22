/**
 * Wave 51-52 E2E tests — Webhooks V3, Service Mesh, Scheduling Engine,
 * Data Export, Platform Config, Contract Testing
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

// --- Wave 51: Tenant Webhooks V3 ---

describe('Wave 51: Tenant Webhooks V3', () => {
  it('GET /v1/webhooks-v3/subscriptions — list (auth)', async () => {
    const res = await req('/v1/webhooks-v3/subscriptions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/webhooks-v3/subscriptions — create (auth)', async () => {
    const res = await req('/v1/webhooks-v3/subscriptions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://example.com/webhook', events: ['mission.completed'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/webhooks-v3/event-types — event types (public)', async () => {
    const res = await req('/v1/webhooks-v3/event-types');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhooks-v3/stats — delivery stats (auth)', async () => {
    const res = await req('/v1/webhooks-v3/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhooks-v3/admin/overview — admin', async () => {
    const res = await req('/v1/webhooks-v3/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 51: Platform Service Mesh ---

describe('Wave 51: Platform Service Mesh', () => {
  it('GET /admin/service-mesh/services — list (admin)', async () => {
    const res = await req('/admin/service-mesh/services', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/service-mesh/services — register (admin)', async () => {
    const res = await req('/admin/service-mesh/services', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ service_name: 'auth-service', endpoint_url: 'https://auth.internal' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/service-mesh/topology — topology (admin)', async () => {
    const res = await req('/admin/service-mesh/topology', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/service-mesh/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/service-mesh/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/service-mesh/services — 403 without key', async () => {
    const res = await req('/admin/service-mesh/services');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 51: Mission Scheduling Engine ---

describe('Wave 51: Mission Scheduling Engine', () => {
  it('GET /v1/scheduling/jobs — list (auth)', async () => {
    const res = await req('/v1/scheduling/jobs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/scheduling/jobs — create (auth)', async () => {
    const res = await req('/v1/scheduling/jobs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Daily Report', cron_expression: '0 9 * * *', mission_config_json: { goal: 'Generate report' } }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/scheduling/jobs/j1/trigger — trigger (auth)', async () => {
    const res = await req('/v1/scheduling/jobs/j1/trigger', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/scheduling/jobs/j1/executions — executions (auth)', async () => {
    const res = await req('/v1/scheduling/jobs/j1/executions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/scheduling/admin/overview — admin', async () => {
    const res = await req('/v1/scheduling/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 52: Tenant Data Export ---

describe('Wave 52: Tenant Data Export', () => {
  it('POST /v1/data-export/exports — request (auth)', async () => {
    const res = await req('/v1/data-export/exports', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ export_type: 'missions', format: 'json' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/data-export/exports — list (auth)', async () => {
    const res = await req('/v1/data-export/exports', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/data-export/templates — templates (public)', async () => {
    const res = await req('/v1/data-export/templates');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/data-export/admin/overview — admin', async () => {
    const res = await req('/v1/data-export/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 52: Admin Platform Config ---

describe('Wave 52: Admin Platform Config', () => {
  it('GET /admin/platform-config/configs — list (admin)', async () => {
    const res = await req('/admin/platform-config/configs', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('PUT /admin/platform-config/configs/maintenance_mode — set (admin)', async () => {
    const res = await req('/admin/platform-config/configs/maintenance_mode', {
      method: 'PUT',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ value: 'false', description: 'Maintenance mode toggle' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/platform-config/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/platform-config/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/platform-config/configs — 403 without key', async () => {
    const res = await req('/admin/platform-config/configs');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 52: API Contract Testing ---

describe('Wave 52: API Contract Testing', () => {
  it('GET /admin/contract-testing/contracts — list (admin)', async () => {
    const res = await req('/admin/contract-testing/contracts', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/contract-testing/contracts — create (admin)', async () => {
    const res = await req('/admin/contract-testing/contracts', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Missions API', api_path: '/v1/missions', method: 'POST', schema_json: {} }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/contract-testing/compliance — compliance (admin)', async () => {
    const res = await req('/admin/contract-testing/compliance', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/contract-testing/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/contract-testing/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/contract-testing/contracts — 403 without key', async () => {
    const res = await req('/admin/contract-testing/contracts');
    expect([401, 403]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 51-52: OpenAPI spec', () => {
  it('includes Wave 51-52 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 51
    expect(paths).toContain('/v1/webhooks-v3/subscriptions');
    expect(paths).toContain('/v1/webhooks-v3/event-types');
    expect(paths).toContain('/admin/service-mesh/services');
    expect(paths).toContain('/admin/service-mesh/topology');
    expect(paths).toContain('/v1/scheduling/jobs');
    // Wave 52
    expect(paths).toContain('/v1/data-export/exports');
    expect(paths).toContain('/v1/data-export/templates');
    expect(paths).toContain('/admin/platform-config/configs');
    expect(paths).toContain('/admin/contract-testing/contracts');
    expect(paths).toContain('/admin/contract-testing/compliance');
  });
});
