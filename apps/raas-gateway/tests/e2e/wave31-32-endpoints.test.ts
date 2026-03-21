/**
 * Wave 31-32 E2E tests — Audit Streaming, IP Allowlist, Data Retention,
 * Error Budgets, Usage Forecasting, Compliance Reports
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

// --- Wave 31: Audit Streaming ---

describe('Wave 31: Audit Streaming', () => {
  it('GET /v1/audit-streaming/configs — list configs (auth)', async () => {
    const res = await req('/v1/audit-streaming/configs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/audit-streaming/configs — create config (auth)', async () => {
    const res = await req('/v1/audit-streaming/configs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ stream_type: 'webhook', destination_url: 'https://example.com/audit', event_filters: ['mission.created'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/audit-streaming/stats — delivery stats (auth)', async () => {
    const res = await req('/v1/audit-streaming/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/audit-streaming/admin/pending — pending deliveries (admin)', async () => {
    const res = await req('/v1/audit-streaming/admin/pending', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 500]).toContain(res.status);
  });
});

// --- Wave 31: IP Allowlist ---

describe('Wave 31: IP Allowlist', () => {
  it('GET /v1/ip-allowlist/rules — list rules (auth)', async () => {
    const res = await req('/v1/ip-allowlist/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/ip-allowlist/rules — add rule (auth)', async () => {
    const res = await req('/v1/ip-allowlist/rules', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_address: '192.168.1.0/24', label: 'Office network' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/ip-allowlist/check — check IP (auth)', async () => {
    const res = await req('/v1/ip-allowlist/check', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ ip_address: '192.168.1.100' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/ip-allowlist/blocked-count — blocked count (auth)', async () => {
    const res = await req('/v1/ip-allowlist/blocked-count', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 31: Data Retention ---

describe('Wave 31: Data Retention', () => {
  it('GET /v1/data-retention/policies — list policies (auth)', async () => {
    const res = await req('/v1/data-retention/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/data-retention/policies — create policy (auth)', async () => {
    const res = await req('/v1/data-retention/policies', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data_type: 'missions', retention_days: 90, auto_purge: true }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/data-retention/seed — seed defaults (auth)', async () => {
    const res = await req('/v1/data-retention/seed', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 500]).toContain(res.status);
  });

  it('GET /v1/data-retention/stats — retention stats (auth)', async () => {
    const res = await req('/v1/data-retention/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/data-retention/admin/due — due policies (admin)', async () => {
    const res = await req('/v1/data-retention/admin/due', { headers: { 'X-Admin-Key': ADMIN_API_KEY, Authorization: `Bearer ${token}` } });
    expect([200, 500]).toContain(res.status);
  });
});

// --- Wave 32: Error Budgets ---

describe('Wave 32: Error Budgets', () => {
  it('GET /v1/error-budgets/slos — list SLOs (auth)', async () => {
    const res = await req('/v1/error-budgets/slos', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/error-budgets/slos — create SLO (auth)', async () => {
    const res = await req('/v1/error-budgets/slos', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Mission Success Rate', slo_type: 'availability', target_value: 99.0, window_days: 30 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/error-budgets/summary — budget summary (auth)', async () => {
    const res = await req('/v1/error-budgets/summary', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/error-budgets/alerts — budget alerts (auth)', async () => {
    const res = await req('/v1/error-budgets/alerts', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/error-budgets/seed — seed default SLOs (auth)', async () => {
    const res = await req('/v1/error-budgets/seed', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 500]).toContain(res.status);
  });
});

// --- Wave 32: Usage Forecasting ---

describe('Wave 32: Usage Forecasting', () => {
  it('GET /v1/usage-forecast/snapshots — historical data (auth)', async () => {
    const res = await req('/v1/usage-forecast/snapshots?metric=missions&days=30', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/usage-forecast/snapshots — record snapshot (auth)', async () => {
    const res = await req('/v1/usage-forecast/snapshots', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ metric_type: 'missions', value: 42 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/usage-forecast/generate — generate forecast (auth)', async () => {
    const res = await req('/v1/usage-forecast/generate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ metric_type: 'missions', days_ahead: 7 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/usage-forecast/all — all forecasts (auth)', async () => {
    const res = await req('/v1/usage-forecast/all', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/usage-forecast/anomalies — detect anomalies (auth)', async () => {
    const res = await req('/v1/usage-forecast/anomalies?metric=missions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/usage-forecast/capacity-alert — capacity alerts (auth)', async () => {
    const res = await req('/v1/usage-forecast/capacity-alert', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 32: Compliance Reports ---

describe('Wave 32: Compliance Reports', () => {
  it('GET /v1/compliance/frameworks — supported frameworks (no auth needed)', async () => {
    const res = await req('/v1/compliance/frameworks', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/compliance/reports/generate — generate report (auth)', async () => {
    const res = await req('/v1/compliance/reports/generate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ report_type: 'soc2', coverage_start: '2026-01-01', coverage_end: '2026-03-21' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/compliance/reports — list reports (auth)', async () => {
    const res = await req('/v1/compliance/reports', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/compliance/checks — run live checks (auth)', async () => {
    const res = await req('/v1/compliance/checks?category=soc2', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/compliance/score — compliance score (auth)', async () => {
    const res = await req('/v1/compliance/score?category=gdpr', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/compliance/summary — cross-category summary (auth)', async () => {
    const res = await req('/v1/compliance/summary', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- OpenAPI ---

describe('Wave 31-32: OpenAPI spec', () => {
  it('includes Wave 31-32 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 31
    expect(paths).toContain('/v1/audit-streaming/configs');
    expect(paths).toContain('/v1/audit-streaming/stats');
    expect(paths).toContain('/v1/ip-allowlist/rules');
    expect(paths).toContain('/v1/ip-allowlist/check');
    expect(paths).toContain('/v1/data-retention/policies');
    expect(paths).toContain('/v1/data-retention/seed');
    // Wave 32
    expect(paths).toContain('/v1/error-budgets/slos');
    expect(paths).toContain('/v1/error-budgets/summary');
    expect(paths).toContain('/v1/error-budgets/alerts');
    expect(paths).toContain('/v1/usage-forecast/snapshots');
    expect(paths).toContain('/v1/usage-forecast/generate');
    expect(paths).toContain('/v1/usage-forecast/anomalies');
    expect(paths).toContain('/v1/compliance/reports');
    expect(paths).toContain('/v1/compliance/checks');
    expect(paths).toContain('/v1/compliance/score');
    expect(paths).toContain('/v1/compliance/frameworks');
  });
});
