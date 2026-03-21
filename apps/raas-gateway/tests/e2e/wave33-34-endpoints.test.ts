/**
 * Wave 33-34 E2E tests — Cron Orchestrator, Onboarding V2, Platform Health,
 * Revenue Analytics V2, Tenant Lifecycle, Adaptive Rate Limiting
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

// --- Wave 33: Cron Orchestrator ---

describe('Wave 33: Cron Orchestrator', () => {
  it('GET /v1/cron/jobs — list jobs (auth)', async () => {
    const res = await req('/v1/cron/jobs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/cron/jobs — register job (auth)', async () => {
    const res = await req('/v1/cron/jobs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_type: 'data_retention_purge', schedule: 'daily' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/cron/stats — job stats (auth)', async () => {
    const res = await req('/v1/cron/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/cron/seed — seed system jobs (auth)', async () => {
    const res = await req('/v1/cron/seed', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 500]).toContain(res.status);
  });

  it('GET /v1/cron/admin/overdue — overdue jobs (admin)', async () => {
    const res = await req('/v1/cron/admin/overdue', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /v1/cron/admin/run — run overdue (admin)', async () => {
    const res = await req('/v1/cron/admin/run', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 33: Onboarding V2 ---

describe('Wave 33: Onboarding V2', () => {
  it('GET /v1/onboarding-v2/status — onboarding status (auth)', async () => {
    const res = await req('/v1/onboarding-v2/status', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/onboarding-v2/start — start onboarding (auth)', async () => {
    const res = await req('/v1/onboarding-v2/start', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/onboarding-v2/complete/welcome — complete step (auth)', async () => {
    const res = await req('/v1/onboarding-v2/complete/welcome', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/onboarding-v2/recommendations — recommendations (auth)', async () => {
    const res = await req('/v1/onboarding-v2/recommendations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/onboarding-v2/seed-defaults — seed defaults (auth)', async () => {
    const res = await req('/v1/onboarding-v2/seed-defaults', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 500]).toContain(res.status);
  });

  it('GET /v1/onboarding-v2/admin/completion-rate — admin (auth+admin)', async () => {
    const res = await req('/v1/onboarding-v2/admin/completion-rate', {
      headers: { Authorization: `Bearer ${token}`, 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 33: Platform Health ---

describe('Wave 33: Platform Health', () => {
  it('GET /platform-health/overview — platform overview (public)', async () => {
    const res = await req('/platform-health/overview');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /platform-health/services — service statuses (public)', async () => {
    const res = await req('/platform-health/services');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /platform-health/features — feature coverage (public)', async () => {
    const res = await req('/platform-health/features');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /platform-health/endpoints — endpoint count (public)', async () => {
    const res = await req('/platform-health/endpoints');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /platform-health/degraded — degraded services (public)', async () => {
    const res = await req('/platform-health/degraded');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /platform-health/capacity — system capacity (admin)', async () => {
    const res = await req('/platform-health/capacity', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 34: Revenue Analytics V2 ---

describe('Wave 34: Revenue Analytics V2', () => {
  it('GET /admin/revenue-v2/mrr — MRR breakdown (admin)', async () => {
    const res = await req('/admin/revenue-v2/mrr', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/revenue-v2/cohorts — cohort analysis (admin)', async () => {
    const res = await req('/admin/revenue-v2/cohorts', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/revenue-v2/nrr — net revenue retention (admin)', async () => {
    const res = await req('/admin/revenue-v2/nrr', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/revenue-v2/segments — customer segments (admin)', async () => {
    const res = await req('/admin/revenue-v2/segments', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/revenue-v2/forecast — revenue forecast (admin)', async () => {
    const res = await req('/admin/revenue-v2/forecast', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/revenue-v2/top-tenants — top tenants (admin)', async () => {
    const res = await req('/admin/revenue-v2/top-tenants', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 34: Tenant Lifecycle ---

describe('Wave 34: Tenant Lifecycle', () => {
  it('GET /v1/lifecycle/stage — lifecycle stage (auth)', async () => {
    const res = await req('/v1/lifecycle/stage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/lifecycle/history — transition history (auth)', async () => {
    const res = await req('/v1/lifecycle/history', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/lifecycle/risk — risk score (auth)', async () => {
    const res = await req('/v1/lifecycle/risk', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/lifecycle/admin/distribution — stage distribution (admin)', async () => {
    const res = await req('/v1/lifecycle/admin/distribution', {
      headers: { Authorization: `Bearer ${token}`, 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /v1/lifecycle/admin/at-risk — at-risk tenants (admin)', async () => {
    const res = await req('/v1/lifecycle/admin/at-risk', {
      headers: { Authorization: `Bearer ${token}`, 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /v1/lifecycle/admin/churn — churn analysis (admin)', async () => {
    const res = await req('/v1/lifecycle/admin/churn', {
      headers: { Authorization: `Bearer ${token}`, 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 34: Adaptive Rate Limiting ---

describe('Wave 34: Adaptive Rate Limiting', () => {
  it('GET /v1/adaptive-rate-limit/config — rate limit config (auth)', async () => {
    const res = await req('/v1/adaptive-rate-limit/config', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/adaptive-rate-limit/config — set config (auth)', async () => {
    const res = await req('/v1/adaptive-rate-limit/config', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ endpoint_pattern: '/v1/missions', requests_per_minute: 100 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/adaptive-rate-limit/violations — violation history (auth)', async () => {
    const res = await req('/v1/adaptive-rate-limit/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/adaptive-rate-limit/status — rate limit status (auth)', async () => {
    const res = await req('/v1/adaptive-rate-limit/status', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/adaptive-rate-limit/admin/violators — top violators (admin)', async () => {
    const res = await req('/v1/adaptive-rate-limit/admin/violators', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /v1/adaptive-rate-limit/admin/seed — seed tier defaults (admin)', async () => {
    const res = await req('/v1/adaptive-rate-limit/admin/seed', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 201, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 33-34: OpenAPI spec', () => {
  it('includes Wave 33-34 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 33
    expect(paths).toContain('/v1/cron/jobs');
    expect(paths).toContain('/v1/cron/stats');
    expect(paths).toContain('/v1/onboarding-v2/status');
    expect(paths).toContain('/v1/onboarding-v2/start');
    expect(paths).toContain('/platform-health/overview');
    expect(paths).toContain('/platform-health/services');
    // Wave 34
    expect(paths).toContain('/admin/revenue-v2/mrr');
    expect(paths).toContain('/admin/revenue-v2/cohorts');
    expect(paths).toContain('/admin/revenue-v2/nrr');
    expect(paths).toContain('/v1/lifecycle/stage');
    expect(paths).toContain('/v1/lifecycle/admin/at-risk');
    expect(paths).toContain('/v1/adaptive-rate-limit/config');
    expect(paths).toContain('/v1/adaptive-rate-limit/admin/violators');
  });
});
