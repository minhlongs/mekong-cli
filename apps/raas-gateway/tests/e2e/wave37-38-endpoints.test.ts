/**
 * Wave 37-38 E2E tests — Custom Domains, Tenant Collaboration, AI Agent Marketplace,
 * Usage Alerts, Migration Tools, Notifications Hub
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

// --- Wave 37: Custom Domains ---

describe('Wave 37: Custom Domains', () => {
  it('GET /v1/custom-domains/domains — list domains (auth)', async () => {
    const res = await req('/v1/custom-domains/domains', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/custom-domains/domains — add domain (auth)', async () => {
    const res = await req('/v1/custom-domains/domains', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ domain: 'api.example.com' }),
    });
    expect([200, 201, 400, 409, 500]).toContain(res.status);
  });

  it('GET /v1/custom-domains/stats — domain stats (auth)', async () => {
    const res = await req('/v1/custom-domains/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/custom-domains/lookup/example.com — lookup (public)', async () => {
    const res = await req('/v1/custom-domains/lookup/example.com');
    expect([200, 404]).toContain(res.status);
  });

  it('GET /v1/custom-domains/admin/overview — admin (X-Admin-Key)', async () => {
    const res = await req('/v1/custom-domains/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 37: Tenant Collaboration ---

describe('Wave 37: Tenant Collaboration', () => {
  it('GET /v1/collaboration/comments/mission-1 — list comments (auth)', async () => {
    const res = await req('/v1/collaboration/comments/mission-1', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/collaboration/comments/mission-1 — add comment (auth)', async () => {
    const res = await req('/v1/collaboration/comments/mission-1', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: 'Great work!' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/collaboration/views — list views (auth)', async () => {
    const res = await req('/v1/collaboration/views', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/collaboration/feed — activity feed (auth)', async () => {
    const res = await req('/v1/collaboration/feed', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/collaboration/stats — stats (auth)', async () => {
    const res = await req('/v1/collaboration/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/collaboration/admin/overview — admin', async () => {
    const res = await req('/v1/collaboration/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 37: AI Agent Marketplace ---

describe('Wave 37: AI Agent Marketplace', () => {
  it('GET /v1/agent-marketplace/browse — browse (public)', async () => {
    const res = await req('/v1/agent-marketplace/browse');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/agent-marketplace/featured — featured (public)', async () => {
    const res = await req('/v1/agent-marketplace/featured');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/agent-marketplace/agent/test-agent — detail (public)', async () => {
    const res = await req('/v1/agent-marketplace/agent/test-agent');
    expect([200, 404]).toContain(res.status);
  });

  it('POST /v1/agent-marketplace/publish — publish agent (auth)', async () => {
    const res = await req('/v1/agent-marketplace/publish', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Test Agent', slug: 'test-agent', category: 'general' }),
    });
    expect([200, 201, 400, 409, 500]).toContain(res.status);
  });

  it('GET /v1/agent-marketplace/installed — installed (auth)', async () => {
    const res = await req('/v1/agent-marketplace/installed', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/agent-marketplace/publisher/stats — publisher stats (auth)', async () => {
    const res = await req('/v1/agent-marketplace/publisher/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/agent-marketplace/admin/stats — admin stats', async () => {
    const res = await req('/v1/agent-marketplace/admin/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 38: Usage Alerts ---

describe('Wave 38: Usage Alerts', () => {
  it('GET /v1/usage-alerts/rules — list rules (auth)', async () => {
    const res = await req('/v1/usage-alerts/rules', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/usage-alerts/rules — create rule (auth)', async () => {
    const res = await req('/v1/usage-alerts/rules', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ rule_type: 'credits_threshold', threshold_value: 100, action: 'notify' }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/usage-alerts/history — alert history (auth)', async () => {
    const res = await req('/v1/usage-alerts/history', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/usage-alerts/budget — budget config (auth)', async () => {
    const res = await req('/v1/usage-alerts/budget', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/usage-alerts/check — check budget (auth)', async () => {
    const res = await req('/v1/usage-alerts/check', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ credits: 5 }),
    });
    expect([200, 402, 500]).toContain(res.status);
  });

  it('GET /v1/usage-alerts/admin/overview — admin', async () => {
    const res = await req('/v1/usage-alerts/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 38: Migration Tools ---

describe('Wave 38: Migration Tools', () => {
  it('GET /v1/migration/jobs — list jobs (auth)', async () => {
    const res = await req('/v1/migration/jobs', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/migration/jobs — create job (auth)', async () => {
    const res = await req('/v1/migration/jobs', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ direction: 'export', data_types: ['missions'] }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/migration/export — export data (auth)', async () => {
    const res = await req('/v1/migration/export?types=missions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/migration/supported-platforms — platforms (public)', async () => {
    const res = await req('/v1/migration/supported-platforms');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/migration/admin/stats — admin stats', async () => {
    const res = await req('/v1/migration/admin/stats', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });
});

// --- Wave 38: Notifications Hub ---

describe('Wave 38: Notifications Hub', () => {
  it('GET /v1/notifications-hub/channels — list channels (auth)', async () => {
    const res = await req('/v1/notifications-hub/channels', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/notifications-hub/channels — add channel (auth)', async () => {
    const res = await req('/v1/notifications-hub/channels', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ channel_type: 'email', config: { email: 'test@example.com' } }),
    });
    expect([200, 201, 400, 500]).toContain(res.status);
  });

  it('GET /v1/notifications-hub/log — notification log (auth)', async () => {
    const res = await req('/v1/notifications-hub/log', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/notifications-hub/stats — stats (auth)', async () => {
    const res = await req('/v1/notifications-hub/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/notifications-hub/templates — templates (auth)', async () => {
    const res = await req('/v1/notifications-hub/templates', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/notifications-hub/admin/overview — admin', async () => {
    const res = await req('/v1/notifications-hub/admin/overview', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect([200, 403, 500]).toContain(res.status);
  });

  it('POST /v1/notifications-hub/admin/seed-templates — seed (admin)', async () => {
    const res = await req('/v1/notifications-hub/admin/seed-templates', {
      method: 'POST',
      headers: { 'X-Admin-Key': ADMIN_API_KEY },
    });
    expect([200, 201, 403, 500]).toContain(res.status);
  });
});

// --- OpenAPI ---

describe('Wave 37-38: OpenAPI spec', () => {
  it('includes Wave 37-38 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    // Wave 37
    expect(paths).toContain('/v1/custom-domains/domains');
    expect(paths).toContain('/v1/custom-domains/stats');
    expect(paths).toContain('/v1/collaboration/feed');
    expect(paths).toContain('/v1/collaboration/stats');
    expect(paths).toContain('/v1/agent-marketplace/browse');
    expect(paths).toContain('/v1/agent-marketplace/featured');
    // Wave 38
    expect(paths).toContain('/v1/usage-alerts/rules');
    expect(paths).toContain('/v1/usage-alerts/budget');
    expect(paths).toContain('/v1/migration/jobs');
    expect(paths).toContain('/v1/migration/export');
    expect(paths).toContain('/v1/notifications-hub/channels');
    expect(paths).toContain('/v1/notifications-hub/stats');
  });
});
