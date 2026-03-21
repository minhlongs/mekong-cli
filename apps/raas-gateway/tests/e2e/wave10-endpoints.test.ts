/**
 * E2E tests — Wave 9-10 endpoints: referrals, projects, team, webhook management
 */

import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

// ---------------------------------------------------------------------------
// Mock helpers (same pattern as checkout-metrics-docs.test.ts)
// ---------------------------------------------------------------------------

class MockKV {
  private store: Map<string, string> = new Map();

  async get(key: string, type?: 'json'): Promise<any> {
    const value = this.store.get(key);
    if (value === undefined) return null;
    if (type === 'json') return JSON.parse(value);
    return value;
  }

  async put(key: string, value: string, _options?: { expirationTtl?: number }): Promise<void> {
    this.store.set(key, value);
  }

  async delete(key: string): Promise<void> {
    this.store.delete(key);
  }
}

class MockD1 {
  prepare(_query: string) {
    const stmt = {
      bind: (..._args: any[]) => stmt,
      first: async () => null,
      run: async () => ({ success: true, meta: { changes: 1 } }),
      all: async () => ({ results: [] }),
    };
    return stmt;
  }

  async batch(_statements: any[]) {
    return [];
  }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';

async function makeToken(tier = 'pro'): Promise<string> {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setIssuer('raas-gateway')
    .setAudience('raas-api')
    .setExpirationTime('1h')
    .sign(secret);
}

function authHeader(token: string) {
  return { Authorization: `Bearer ${token}` };
}

// ---------------------------------------------------------------------------
// Test suite
// ---------------------------------------------------------------------------

describe('Wave 10 E2E: Referrals, Projects, Team, Webhook Management', () => {
  let env: Env;
  let token: string;

  beforeEach(async () => {
    env = {
      RATE_LIMIT_KV: new MockKV() as any,
      SESSION_KV: new MockKV() as any,
      DB: new MockD1() as any,
      JWT_SECRET=REDACTED,
      POLAR_WEBHOOK_SECRET: 'test-webhook-secret',
      ENVIRONMENT: 'test',
      LOG_LEVEL: 'debug',
      AI: {} as any,
      TELEGRAM_BOT_TOKEN: 'test-bot-token',
    };
    token = await makeToken('pro');
  });

  // -------------------------------------------------------------------------
  // Referrals
  // -------------------------------------------------------------------------

  describe('POST /v1/referrals/generate', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/referrals/generate', { method: 'POST' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 with referral_code when authenticated', async () => {
      const res = await app.request(
        '/v1/referrals/generate',
        { method: 'POST', headers: authHeader(token) },
        env,
      );
      // MockD1.first returns null → code is generated, still 200
      expect([200, 201]).toContain(res.status);
      const data = await res.json() as any;
      expect(data.referral_code).toBeDefined();
      expect(data.referral_url).toBeDefined();
    });
  });

  describe('GET /v1/referrals/stats', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/referrals/stats', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 with stats object when authenticated', async () => {
      const res = await app.request(
        '/v1/referrals/stats',
        { method: 'GET', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(typeof data.referral_count).toBe('number');
      expect(typeof data.total_bonus_credits).toBe('number');
      expect(Array.isArray(data.referrals)).toBe(true);
    });
  });

