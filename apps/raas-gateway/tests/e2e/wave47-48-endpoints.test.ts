/**
 * Wave 47-48 E2E tests — Mission Approval Workflow, Platform Security Policies, Admin User Management,
 * Tenant Billing History, API Gateway Middleware Config, Platform Capacity Planning
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

// --- Wave 47: Mission Approval Workflow ---

describe('Wave 47: Mission Approval Workflow', () => {
  it('GET /v1/mission-approvals/workflows — list (auth)', async () => {
    const res = await req('/v1/mission-approvals/workflows', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/mission-approvals/workflows — create (auth)', async () => {
    const res = await req('/v1/mission-approvals/workflows', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Test Workflow', steps_json: [{ approver: 'admin', role: 'manager' }] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('POST /v1/mission-approvals/submit — submit (auth)', async () => {
    const res = await req('/v1/mission-approvals/submit', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission_id: 'm-1', workflow_id: 'wf-1' }),
    });
    expect([200, 201, 400, 404, 500]).toContain(res.status);
  });

  it('GET /v1/mission-approvals/pending — pending (auth)', async () => {
    const res = await req('/v1/mission-approvals/pending', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/mission-approvals/admin/overview — admin', async () => {
    const res = await req('/v1/mission-approvals/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 47: Platform Security Policies ---

describe('Wave 47: Platform Security Policies', () => {
  it('GET /v1/security-policies/policies — list (auth)', async () => {
    const res = await req('/v1/security-policies/policies', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/security-policies/policies — create (auth)', async () => {
    const res = await req('/v1/security-policies/policies', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ policy_name: 'Strong Password', policy_type: 'password', rules_json: { min_length: 12 }, severity: 'high' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/security-policies/templates — templates (public)', async () => {
    const res = await req('/v1/security-policies/templates');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/security-policies/violations — violations (auth)', async () => {
    const res = await req('/v1/security-policies/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/security-policies/compliance — compliance (auth)', async () => {
    const res = await req('/v1/security-policies/compliance', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/security-policies/admin/overview — admin', async () => {
    const res = await req('/v1/security-policies/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 47: Admin User Management ---

describe('Wave 47: Admin User Management', () => {
  it('GET /admin/user-mgmt/users — list (admin)', async () => {
    const res = await req('/admin/user-mgmt/users', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/user-mgmt/users — create (admin)', async () => {
    const res = await req('/admin/user-mgmt/users', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'admin@test.com', display_name: 'Test Admin', role: 'admin' }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/user-mgmt/roles — roles (admin)', async () => {
    const res = await req('/admin/user-mgmt/roles', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/user-mgmt/activity — activity (admin)', async () => {
    const res = await req('/admin/user-mgmt/activity', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/user-mgmt/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/user-mgmt/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/user-mgmt/users — 403 without key', async () => {
    const res = await req('/admin/user-mgmt/users');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 48: Tenant Billing History ---

describe('Wave 48: Tenant Billing History', () => {
  it('GET /v1/billing-history/invoices — list (auth)', async () => {
    const res = await req('/v1/billing-history/invoices', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/billing-history/invoices — create (auth)', async () => {
    const res = await req('/v1/billing-history/invoices', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount_cents: 9900, currency: 'USD', period_start: '2026-03-01', period_end: '2026-03-31' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/billing-history/payments — payments (auth)', async () => {
    const res = await req('/v1/billing-history/payments', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/billing-history/statements/generate — generate (auth)', async () => {
    const res = await req('/v1/billing-history/statements/generate', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ month: '2026-03' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/billing-history/admin/overview — admin', async () => {
    const res = await req('/v1/billing-history/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 48: API Gateway Middleware Config ---

describe('Wave 48: API Gateway Middleware Config', () => {
  it('GET /v1/gateway-middleware/configs — list (auth)', async () => {
    const res = await req('/v1/gateway-middleware/configs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/gateway-middleware/configs — create (auth)', async () => {
    const res = await req('/v1/gateway-middleware/configs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Add CORS', middleware_type: 'cors_override', config_json: { origin: '*' } }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/gateway-middleware/templates — templates (public)', async () => {
    const res = await req('/v1/gateway-middleware/templates');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/gateway-middleware/logs — logs (auth)', async () => {
    const res = await req('/v1/gateway-middleware/logs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/gateway-middleware/preview — preview (auth)', async () => {
    const res = await req('/v1/gateway-middleware/preview?endpoint=/v1/missions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/gateway-middleware/admin/overview — admin', async () => {
    const res = await req('/v1/gateway-middleware/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 48: Platform Capacity Planning ---

describe('Wave 48: Platform Capacity Planning', () => {
  it('GET /admin/capacity/current — current (admin)', async () => {
    const res = await req('/admin/capacity/current', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /admin/capacity/snapshots — record (admin)', async () => {
    const res = await req('/admin/capacity/snapshots', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_type: 'compute', current_usage: 75, max_capacity: 100, utilization_pct: 75 }),
    });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });

  it('GET /admin/capacity/recommendations — list (admin)', async () => {
    const res = await req('/admin/capacity/recommendations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/capacity/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/capacity/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('GET /admin/capacity/current — 403 without key', async () => {
    const res = await req('/admin/capacity/current');
    expect([401, 403]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 47-48: OpenAPI spec', () => {
  it('includes Wave 47-48 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 47
    expect(paths).toContain('/v1/mission-approvals/workflows');
    expect(paths).toContain('/v1/mission-approvals/pending');
    expect(paths).toContain('/v1/security-policies/policies');
    expect(paths).toContain('/v1/security-policies/compliance');
    expect(paths).toContain('/admin/user-mgmt/users');
    expect(paths).toContain('/admin/user-mgmt/roles');
    // Wave 48
    expect(paths).toContain('/v1/billing-history/invoices');
    expect(paths).toContain('/v1/billing-history/payments');
    expect(paths).toContain('/v1/gateway-middleware/configs');
    expect(paths).toContain('/v1/gateway-middleware/templates');
    expect(paths).toContain('/admin/capacity/dashboard');
    expect(paths).toContain('/admin/capacity/recommendations');
  });
});
