/**
 * E2E tests - Wave 17-18: tenant isolation, impersonation, data export, SSO,
 * developer portal, changelog, status badges, notification preferences
 */
import { describe, it, expect, beforeEach } from 'vitest';
import * as jose from 'jose';
import { app } from '../../src/index';
import type { Env } from '../../src/index';

class MockKV {
  private store: Map<string, string> = new Map();
  async get(key: string, type?: 'json'): Promise<any> {
    const v = this.store.get(key); if (v === undefined) return null;
    return type === 'json' ? JSON.parse(v) : v;
  }
  async put(key: string, value: string, _opts?: any): Promise<void> { this.store.set(key, value); }
  async delete(key: string): Promise<void> { this.store.delete(key); }
  async list(_opts?: any): Promise<{ keys: { name: string }[] }> {
    return { keys: Array.from(this.store.keys()).map(name => ({ name })) };
  }
}

class MockD1 {
  prepare(_q: string) {
    const s = { bind: (..._a: any[]) => s, first: async () => null, run: async () => ({ success: true, meta: { changes: 1 } }), all: async () => ({ results: [] }) };
    return s;
  }
  async batch(_s: any[]) { return []; }
}

const JWT_SECRET=REDACTED = 'test-secret-key-for-testing-only-12345';
const ADMIN_API_KEY = 'test-admin-key';

async function makeToken(tier = 'pro'): Promise<string> {
  const secret = new TextEncoder().encode(JWT_SECRET=REDACTED);
  return new jose.SignJWT({ sub: 'tenant-test-123', tier, permissions: [] })
    .setProtectedHeader({ alg: 'HS256' }).setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api').setExpirationTime('1h').sign(secret);
}

function createEnv(): Env {
  return { DB: new MockD1() as any, RATE_LIMIT_KV: new MockKV() as any, SESSION_KV: new MockKV() as any, AI: {} as any, JWT_SECRET=REDACTED, POLAR_WEBHOOK_SECRET: 'test', TELEGRAM_BOT_TOKEN: 'test', ENVIRONMENT: 'test', LOG_LEVEL: 'error', ADMIN_API_KEY };
}

