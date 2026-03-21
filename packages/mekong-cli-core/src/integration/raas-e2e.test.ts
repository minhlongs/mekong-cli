/**
 * raas-e2e.test.ts — E2E integration tests for RaaS flow: CLI → Gateway → Polar
 * Tests: credential store, MekongClient factory, signup, mission submit, billing checkout
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { mkdtempSync } from 'node:fs';

// ── Module mocks declared before imports that use them ──────────────────────

// Track fs calls and store in-memory state
const fsState: Record<string, string> = {};
let fsExistsResult = false;

vi.mock('node:fs', () => ({
  existsSync: (p: string) => p in fsState,
  readFileSync: (p: string) => {
    if (!(p in fsState)) throw new Error(`ENOENT: ${p}`);
    return fsState[p];
  },
  writeFileSync: (p: string, data: string) => { fsState[p] = data; },
  mkdirSync: () => undefined,
}));

vi.mock('node:os', () => ({
  homedir: () => '/mock-home',
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import {
  loadCredentials,
  saveCredentials,
  clearCredentials,
  isAuthenticated,
  getCloudClient,
  requireCloudClient,
} from '../core/raas-client.js';

// ── Helpers ──────────────────────────────────────────────────────────────────

const CREDS_PATH = '/mock-home/.mekong/credentials.json';

function resetState() {
  // Clear in-memory fs state first (so clearCredentials sees the file)
  for (const k of Object.keys(fsState)) delete fsState[k];
  // clearCredentials() resets _client singleton to null in raas-client module
  clearCredentials();
}

function seedCreds(data: object) {
  fsState[CREDS_PATH] = JSON.stringify(data);
}

// ── Test Suites ──────────────────────────────────────────────────────────────

describe('Credential Store', () => {
  beforeEach(resetState);

  it('returns empty object when no credentials file', () => {
    const creds = loadCredentials();
    expect(creds).toEqual({});
  });

  it('saves and loads credentials round-trip', () => {
    saveCredentials({ jwt: 'tok-abc', email: 'user@test.com', tenantId: 'tenant-1' });
    const creds = loadCredentials();
    expect(creds.jwt).toBe('tok-abc');
    expect(creds.email).toBe('user@test.com');
    expect(creds.tenantId).toBe('tenant-1');
  });

  it('clearCredentials writes empty object', () => {
    seedCreds({ jwt: 'tok-xyz', apiKey: 'ak-123' });
    clearCredentials();
    const creds = loadCredentials();
    expect(creds.jwt).toBeUndefined();
    expect(creds.apiKey).toBeUndefined();
  });

  it('isAuthenticated returns false when no credentials', () => {
    expect(isAuthenticated()).toBe(false);
  });

  it('isAuthenticated returns true when jwt present', () => {
    seedCreds({ jwt: 'tok-valid' });
    expect(isAuthenticated()).toBe(true);
  });

  it('isAuthenticated returns true when apiKey present', () => {
    seedCreds({ apiKey: 'ak-valid' });
    expect(isAuthenticated()).toBe(true);
  });
});

describe('MekongClient Factory', () => {
  beforeEach(resetState);

  it('getCloudClient returns null when not authenticated', () => {
    const client = getCloudClient();
    expect(client).toBeNull();
  });

  it('getCloudClient returns MekongClient when jwt present', () => {
    seedCreds({ jwt: 'tok-abc', baseUrl: 'http://localhost:8787' });
    const client = getCloudClient();
    expect(client).not.toBeNull();
    expect(client).toHaveProperty('missions');
    expect(client).toHaveProperty('billing');
    expect(client).toHaveProperty('credits');
  });

  it('requireCloudClient throws when not authenticated', () => {
    expect(() => requireCloudClient()).toThrow('Not logged in');
  });

  it('requireCloudClient returns client when credentials exist', () => {
    seedCreds({ apiKey: 'ak-test', baseUrl: 'http://localhost:8787' });
    const client = requireCloudClient();
    expect(client).toHaveProperty('missions');
  });
});

describe('Signup Flow (mock fetch)', () => {
  beforeEach(() => {
    resetState();
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => vi.unstubAllGlobals());

  it('signup → save token → isAuthenticated', async () => {
    const mockFetch = vi.mocked(fetch);
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        token: 'jwt-from-gateway',
        credits: 50,
        tenant: { id: 'tenant-xyz', email: 'dev@test.com' },
      }),
    } as Response);

    const res = await fetch('http://localhost:8787/v1/tenants/signup', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: 'Dev', email: 'dev@test.com' }),
    });
    const data = await res.json() as { token: string; tenant: { id: string; email: string }; credits: number };

    saveCredentials({ jwt: data.token, email: data.tenant.email, tenantId: data.tenant.id });

    expect(isAuthenticated()).toBe(true);
    expect(loadCredentials().jwt).toBe('jwt-from-gateway');
    expect(loadCredentials().email).toBe('dev@test.com');
  });
});

describe('Mission Submit Flow (mock fetch)', () => {
  beforeEach(() => {
    resetState();
    seedCreds({ jwt: 'tok-mission', baseUrl: 'http://localhost:8787' });
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => vi.unstubAllGlobals());

  it('submits mission and returns mission id', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: 'mission-001',
        goal: 'Write a blog post',
        status: 'pending',
        credits_cost: 2,
        complexity: 'simple',
        created_at: new Date().toISOString(),
      }),
    } as Response);

    const client = requireCloudClient();
    const mission = await client.missions.submit({ goal: 'Write a blog post', complexity: 'simple' });

    expect(mission.id).toBe('mission-001');
    expect(mission.status).toBe('pending');
    expect(mission.credits_cost).toBe(2);
  });
});

describe('Billing Checkout Flow (mock fetch)', () => {
  beforeEach(() => {
    resetState();
    seedCreds({ jwt: 'tok-billing', baseUrl: 'http://localhost:8787' });
    vi.stubGlobal('fetch', vi.fn());
  });
  afterEach(() => vi.unstubAllGlobals());

  it('creates checkout and returns Polar checkout URL', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        checkout_url: 'https://polar.sh/checkout/session-abc123',
        session_id: 'session-abc123',
        pack_id: 'pack-starter',
      }),
    } as Response);

    const client = requireCloudClient();
    const result = await client.billing.createCheckout({
      pack_id: 'pack-starter',
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
    });

    expect(result.checkout_url).toContain('polar.sh');
    expect(result.checkout_url).toContain('session-abc123');
  });
});
