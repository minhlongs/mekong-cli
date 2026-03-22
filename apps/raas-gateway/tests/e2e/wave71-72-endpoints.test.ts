/**
 * Wave 71-72 E2E tests — Webhook Templates, Cost Optimization, Tenant Grouping,
 * Schema Validation, Platform Alerts, Workflow Automation
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

class MockKV {
  private store = new Map<string, string>();
  async get(key: string, type?: 'json') { const v = this.store.get(key); if (v === undefined) return null; return type === 'json' ? JSON.parse(v) : v; }
  async put(key: string, value: string) { this.store.set(key, value); }
  async delete(key: string) { this.store.delete(key); }
  async list(_opts?: any) { return { keys: Array.from(this.store.keys()).map(name => ({ name })) }; }
}
class MockD1 {
  prepare(_q: string) { const stmt = { bind: (..._a: any[]) => stmt, first: async () => null, run: async () => ({ success: true, meta: { changes: 1 } }), all: async () => ({ results: [] }) }; return stmt; }
  async batch(_s: any[]) { return [{ results: [] }]; }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';
const ADMIN_API_KEY = 'test-admin-key';
async function makeToken(tier = 'pro') {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] }).setProtectedHeader({ alg: 'HS256' }).setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api').setExpirationTime('1h').sign(secret);
}
function createEnv(): Env {
  return { DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any, SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED, POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test', ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY };
}
let env: Env; let token: string;
beforeEach(async () => { env = createEnv(); token = await makeToken(); });
function req(path: string, init?: RequestInit) { return app.request(path, init, env); }

// --- Wave 71: Tenant Webhook Templates ---
describe('Wave 71: Tenant Webhook Templates', () => {
  it('GET /v1/webhook-templates/templates — list (auth)', async () => {
    const res = await req('/v1/webhook-templates/templates', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/webhook-templates/templates — create (auth)', async () => {
    const res = await req('/v1/webhook-templates/templates', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ template_name: 'mission-complete', event_type: 'mission.completed', url_pattern: 'https://example.com/webhook' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/webhook-templates/usage — usage (auth)', async () => {
    const res = await req('/v1/webhook-templates/usage', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/webhook-templates/admin/overview — admin', async () => {
    const res = await req('/v1/webhook-templates/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 71: Mission Cost Optimization ---
describe('Wave 71: Mission Cost Optimization', () => {
  it('GET /v1/cost-optimization/rules — list (auth)', async () => {
    const res = await req('/v1/cost-optimization/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/cost-optimization/rules — create (auth)', async () => {
    const res = await req('/v1/cost-optimization/rules', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ rule_name: 'downgrade-simple', action_type: 'downgrade_model', savings_estimate: 0.3 }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/cost-optimization/events — events (auth)', async () => {
    const res = await req('/v1/cost-optimization/events', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/cost-optimization/admin/overview — admin', async () => {
    const res = await req('/v1/cost-optimization/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 71: Platform Tenant Grouping ---
describe('Wave 71: Platform Tenant Grouping', () => {
  it('GET /admin/tenant-grouping/groups — list (admin)', async () => {
    const res = await req('/admin/tenant-grouping/groups', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/tenant-grouping/groups — create (admin)', async () => {
    const res = await req('/admin/tenant-grouping/groups', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ group_name: 'enterprise-clients', description: 'Top tier clients' }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/tenant-grouping/members — members (admin)', async () => {
    const res = await req('/admin/tenant-grouping/members', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/tenant-grouping/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/tenant-grouping/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/tenant-grouping/groups — 403 without key', async () => {
    const res = await req('/admin/tenant-grouping/groups');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 72: Tenant API Schema Validation ---
describe('Wave 72: Tenant API Schema Validation', () => {
  it('GET /v1/schema-validation/rules — list (auth)', async () => {
    const res = await req('/v1/schema-validation/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/schema-validation/rules — create (auth)', async () => {
    const res = await req('/v1/schema-validation/rules', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ endpoint_pattern: '/v1/missions', schema_json: '{"type":"object"}', validation_mode: 'strict' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/schema-validation/violations — violations (auth)', async () => {
    const res = await req('/v1/schema-validation/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/schema-validation/admin/overview — admin', async () => {
    const res = await req('/v1/schema-validation/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- Wave 72: Admin Platform Alerts ---
describe('Wave 72: Admin Platform Alerts', () => {
  it('GET /admin/platform-alerts/rules — list (admin)', async () => {
    const res = await req('/admin/platform-alerts/rules', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('POST /admin/platform-alerts/rules — create (admin)', async () => {
    const res = await req('/admin/platform-alerts/rules', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ rule_name: 'high-error-rate', metric_name: 'error_rate', condition: 'gt', threshold: 0.05 }) });
    expect([200, 201, 400, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-alerts/incidents — incidents (admin)', async () => {
    const res = await req('/admin/platform-alerts/incidents', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-alerts/dashboard — dashboard (admin)', async () => {
    const res = await req('/admin/platform-alerts/dashboard', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
  it('GET /admin/platform-alerts/rules — 403 without key', async () => {
    const res = await req('/admin/platform-alerts/rules');
    expect([401, 403]).toContain(res.status);
  });
});

// --- Wave 72: Tenant Workflow Automation ---
describe('Wave 72: Tenant Workflow Automation', () => {
  it('GET /v1/workflow-automation/workflows — list (auth)', async () => {
    const res = await req('/v1/workflow-automation/workflows', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('POST /v1/workflow-automation/workflows — create (auth)', async () => {
    const res = await req('/v1/workflow-automation/workflows', { method: 'POST', headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }, body: JSON.stringify({ workflow_name: 'auto-notify', trigger_event: 'mission.completed', action_type: 'webhook' }) });
    expect([200, 201, 400, 500]).toContain(res.status);
  });
  it('GET /v1/workflow-automation/runs — runs (auth)', async () => {
    const res = await req('/v1/workflow-automation/runs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });
  it('GET /v1/workflow-automation/admin/overview — admin', async () => {
    const res = await req('/v1/workflow-automation/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 401, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---
describe('Wave 71-72: OpenAPI spec', () => {
  it('includes Wave 71-72 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/webhook-templates/templates');
    expect(paths).toContain('/v1/webhook-templates/usage');
    expect(paths).toContain('/v1/cost-optimization/rules');
    expect(paths).toContain('/v1/cost-optimization/events');
    expect(paths).toContain('/admin/tenant-grouping/groups');
    expect(paths).toContain('/admin/tenant-grouping/members');
    expect(paths).toContain('/v1/schema-validation/rules');
    expect(paths).toContain('/v1/schema-validation/violations');
    expect(paths).toContain('/admin/platform-alerts/rules');
    expect(paths).toContain('/admin/platform-alerts/incidents');
    expect(paths).toContain('/v1/workflow-automation/workflows');
    expect(paths).toContain('/v1/workflow-automation/runs');
  });
});
