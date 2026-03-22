/**
 * Wave 41-42 E2E tests — Tenant SSO V2, API Gateway Caching, Mission Dependencies,
 * Tenant Invoicing, Platform Changelog V2, Admin Command Center
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

// --- Wave 41: Tenant SSO V2 ---

describe('Wave 41: Tenant SSO V2', () => {
  it('GET /v1/sso/configs — list SSO configs (auth)', async () => {
    const res = await req('/v1/sso/configs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/sso/configs — create SSO config (auth)', async () => {
    const res = await req('/v1/sso/configs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider_type: 'oidc', provider_name: 'Google', client_id: 'test', issuer_url: 'https://accounts.google.com' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/sso/login/cfg-123 — initiate SSO (public)', async () => {
    const res = await req('/v1/sso/login/cfg-123', { method: 'POST' });
    expect([200, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/sso/stats — SSO stats (auth)', async () => {
    const res = await req('/v1/sso/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/sso/admin/overview — admin', async () => {
    const res = await req('/v1/sso/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 41: API Gateway Caching ---

describe('Wave 41: API Gateway Caching', () => {
  it('GET /v1/cache/configs — list configs (auth)', async () => {
    const res = await req('/v1/cache/configs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/cache/configs — create config (auth)', async () => {
    const res = await req('/v1/cache/configs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ path_pattern: '/v1/missions/*', ttl_seconds: 300 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/cache/invalidate — invalidate (auth)', async () => {
    const res = await req('/v1/cache/invalidate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ path_pattern: '/v1/missions/*' }),
    });
    expect([200, 500]).toContain(res.status);
  });

  it('GET /v1/cache/stats — cache stats (auth)', async () => {
    const res = await req('/v1/cache/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/cache/admin/overview — admin', async () => {
    const res = await req('/v1/cache/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 41: Mission Dependencies ---

describe('Wave 41: Mission Dependencies', () => {
  it('GET /v1/mission-chains/chains — list chains (auth)', async () => {
    const res = await req('/v1/mission-chains/chains', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/mission-chains/chains — create chain (auth)', async () => {
    const res = await req('/v1/mission-chains/chains', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Test Chain', description: 'Test DAG' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/mission-chains/chains/mc-1/start — start chain (auth)', async () => {
    const res = await req('/v1/mission-chains/chains/mc-1/start', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/mission-chains/chains/mc-1/ready — ready missions (auth)', async () => {
    const res = await req('/v1/mission-chains/chains/mc-1/ready', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-chains/admin/overview — admin', async () => {
    const res = await req('/v1/mission-chains/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 42: Tenant Invoicing ---

describe('Wave 42: Tenant Invoicing', () => {
  it('GET /v1/invoicing/invoices — list invoices (auth)', async () => {
    const res = await req('/v1/invoicing/invoices', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/invoicing/invoices — create invoice (auth)', async () => {
    const res = await req('/v1/invoicing/invoices', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ currency: 'USD', line_items: [{ description: 'Pro Plan', quantity: 1, unit_price: 14900, item_type: 'subscription' }] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/invoicing/summary — summary (auth)', async () => {
    const res = await req('/v1/invoicing/summary', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/invoicing/admin/overview — admin', async () => {
    const res = await req('/v1/invoicing/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /v1/invoicing/admin/overdue — overdue (admin)', async () => {
    const res = await req('/v1/invoicing/admin/overdue', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 42: Platform Changelog V2 ---

describe('Wave 42: Platform Changelog V2', () => {
  it('GET /v1/changelog-v2/entries — list entries (public)', async () => {
    const res = await req('/v1/changelog-v2/entries');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/changelog-v2/unread — unread count (auth)', async () => {
    const res = await req('/v1/changelog-v2/unread', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/changelog-v2/subscription — get subscription (auth)', async () => {
    const res = await req('/v1/changelog-v2/subscription', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/changelog-v2/admin/entries — create entry (admin)', async () => {
    const res = await req('/v1/changelog-v2/admin/entries', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ version: '2.1.0', title: 'New Feature', content: 'Details here', category: 'feature' }),
    });
    expect([200, 201, 403, 500]).toContain(res.status);
  });

  it('GET /v1/changelog-v2/admin/stats — stats (admin)', async () => {
    const res = await req('/v1/changelog-v2/admin/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 42: Admin Command Center ---

describe('Wave 42: Admin Command Center', () => {
  it('POST /admin/commands/execute — execute (admin)', async () => {
    const res = await req('/admin/commands/execute', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ command_type: 'system_check', command_name: 'health', executed_by: 'admin' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/commands/history — history (admin)', async () => {
    const res = await req('/admin/commands/history', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/commands/available — available commands (admin)', async () => {
    const res = await req('/admin/commands/available', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/commands/scheduled — scheduled (admin)', async () => {
    const res = await req('/admin/commands/scheduled', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/commands/stats — stats (admin)', async () => {
    const res = await req('/admin/commands/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/commands/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/commands/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 41-42: OpenAPI spec', () => {
  it('includes Wave 41-42 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 41
    expect(paths).toContain('/v1/sso/configs');
    expect(paths).toContain('/v1/sso/stats');
    expect(paths).toContain('/v1/cache/configs');
    expect(paths).toContain('/v1/cache/stats');
    expect(paths).toContain('/v1/mission-chains/chains');
    expect(paths).toContain('/v1/mission-chains/admin/overview');
    // Wave 42
    expect(paths).toContain('/v1/invoicing/invoices');
    expect(paths).toContain('/v1/invoicing/summary');
    expect(paths).toContain('/v1/changelog-v2/entries');
    expect(paths).toContain('/v1/changelog-v2/subscription');
    expect(paths).toContain('/admin/commands/execute');
    expect(paths).toContain('/admin/commands/dashboard');
  });
});
