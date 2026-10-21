import { describe, it, expect } from 'vitest';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { mkdirSync } from 'node:fs';

import { generateKey } from '../src/core/key-generator.js';
import { LicenseStore } from '../src/core/store.js';
import { LicenseGate } from '../src/core/gate.js';
import { issueKey, batchIssue, auditStore } from '../src/admin/store-admin.js';
import { KeyAdmin } from '../src/admin/key-admin.js';
import { SalesWebhookHandler } from '../src/admin/sales-integration.js';
import { createGate, issueTrialKey } from '../src/integration/gate-helpers.js';
import { withLicenseCheck } from '../src/integration/nextjs-middleware.js';
import { createCliLicenseMiddleware } from '../src/integration/cli-middleware.js';
import { licenseMiddleware } from '../src/integration/express-middleware.js';

function tmpStore(): LicenseStore {
  const dir = join(tmpdir(), `license-sdk-mw-${Date.now()}-${Math.random().toString(36).slice(2)}`);
  mkdirSync(dir, { recursive: true });
  return new LicenseStore(dir);
}

describe('LicenseGate', () => {
  it('defaults to free tier, unauthenticated', () => {
    const store = tmpStore();
    const gate = new LicenseGate({ brand: 'OPENCLAW', store });
    expect(gate.getCurrentTier()).toBe('free');
    expect(gate.getStatus().activated).toBe(false);
  });

  it('canAccess: free command allowed on free tier', () => {
    const store = tmpStore();
    const gate = new LicenseGate({ brand: 'MEKONG', store });
    expect(gate.canAccess('ls', 'free').allowed).toBe(true);
  });

  it('canAccess: pro command denied on free tier', () => {
    const store = tmpStore();
    const gate = new LicenseGate({ brand: 'MEKONG', store });
    const result = gate.canAccess('analytics', 'pro');
    expect(result.allowed).toBe(false);
    expect(result.reason).toMatch(/pro/);
  });

  it('activate via JSON key string upgrades tier', () => {
    const store = tmpStore();
    const k = generateKey('ALGO', 'enterprise', 'corp');
    store.save('ALGO', k);
    const gate = new LicenseGate({ brand: 'ALGO', store });
    expect(gate.getCurrentTier()).toBe('enterprise');
  });

  it('featureMap resolves required tier per command', () => {
    const store = tmpStore();
    const k = generateKey('AGENCYOS', 'pro', 'user');
    store.save('AGENCYOS', k);
    const gate = new LicenseGate({
      brand: 'AGENCYOS',
      featureMap: { export: 'pro', admin: 'enterprise' },
      store,
    });
    expect(gate.canAccess('export').allowed).toBe(true);
    expect(gate.canAccess('admin').allowed).toBe(false);
  });
});

describe('admin: store-admin, key-admin & sales-integration', () => {
  it('issueKey saves to store and returns key', () => {
    const store = tmpStore();
    const k = issueKey('MEKONG', 'pro', 'admin-user', undefined, store);
    expect(k.brand).toBe('MEKONG');
    expect(store.load('MEKONG')).not.toBeNull();
  });

  it('batchIssue returns correct count without saving', () => {
    const keys = batchIssue('SOPHIA', 'starter', 'bulk-owner', 3);
    expect(keys).toHaveLength(3);
  });

  it('auditStore reports valid status', () => {
    const store = tmpStore();
    const k = generateKey('WELL', 'pro', 'audit-user');
    store.save('WELL', k);
    const entries = auditStore(store);
    expect(entries).toHaveLength(1);
    expect(entries[0].status).toBe('valid');
    expect(entries[0].tier).toBe('pro');
  });

  it('KeyAdmin generates, revokes, and exports keys', () => {
    const admin = new KeyAdmin();
    const k = admin.generateOne('MEKONG', 'pro', 'owner1');
    expect(admin.listActive()).toHaveLength(1);
    expect(admin.revokeKey(k.key)).toBe(true);
    expect(admin.isRevoked(k.key)).toBe(true);
    expect(admin.listActive()).toHaveLength(0);
  });

  it('SalesWebhookHandler handles Stripe webhook', () => {
    const handler = new SalesWebhookHandler('MEKONG');
    const res = handler.handleStripeWebhook({
      type: 'payment_intent.succeeded',
      customer: 'cus_123',
      amount: 9900,
    });
    expect(res.success).toBe(true);
    expect(res.key).toMatch(/^MEKONG-/);
  });
});

describe('integration: gate-helpers & middlewares', () => {
  it('createGate returns a LicenseGate', () => {
    const store = tmpStore();
    const gate = createGate({ brand: 'MEKONG', store });
    expect(gate).toBeInstanceOf(LicenseGate);
  });

  it('issueTrialKey saves a starter key and returns key string', () => {
    const store = tmpStore();
    const keyStr = issueTrialKey('OPENCLAW', 'trial-user', 'starter', 14, store);
    expect(keyStr).toMatch(/^OPENCLAW-/);
    const loaded = store.load('OPENCLAW');
    expect(loaded).not.toBeNull();
    expect(loaded!.tier).toBe('starter');
  });

  it('withLicenseCheck rejects missing key and skips unprotected paths', () => {
    const check = withLicenseCheck({ brand: 'MEKONG', protectedPaths: ['/api/pro'] });
    expect(check({ url: '/public' }).allowed).toBe(true);
    expect(check({ url: '/api/pro' }).allowed).toBe(false);
  });

  it('createCliLicenseMiddleware invokes onDenied when access fails', () => {
    let deniedCmd = '';
    const mw = createCliLicenseMiddleware({
      brand: 'MEKONG',
      featureMap: { deploy: 'enterprise' },
      onDenied: (cmd) => {
        deniedCmd = cmd;
      },
    });
    mw({ name: () => 'deploy' });
    expect(deniedCmd).toBe('deploy');
  });

  it('licenseMiddleware returns 401 when no key provided', () => {
    const mw = licenseMiddleware({ brand: 'MEKONG' });
    let statusCode = 0;
    mw(
      { headers: {}, query: {}, path: '/test' },
      {
        status: (code: number) => {
          statusCode = code;
          return { json: () => ({}) };
        },
      },
      () => {}
    );
    expect(statusCode).toBe(401);
  });
});
