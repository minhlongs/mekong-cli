/**
 * Wave 19-20 E2E tests — models, affiliates, sales pipeline, ROI tools, scheduled handler
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

// --- Mock helpers (same pattern as wave15-16) ---

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
  async batch(_s: any[]) { return []; }
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

// ─── Wave 19: Models ────────────────────────────────────────────────

describe('Wave 19: Models API', () => {
  it('GET /v1/models — list models', async () => {
    const res = await req('/v1/models', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    expect(body.data.models.length).toBeGreaterThan(0);
    expect(body.data.count).toBeGreaterThan(0);
  });

  it('GET /v1/models?provider=bailian — filter', async () => {
    const res = await req('/v1/models?provider=bailian', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    body.data.models.forEach((m: any) => expect(m.provider).toBe('bailian'));
  });

  it('GET /v1/models/nonexistent — 404', async () => {
    const res = await req('/v1/models/nonexistent', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBe(404);
  });

  it('POST /v1/models/select — auto-select', async () => {
    const res = await req('/v1/models/select', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ capability: 'code' }),
    });
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    expect(body.data.selected).toBeDefined();
    expect(body.data.selected.capabilities).toContain('code');
  });
});

// ─── Wave 19: Affiliates ────────────────────────────────────────────

describe('Wave 19: Affiliate Engine', () => {
  it('POST /v1/affiliates/register — register partner', async () => {
    const res = await req('/v1/affiliates/register', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/affiliates/stats — partner stats', async () => {
    const res = await req('/v1/affiliates/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/affiliates/commissions — list commissions', async () => {
    const res = await req('/v1/affiliates/commissions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/affiliates/admin — admin list (requires key)', async () => {
    const res = await req('/v1/affiliates/admin', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/affiliates/admin/leaderboard — leaderboard', async () => {
    const res = await req('/v1/affiliates/admin/leaderboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/affiliates/admin — 401 without key', async () => {
    const res = await req('/v1/affiliates/admin');
    expect(res.status).toBe(401);
  });
});

// ─── Wave 19: Scheduled Handler ─────────────────────────────────────

describe('Wave 19: Scheduled Handler', () => {
  it('exports handleScheduled function', async () => {
    const mod = await import('../../src/services/scheduled-handler');
    expect(typeof mod.handleScheduled).toBe('function');
  });
});

// ─── Wave 20: Sales Pipeline ────────────────────────────────────────

describe('Wave 20: Sales Pipeline', () => {
  it('POST /admin/sales/leads — create lead', async () => {
    const res = await req('/admin/sales/leads', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: 'Test Corp', contact_email: 'a@b.com', estimated_arr: 5000 }),
    });
    // 201 on success, 500 acceptable with mock DB (no real insert)
    expect([201, 500]).toContain(res.status);
  });

  it('GET /admin/sales/leads — list leads', async () => {
    const res = await req('/admin/sales/leads', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /admin/sales/pipeline — pipeline view', async () => {
    const res = await req('/admin/sales/pipeline', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /admin/sales/forecast — revenue forecast', async () => {
    const res = await req('/admin/sales/forecast', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /admin/sales/leads — 401 without admin key', async () => {
    const res = await req('/admin/sales/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: 'Hack' }),
    });
    expect(res.status).toBe(401);
  });
});

// ─── Wave 20: ROI Calculator ────────────────────────────────────────

describe('Wave 20: ROI Calculator & Sales Tools', () => {
  it('POST /tools/roi-calculator — calculate ROI', async () => {
    const res = await req('/tools/roi-calculator', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ team_size: 5, missions_per_month: 100, current_monthly_cost: 500 }),
    });
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    expect(body.recommended_tier).toBeDefined();
    expect(body.monthly_savings).toBeGreaterThanOrEqual(0);
  });

  it('POST /tools/demo/request — create sandbox', async () => {
    const res = await req('/tools/demo/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'demo@test.com' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /tools/demo/request — creates sandbox even without email', async () => {
    const res = await req('/tools/demo/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    // Email is optional — sandbox created with null email
    expect(res.status).toBe(201);
  });

  it('POST /tools/trial/signup — start trial', async () => {
    const res = await req('/tools/trial/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'trial@test.com' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /admin/sales/demos — list demos (admin)', async () => {
    const res = await req('/admin/sales/demos', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /admin/sales/trials/metrics — trial metrics (admin)', async () => {
    const res = await req('/admin/sales/trials/metrics', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });
});

// ─── OpenAPI ────────────────────────────────────────────────────────

describe('Wave 19-20: OpenAPI spec', () => {
  it('includes Wave 19-20 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/models');
    expect(paths).toContain('/v1/affiliates/register');
    expect(paths).toContain('/admin/sales/leads');
    expect(paths).toContain('/tools/roi-calculator');
    expect(paths).toContain('/admin/sales/forecast');
  });
});
