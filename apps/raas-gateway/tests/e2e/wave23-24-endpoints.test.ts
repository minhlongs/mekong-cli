/**
 * Wave 23-24 E2E tests — SSE events, event bus, webhook v2, rate limits v2, tenant isolation, deep health
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

// --- Wave 23: Event Streaming ---

describe('Wave 23: Event Streaming', () => {
  it('POST /v1/events/publish — publish event', async () => {
    const res = await req('/v1/events/publish', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission_id: 'mission-1', event_type: 'mission.completed', payload: { result: 'ok' } }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/events/active — active streams count', async () => {
    const res = await req('/v1/events/active', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/events/publish — 401 without auth', async () => {
    const res = await req('/v1/events/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mission_id: 'm1', event_type: 'test' }),
    });
    expect(res.status).toBe(401);
  });
});

// --- Wave 23: Event Bus ---

describe('Wave 23: Event Bus', () => {
  it('GET /v1/event-bus/events — list events', async () => {
    const res = await req('/v1/event-bus/events', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/event-bus/stats — event stats', async () => {
    const res = await req('/v1/event-bus/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/event-bus/subscribe — subscribe to events', async () => {
    const res = await req('/v1/event-bus/subscribe', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_types: ['mission.completed'], webhook_url: 'https://example.com/hook' }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/event-bus/subscriptions — list subscriptions', async () => {
    const res = await req('/v1/event-bus/subscriptions', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/event-bus/emit — emit event', async () => {
    const res = await req('/v1/event-bus/emit', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'mission.created', payload: { goal: 'test' } }),
    });
    expect(res.status).toBeLessThan(500);
  });
});

// --- Wave 23: Webhook v2 ---

describe('Wave 23: Webhook v2', () => {
  it('POST /v1/webhooks-v2 — create webhook', async () => {
    const res = await req('/v1/webhooks-v2', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://example.com/webhook', events: ['mission.completed'] }),
    });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhooks-v2 — list webhooks', async () => {
    const res = await req('/v1/webhooks-v2', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/webhooks-v2/stats — webhook stats', async () => {
    const res = await req('/v1/webhooks-v2/stats', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('POST /v1/webhooks-v2 — 401 without auth', async () => {
    const res = await req('/v1/webhooks-v2', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: 'https://example.com/webhook' }),
    });
    expect(res.status).toBe(401);
  });
});

// --- Wave 24: Rate Limiting v2 ---

describe('Wave 24: Rate Limiting v2', () => {
  it('GET /v1/rate-limits — rate limit status', async () => {
    const res = await req('/v1/rate-limits', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-limits/history — rate limit history', async () => {
    const res = await req('/v1/rate-limits/history', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-limits/tiers — tier configs (public)', async () => {
    const res = await req('/v1/rate-limits/tiers');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    expect(body.data || body.tiers || body.starter).toBeDefined();
  });

  it('GET /v1/rate-limits/top-limited — admin only', async () => {
    const res = await req('/v1/rate-limits/top-limited', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/rate-limits/top-limited — 401 without admin key', async () => {
    const res = await req('/v1/rate-limits/top-limited');
    expect(res.status).toBe(401);
  });
});

// --- Wave 24: Tenant Isolation ---

describe('Wave 24: Tenant Isolation', () => {
  it('GET /v1/isolation/status — isolation context', async () => {
    const res = await req('/v1/isolation/status', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/isolation/scope — data scope', async () => {
    const res = await req('/v1/isolation/scope', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/isolation/score — isolation score', async () => {
    const res = await req('/v1/isolation/score', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/isolation/violations — violation history', async () => {
    const res = await req('/v1/isolation/violations', { headers: { Authorization: `Bearer ${token}` } });
    expect(res.status).toBeLessThan(500);
  });

  it('GET /v1/isolation/status — 401 without auth', async () => {
    const res = await req('/v1/isolation/status');
    expect(res.status).toBe(401);
  });
});

// --- Wave 24: Deep Health ---

describe('Wave 24: Deep Health', () => {
  it('GET /health/deep — full health check', async () => {
    const res = await req('/health/deep');
    // 503 acceptable — mock D1/KV fail health checks (no real database)
    expect([200, 207, 503]).toContain(res.status);
  });

  it('GET /health/deep/d1 — D1 health', async () => {
    const res = await req('/health/deep/d1');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /health/deep/kv — KV health', async () => {
    const res = await req('/health/deep/kv');
    expect(res.status).toBeLessThan(500);
  });

  it('GET /health/deep/history — admin only', async () => {
    const res = await req('/health/deep/history', { headers: { 'X-Admin-Key': ADMIN_API_KEY } });
    expect(res.status).toBeLessThan(500);
  });
});

// --- OpenAPI ---

describe('Wave 23-24: OpenAPI spec', () => {
  it('includes Wave 23-24 paths', async () => {
    const res = await req('/openapi.json');
    expect(res.status).toBe(200);
    const body = await res.json() as any;
    const paths = Object.keys(body.paths);
    expect(paths).toContain('/v1/events/publish');
    expect(paths).toContain('/v1/event-bus/events');
    expect(paths).toContain('/v1/event-bus/subscribe');
    expect(paths).toContain('/v1/webhooks-v2');
    expect(paths).toContain('/v1/webhooks-v2/{id}/deliveries');
    expect(paths).toContain('/v1/rate-limits/tiers');
    expect(paths).toContain('/v1/rate-limits/custom');
    expect(paths).toContain('/v1/isolation/status');
    expect(paths).toContain('/v1/isolation/scope');
    expect(paths).toContain('/health/deep/d1');
  });
});
