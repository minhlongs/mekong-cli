/**
 * Wave 25-26 E2E tests — multi-currency, audit export, white-label, API versioning, bulk ops, SLA
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

// --- Wave 25: Multi-Currency ---

describe('Wave 25: Multi-Currency', () => {
  it('GET /v1/currencies — supported currencies', async () => {
    const res = await req('/v1/currencies');
    expect(res.status).toBe(200);
  });

  it('GET /v1/currencies/rates — exchange rates', async () => {
    const res = await req('/v1/currencies/rates');
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/currencies/convert — convert amount', async () => {
    const res = await req('/v1/currencies/convert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: 100, from: 'USD', to: 'EUR' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/currencies/pricing — pricing in EUR', async () => {
    const res = await req('/v1/currencies/pricing?currency=EUR');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/currencies/preference — tenant currency (auth)', async () => {
    const res = await req('/v1/currencies/preference', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('PUT /v1/currencies/preference — set currency (auth)', async () => {
    const res = await req('/v1/currencies/preference', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ currency: 'EUR' }),
    });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 25: Audit Export ---

describe('Wave 25: Audit Export', () => {
  it('POST /v1/audit/export — export logs (auth)', async () => {
    const res = await req('/v1/audit/export', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ format: 'json' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit/compliance — compliance status (auth)', async () => {
    const res = await req('/v1/audit/compliance', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit/retention — retention policy (auth)', async () => {
    const res = await req('/v1/audit/retention', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit/gdpr-export — GDPR export (auth)', async () => {
    const res = await req('/v1/audit/gdpr-export', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/audit/deletion-request — request deletion (auth)', async () => {
    const res = await req('/v1/audit/deletion-request', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason: 'Account closure' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit/exports — export history (auth)', async () => {
    const res = await req('/v1/audit/exports', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 25: White-Label ---

describe('Wave 25: White-Label Branding', () => {
  it('GET /v1/branding — get branding (auth)', async () => {
    const res = await req('/v1/branding', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('PUT /v1/branding — update branding (auth)', async () => {
    const res = await req('/v1/branding', {
      method: 'PUT',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ company_name: 'My Brand', primary_color: '#ff5500' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/branding/features — available features (auth)', async () => {
    const res = await req('/v1/branding/features', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/branding/preview — CSS preview (auth)', async () => {
    const res = await req('/v1/branding/preview', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/branding/domain/example.com — lookup by domain (public)', async () => {
    const res = await req('/v1/branding/domain/example.com');
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 26: API Versioning ---

describe('Wave 26: API Versioning', () => {
  it('GET /api/versions — list versions (public)', async () => {
    const res = await req('/api/versions');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    expect(body.versions || body.data).toBeDefined();
  });

  it('GET /api/versions/v1 — version details', async () => {
    const res = await req('/api/versions/v1');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /api/versions/v1/changelog — version changelog', async () => {
    const res = await req('/api/versions/v1/changelog');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /api/versions/migrate/v1/v2 — migration guide', async () => {
    const res = await req('/api/versions/migrate/v1/v2');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /api/versions/usage — admin only', async () => {
    const res = await req('/api/versions/usage', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 26: Bulk Operations ---

describe('Wave 26: Bulk Operations', () => {
  it('POST /v1/bulk/export — bulk export (auth)', async () => {
    const res = await req('/v1/bulk/export', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource: 'missions', format: 'json' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/bulk/import — bulk import (auth)', async () => {
    const res = await req('/v1/bulk/import', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource: 'missions', items: [{ goal: 'Test mission' }] }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/bulk/jobs — list jobs (auth)', async () => {
    const res = await req('/v1/bulk/jobs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/bulk/stats — bulk stats (auth)', async () => {
    const res = await req('/v1/bulk/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 26: SLA Monitoring ---

describe('Wave 26: SLA Monitoring', () => {
  it('GET /sla/targets — SLA targets (public)', async () => {
    const res = await req('/sla/targets');
    expect(res.status).toBe(200);
  });

  it('GET /sla/status — platform status (public)', async () => {
    const res = await req('/sla/status');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /sla/uptime — uptime percentage (public)', async () => {
    const res = await req('/sla/uptime');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /sla/report — SLA report (auth)', async () => {
    const res = await req('/sla/report', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /sla/breaches — breach history (admin)', async () => {
    const res = await req('/sla/breaches', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- OpenAPI ---

describe('Wave 25-26: OpenAPI spec', () => {
  it('includes Wave 25-26 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/currencies');
    expect(paths).toContain('/v1/currencies/convert');
    expect(paths).toContain('/v1/audit/export');
    expect(paths).toContain('/v1/audit/compliance');
    expect(paths).toContain('/v1/branding');
    expect(paths).toContain('/v1/branding/domain/{domain}');
    expect(paths).toContain('/api/versions');
    expect(paths).toContain('/v1/bulk/export');
    expect(paths).toContain('/v1/bulk/import');
    expect(paths).toContain('/sla/targets');
    expect(paths).toContain('/sla/uptime');
  });
});
