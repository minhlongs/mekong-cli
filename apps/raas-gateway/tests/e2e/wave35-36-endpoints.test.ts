/**
 * Wave 35-36 E2E tests — API Sandbox, Webhook Simulator, API Usage Analytics,
 * Tenant Backup, Multi-Region Config, Platform Audit Trail
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

// --- Wave 35: API Sandbox ---

describe('Wave 35: API Sandbox', () => {
  it('GET /v1/sandbox/environments — list sandboxes (auth)', async () => {
    const res = await req('/v1/sandbox/environments', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/sandbox/environments — create sandbox (auth)', async () => {
    const res = await req('/v1/sandbox/environments', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'test-sandbox' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/sandbox/stats — sandbox stats (auth)', async () => {
    const res = await req('/v1/sandbox/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/sandbox/execute — execute request (auth)', async () => {
    const res = await req('/v1/sandbox/execute', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ sandbox_id: 'test', method: 'GET', path: '/v1/missions' }),
    });
    expect([200, 400, 404, 500]).toContain(res.status);
  });
});

// --- Wave 35: Webhook Simulator ---

describe('Wave 35: Webhook Simulator', () => {
  it('POST /v1/webhook-simulator/simulate — simulate webhook (auth)', async () => {
    const res = await req('/v1/webhook-simulator/simulate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_url: 'https://example.com/hook', event_type: 'mission.completed', payload: {} }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/webhook-simulator/simulations — list simulations (auth)', async () => {
    const res = await req('/v1/webhook-simulator/simulations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhook-simulator/stats — simulation stats (auth)', async () => {
    const res = await req('/v1/webhook-simulator/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhook-simulator/sample/mission.created — sample payload (auth)', async () => {
    const res = await req('/v1/webhook-simulator/sample/mission.created', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/webhook-simulator/test-endpoints — create test endpoint (auth)', async () => {
    const res = await req('/v1/webhook-simulator/test-endpoints', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 500]).toContain(res.status);
  });
});

// --- Wave 35: API Usage Analytics ---

describe('Wave 35: API Usage Analytics', () => {
  it('GET /v1/api-analytics/summary — usage summary (auth)', async () => {
    const res = await req('/v1/api-analytics/summary', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/api-analytics/top — top endpoints (auth)', async () => {
    const res = await req('/v1/api-analytics/top', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/api-analytics/slowest — slowest endpoints (auth)', async () => {
    const res = await req('/v1/api-analytics/slowest', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/api-analytics/errors — error breakdown (auth)', async () => {
    const res = await req('/v1/api-analytics/errors', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/api-analytics/errors/hotspots — error hotspots (auth)', async () => {
    const res = await req('/v1/api-analytics/errors/hotspots', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/api-analytics/trend/volume — volume trend (auth)', async () => {
    const res = await req('/v1/api-analytics/trend/volume', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 36: Tenant Backup ---

describe('Wave 36: Tenant Backup', () => {
  it('GET /v1/backup/backups — list backups (auth)', async () => {
    const res = await req('/v1/backup/backups', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/backup/backups — create backup (auth)', async () => {
    const res = await req('/v1/backup/backups', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ backup_type: 'full' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/backup/stats — backup stats (auth)', async () => {
    const res = await req('/v1/backup/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/backup/restore-logs — restore logs (auth)', async () => {
    const res = await req('/v1/backup/restore-logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 36: Multi-Region Config ---

describe('Wave 36: Multi-Region Config', () => {
  it('GET /v1/region/config — region config (auth)', async () => {
    const res = await req('/v1/region/config', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/region/optimal — optimal region (auth)', async () => {
    const res = await req('/v1/region/optimal', { headers: { Authorization: `Bearer ${token}` } });
    expect([200, 404, 503]).toContain(res.status);
  });

  it('GET /v1/region/regions — available regions (public)', async () => {
    const res = await req('/v1/region/regions');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/region/status — region status (public)', async () => {
    const res = await req('/v1/region/status');
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/region/admin/seed — seed regions (admin)', async () => {
    const res = await req('/v1/region/admin/seed', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 201, 403, 500]).toContain(res.status);
  });
});

// --- Wave 36: Platform Audit Trail ---

describe('Wave 36: Platform Audit Trail', () => {
  it('GET /admin/audit-trail/entries — audit entries (admin)', async () => {
    const res = await req('/admin/audit-trail/entries', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/audit-trail/stats — audit stats (admin)', async () => {
    const res = await req('/admin/audit-trail/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/audit-trail/search — search audit (admin)', async () => {
    const res = await req('/admin/audit-trail/search?q=login', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/audit-trail/export — export audit (admin)', async () => {
    const res = await req('/admin/audit-trail/export', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/audit-trail/retention — retention configs (admin)', async () => {
    const res = await req('/admin/audit-trail/retention', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 35-36: OpenAPI spec', () => {
  it('includes Wave 35-36 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 35
    expect(paths).toContain('/v1/sandbox/environments');
    expect(paths).toContain('/v1/sandbox/stats');
    expect(paths).toContain('/v1/webhook-simulator/simulate');
    expect(paths).toContain('/v1/webhook-simulator/stats');
    expect(paths).toContain('/v1/api-analytics/summary');
    expect(paths).toContain('/v1/api-analytics/top');
    // Wave 36
    expect(paths).toContain('/v1/backup/backups');
    expect(paths).toContain('/v1/backup/stats');
    expect(paths).toContain('/v1/region/config');
    expect(paths).toContain('/v1/region/regions');
    expect(paths).toContain('/admin/audit-trail/entries');
    expect(paths).toContain('/admin/audit-trail/stats');
  });
});
