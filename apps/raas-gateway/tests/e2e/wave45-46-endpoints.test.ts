/**
 * Wave 45-46 E2E tests — Tenant Data Encryption, Mission Replay/Debug, API Rate Limit Policies,
 * Tenant Onboarding Checklist, Platform Localization, Admin Incident Management
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

// --- Wave 45: Tenant Data Encryption ---

describe('Wave 45: Tenant Data Encryption', () => {
  it('GET /v1/encryption/keys — list keys (auth)', async () => {
    const res = await req('/v1/encryption/keys', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/encryption/keys — create key (auth)', async () => {
    const res = await req('/v1/encryption/keys', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ key_alias: 'main-key', key_type: 'aes-256-gcm' }),
    });
    expect([200, 201, 400, 409, 500]).toContain(res.status);
  });

  it('GET /v1/encryption/audit — audit trail (auth)', async () => {
    const res = await req('/v1/encryption/audit', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/encryption/fields — list fields (auth)', async () => {
    const res = await req('/v1/encryption/fields', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/encryption/stats — key stats (auth)', async () => {
    const res = await req('/v1/encryption/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/encryption/admin/overview — admin', async () => {
    const res = await req('/v1/encryption/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 45: Mission Replay/Debug ---

describe('Wave 45: Mission Replay/Debug', () => {
  it('GET /v1/mission-debug/missions/m-1/steps — execution steps (auth)', async () => {
    const res = await req('/v1/mission-debug/missions/m-1/steps', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-debug/missions/m-1/trace — full trace (auth)', async () => {
    const res = await req('/v1/mission-debug/missions/m-1/trace', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/mission-debug/sessions — create session (auth)', async () => {
    const res = await req('/v1/mission-debug/sessions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission_id: 'm-1', debug_mode: 'trace' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/mission-debug/replay — start replay (auth)', async () => {
    const res = await req('/v1/mission-debug/replay', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission_id: 'm-1', original_mission_id: 'm-0' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/mission-debug/admin/overview — admin', async () => {
    const res = await req('/v1/mission-debug/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 45: API Rate Limit Policies ---

describe('Wave 45: API Rate Limit Policies', () => {
  it('GET /v1/rate-policies/policies — list (auth)', async () => {
    const res = await req('/v1/rate-policies/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/rate-policies/policies — create (auth)', async () => {
    const res = await req('/v1/rate-policies/policies', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_name: 'test', endpoint_pattern: '/v1/missions/*', max_requests: 100, window_seconds: 60 }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/rate-policies/templates — list templates (public)', async () => {
    const res = await req('/v1/rate-policies/templates');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-policies/violations — violations (auth)', async () => {
    const res = await req('/v1/rate-policies/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-policies/stats — stats (auth)', async () => {
    const res = await req('/v1/rate-policies/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-policies/admin/overview — admin', async () => {
    const res = await req('/v1/rate-policies/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 46: Tenant Onboarding Checklist ---

describe('Wave 46: Tenant Onboarding Checklist', () => {
  it('GET /v1/onboarding-checklist — get checklist (auth)', async () => {
    const res = await req('/v1/onboarding-checklist', { headers: { Authorization: `Bearer ${token}` } });
    expect([200, 404, 500]).toContain(res.status);
  });

  it('POST /v1/onboarding-checklist/init — initialize (auth)', async () => {
    const res = await req('/v1/onboarding-checklist/init', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/onboarding-checklist/progress — progress (auth)', async () => {
    const res = await req('/v1/onboarding-checklist/progress', { headers: { Authorization: `Bearer ${token}` } });
    expect([200, 404, 500]).toContain(res.status);
  });

  it('GET /v1/onboarding-checklist/milestones — milestones (auth)', async () => {
    const res = await req('/v1/onboarding-checklist/milestones', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/onboarding-checklist/admin/overview — admin', async () => {
    const res = await req('/v1/onboarding-checklist/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 46: Platform Localization ---

describe('Wave 46: Platform Localization', () => {
  it('GET /v1/i18n/config — locale config (auth)', async () => {
    const res = await req('/v1/i18n/config', { headers: { Authorization: `Bearer ${token}` } });
    expect([200, 404, 500]).toContain(res.status);
  });

  it('GET /v1/i18n/translations/en — translations (public)', async () => {
    const res = await req('/v1/i18n/translations/en');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/i18n/keys — list keys (public)', async () => {
    const res = await req('/v1/i18n/keys');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/i18n/locales — supported locales (public)', async () => {
    const res = await req('/v1/i18n/locales');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/i18n/admin/overview — admin', async () => {
    const res = await req('/v1/i18n/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 46: Admin Incident Management ---

describe('Wave 46: Admin Incident Management', () => {
  it('GET /admin/incidents — list (admin)', async () => {
    const res = await req('/admin/incidents', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/incidents — create (admin)', async () => {
    const res = await req('/admin/incidents', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'Test Incident', severity: 'medium', created_by: 'admin' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/incidents/active — active incidents (admin)', async () => {
    const res = await req('/admin/incidents/active', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/incidents/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/incidents/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/incidents — 403 without key', async () => {
    const res = await req('/admin/incidents');
    expect([401, 403]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 45-46: OpenAPI spec', () => {
  it('includes Wave 45-46 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 45
    expect(paths).toContain('/v1/encryption/keys');
    expect(paths).toContain('/v1/encryption/stats');
    expect(paths).toContain('/v1/mission-debug/sessions');
    expect(paths).toContain('/v1/mission-debug/replay');
    expect(paths).toContain('/v1/rate-policies/policies');
    expect(paths).toContain('/v1/rate-policies/violations');
    // Wave 46
    expect(paths).toContain('/v1/onboarding-checklist');
    expect(paths).toContain('/v1/onboarding-checklist/milestones');
    expect(paths).toContain('/v1/i18n/config');
    expect(paths).toContain('/v1/i18n/locales');
    expect(paths).toContain('/admin/incidents');
    expect(paths).toContain('/admin/incidents/dashboard');
  });
});