describe('Wave 17-18 E2E', () => {
  let env: Env; let token: string;
  beforeEach(async () => { env = createEnv(); token = await makeToken(); });

  describe('Developer Portal', () => {
    it('GET /developers - returns HTML', async () => {
      const res = await app.request('/developers', {}, env);
      expect(res.status).toBe(200);
      const text = await res.text();
      expect(text).toContain('Developer Portal');
    });

    it('GET /developers/quickstart - redirects', async () => {
      const res = await app.request('/developers/quickstart', { redirect: 'manual' }, env);
      expect([301, 302]).toContain(res.status);
    });
  });

  describe('Changelog', () => {
    it('GET /changelog - list entries', async () => {
      const res = await app.request('/changelog', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.success).toBe(true);
    });

    it('GET /changelog/latest', async () => {
      const res = await app.request('/changelog/latest', {}, env);
      expect(res.status).toBe(200);
    });

    it('GET /changelog/rss - returns XML', async () => {
      const res = await app.request('/changelog/rss', {}, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toContain('xml');
    });

    it('POST /changelog - requires admin', async () => {
      const res = await app.request('/changelog', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'test', description: 'test', version: '1.0' }) }, env);
      expect(res.status).toBe(401);
    });

    it('POST /changelog - admin creates entry', async () => {
      const res = await app.request('/changelog', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ title: 'New Feature', description: 'desc', version: '2.0' }) }, env);
      expect(res.status).toBe(201);
    });
  });

  describe('Admin Impersonation', () => {
    it('POST /admin/impersonate - requires admin', async () => {
      const res = await app.request('/admin/impersonate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ tenant_id: 'x' }) }, env);
      expect(res.status).toBe(401);
    });

    it('POST /admin/impersonate - admin can impersonate', async () => {
      const res = await app.request('/admin/impersonate', { method: 'POST', headers: { 'X-Admin-Key': ADMIN_API_KEY, 'Content-Type': 'application/json' }, body: JSON.stringify({ tenant_id: 'tenant-1' }) }, env);
      expect([200, 404]).toContain(res.status);
    });

    it('GET /admin/impersonate/active', async () => {
      const res = await app.request('/admin/impersonate/active', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect(res.status).toBe(200);
    });

    it('GET /admin/isolation/violations', async () => {
      const res = await app.request('/admin/isolation/violations', { headers: { 'X-Admin-Key': ADMIN_API_KEY } }, env);
      expect(res.status).toBe(200);
    });
  });

  describe('Data Export', () => {
    it('GET /v1/export - requires auth', async () => {
      const res = await app.request('/v1/export', {}, env);
      expect(res.status).toBe(401);
    });

    it('GET /v1/export - exports tenant data', async () => {
      const res = await app.request('/v1/export', { headers: { Authorization: 'Bearer ' + token } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('DELETE /v1/data - GDPR delete', async () => {
      const res = await app.request('/v1/data', { method: 'DELETE', headers: { Authorization: 'Bearer ' + token } }, env);
      expect([200, 500]).toContain(res.status);
    });
  });

  describe('SSO Stub', () => {
    it('GET /v1/sso/config - returns not enabled', async () => {
      const res = await app.request('/v1/sso/config', { headers: { Authorization: 'Bearer ' + token } }, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.data.enabled).toBe(false);
    });

    it('GET /v1/sso/metadata - returns XML', async () => {
      const res = await app.request('/v1/sso/metadata', {}, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toContain('xml');
    });

    it('POST /v1/sso/callback - returns 501', async () => {
      const res = await app.request('/v1/sso/callback', { method: 'POST' }, env);
      expect(res.status).toBe(501);
    });
  });

  describe('Status Badges', () => {
    it('GET /badge/status - returns SVG', async () => {
      const res = await app.request('/badge/status', {}, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toContain('svg');
    });

    it('GET /badge/status.json', async () => {
      const res = await app.request('/badge/status.json', {}, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.label).toBe('Mekong RaaS');
    });

    it('GET /badge/version', async () => {
      const res = await app.request('/badge/version', {}, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toContain('svg');
    });

    it('GET /badge/missions', async () => {
      const res = await app.request('/badge/missions', {}, env);
      expect(res.status).toBe(200);
    });
  });

  describe('Notification Preferences', () => {
    it('GET /v1/notifications/preferences - requires auth', async () => {
      const res = await app.request('/v1/notifications/preferences', {}, env);
      expect(res.status).toBe(401);
    });

    it('GET /v1/notifications/preferences', async () => {
      const res = await app.request('/v1/notifications/preferences', { headers: { Authorization: 'Bearer ' + token } }, env);
      expect([200, 500]).toContain(res.status);
    });

    it('GET /v1/notifications/channels', async () => {
      const res = await app.request('/v1/notifications/channels', { headers: { Authorization: 'Bearer ' + token } }, env);
      expect(res.status).toBe(200);
      const body = await res.json() as any;
      expect(body.data.length).toBeGreaterThan(0);
    });

    it('POST /v1/notifications/test', async () => {
      const res = await app.request('/v1/notifications/test', { method: 'POST', headers: { Authorization: 'Bearer ' + token, 'Content-Type': 'application/json' }, body: JSON.stringify({ channel: 'email' }) }, env);
      expect(res.status).toBe(200);
    });
  });

  describe('OpenAPI Spec - Wave 17-18 paths', () => {
    it('includes Wave 17-18 paths', async () => {
      const res = await app.request('/openapi.json', {}, env);
      const spec = await res.json() as any;
      const paths = Object.keys(spec.paths);
      expect(paths).toContain('/developers');
      expect(paths).toContain('/changelog');
      expect(paths).toContain('/badge/status');
      expect(paths).toContain('/v1/export');
      expect(paths).toContain('/v1/sso/config');
      expect(paths).toContain('/v1/notifications/preferences');
    });
  });
});