  describe('POST /v1/referrals/apply', () => {
    // /apply is intended public but sits behind the /v1 global auth middleware in practice
    it('returns 400 when referral_code or tenant_id missing (authenticated)', async () => {
      const res = await app.request('/v1/referrals/apply', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }, env);
      expect(res.status).toBe(400);
    });

    it('returns 404 when referral code not found (authenticated)', async () => {
      const res = await app.request('/v1/referrals/apply', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ referral_code: 'BADCODE', tenant_id: 'other-tenant' }),
      }, env);
      // MockD1.first returns null → referrer not found
      expect(res.status).toBe(404);
    });
  });

  // -------------------------------------------------------------------------
  // Projects
  // -------------------------------------------------------------------------

  describe('POST /v1/projects', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Test' }),
      }, env);
      expect(res.status).toBe(401);
    });

    it('returns 400 when name is missing', async () => {
      const res = await app.request('/v1/projects', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({}),
      }, env);
      expect(res.status).toBe(400);
    });

    it('returns 201 on project creation', async () => {
      const res = await app.request('/v1/projects', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'My Project' }),
      }, env);
      expect(res.status).toBe(201);
    });
  });

  describe('GET /v1/projects', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/projects', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 with projects array', async () => {
      const res = await app.request(
        '/v1/projects',
        { method: 'GET', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.projects)).toBe(true);
    });
  });

  describe('GET /v1/projects/:id', () => {
    it('returns 404 when project not found', async () => {
      const res = await app.request(
        '/v1/projects/nonexistent-id',
        { method: 'GET', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(404);
    });
  });

  describe('DELETE /v1/projects/:id', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/projects/some-id', { method: 'DELETE' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 404 when project not found', async () => {
      const res = await app.request(
        '/v1/projects/nonexistent-id',
        { method: 'DELETE', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(404);
    });
  });

  // -------------------------------------------------------------------------
  // Team
  // -------------------------------------------------------------------------

  describe('POST /v1/team/invite', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/team/invite', { method: 'POST' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 403 for starter tier', async () => {
      const starterToken = await makeToken('starter');
      const res = await app.request('/v1/team/invite', {
        method: 'POST',
        headers: { ...authHeader(starterToken), 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'test@example.com', role: 'member' }),
      }, env);
      expect(res.status).toBe(403);
    });

    it('returns 400 for invalid email on pro tier', async () => {
      const res = await app.request('/v1/team/invite', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'not-an-email', role: 'member' }),
      }, env);
      expect(res.status).toBe(400);
    });

    it('returns 201 for valid invite on pro tier', async () => {
      const res = await app.request('/v1/team/invite', {
        method: 'POST',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: 'member@example.com', role: 'member' }),
      }, env);
      expect(res.status).toBe(201);
      const data = await res.json() as any;
      expect(data.email).toBe('member@example.com');
      expect(data.status).toBe('pending');
    });
  });

  describe('GET /v1/team/members', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/team/members', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 with members array', async () => {
      const res = await app.request(
        '/v1/team/members',
        { method: 'GET', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.members)).toBe(true);
    });
  });

  describe('PUT /v1/team/members/:id', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/team/members/some-id', { method: 'PUT' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 404 when member not found', async () => {
      const res = await app.request('/v1/team/members/nonexistent', {
        method: 'PUT',
        headers: { ...authHeader(token), 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'admin' }),
      }, env);
      // MockD1.first returns null → 404
      expect(res.status).toBe(404);
    });
  });

  describe('DELETE /v1/team/members/:id', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/team/members/some-id', { method: 'DELETE' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 when member removed (mock returns changes=1)', async () => {
      const res = await app.request(
        '/v1/team/members/some-id',
        { method: 'DELETE', headers: authHeader(token) },
        env,
      );
      // MockD1.run returns meta.changes=1 → success
      expect(res.status).toBe(200);
    });
  });

  // -------------------------------------------------------------------------
  // Webhook Management
  // -------------------------------------------------------------------------

  describe('GET /v1/webhooks/events', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/webhooks/events', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 with event types array', async () => {
      const res = await app.request(
        '/v1/webhooks/events',
        { method: 'GET', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect(Array.isArray(data.events)).toBe(true);
      expect(data.events.length).toBeGreaterThan(0);
    });
  });

  describe('POST /v1/webhooks/test', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/webhooks/test', { method: 'POST' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 400 when no webhook_url configured', async () => {
      const res = await app.request(
        '/v1/webhooks/test',
        { method: 'POST', headers: authHeader(token) },
        env,
      );
      // MockD1.first returns null → no webhook_url → 400
      expect(res.status).toBe(400);
    });
  });

  describe('GET /v1/webhooks/config', () => {
    it('returns 401 without auth', async () => {
      const res = await app.request('/v1/webhooks/config', { method: 'GET' }, env);
      expect(res.status).toBe(401);
    });

    it('returns 200 with config object', async () => {
      const res = await app.request(
        '/v1/webhooks/config',
        { method: 'GET', headers: authHeader(token) },
        env,
      );
      expect(res.status).toBe(200);
      const data = await res.json() as any;
      expect('webhook_url' in data).toBe(true);
      expect('events_subscribed' in data).toBe(true);
    });
  });
});
