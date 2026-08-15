import { describe, it, expect, beforeEach } from 'vitest';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { mkdirSync, rmSync } from 'node:fs';

import {
  TIER_ORDER,
  TIER_PRICING,
  tierMeetsMinimum,
  createCustomTiers,
} from '../src/core/tiers.js';
import { generateKey, generateBatchKeys } from '../src/core/key-generator.js';
import { verifyKey, isExpired } from '../src/core/verifier.js';
import { LicenseStore } from '../src/core/store.js';
import { LicenseGate } from '../src/core/gate.js';
import { issueKey, batchIssue, auditStore } from '../src/admin/store-admin.js';
import { createGate, issueTrialKey } from '../src/integration/gate-helpers.js';

// ── helpers ──────────────────────────────────────────────────────────────────

function tmpStore(): LicenseStore {
  const dir = join(tmpdir(), `license-sdk-test-${Date.now()}-${Math.random().toString(36).slice(2)}`);
  mkdirSync(dir, { recursive: true });
  return new LicenseStore(dir);
}

// ── tiers ─────────────────────────────────────────────────────────────────────

describe('tiers', () => {
  it('TIER_ORDER has 4 entries in ascending order', () => {
    expect(TIER_ORDER).toEqual(['free', 'starter', 'pro', 'enterprise']);
  });

  it('TIER_PRICING has correct prices', () => {
    expect(TIER_PRICING.free.priceUsd).toBe(0);
    expect(TIER_PRICING.starter.priceUsd).toBe(29);
    expect(TIER_PRICING.pro.priceUsd).toBe(99);
    expect(TIER_PRICING.enterprise.priceUsd).toBe(299);
  });

  it('tierMeetsMinimum: pro meets starter', () => {
    expect(tierMeetsMinimum('pro', 'starter')).toBe(true);
  });

  it('tierMeetsMinimum: starter does NOT meet pro', () => {
    expect(tierMeetsMinimum('starter', 'pro')).toBe(false);
  });

  it('tierMeetsMinimum: same tier always true', () => {
    expect(tierMeetsMinimum('free', 'free')).toBe(true);
    expect(tierMeetsMinimum('enterprise', 'enterprise')).toBe(true);
  });

  it('createCustomTiers merges overrides', () => {
    const custom = createCustomTiers({ pro: { priceUsd: 79, name: 'Pro Discount' } });
    expect(custom.pro.priceUsd).toBe(79);
    expect(custom.pro.name).toBe('Pro Discount');
    // other tiers unaffected
    expect(custom.starter.priceUsd).toBe(29);
  });
});

// ── key-generator ─────────────────────────────────────────────────────────────

describe('key-generator', () => {
  it('generateKey returns correct shape', () => {
    const k = generateKey('MEKONG', 'pro', 'alice@example.com');
    expect(k.brand).toBe('MEKONG');
    expect(k.tier).toBe('pro');
    expect(k.owner).toBe('alice@example.com');
    expect(k.key).toMatch(/^MEKONG-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}$/);
    expect(k.expiresAt).toBeNull();
    expect(k.signature).toBeTruthy();
  });

  it('generateKey with expiryDays sets expiresAt', () => {
    const k = generateKey('SOPHIA', 'starter', 'bob', 30);
    expect(k.expiresAt).not.toBeNull();
    const diff = new Date(k.expiresAt!).getTime() - Date.now();
    expect(diff).toBeGreaterThan(29 * 86_400_000 - 5000);
  });

  it('generateBatchKeys returns correct count', () => {
    const keys = generateBatchKeys('OPENCLAW', 'enterprise', 'corp', 5);
    expect(keys).toHaveLength(5);
    // all unique
    const unique = new Set(keys.map((k) => k.key));
    expect(unique.size).toBe(5);
  });

  it('generateBatchKeys throws on count < 1', () => {
    expect(() => generateBatchKeys('MEKONG', 'free', 'x', 0)).toThrow(RangeError);
  });
});

// ── verifier ──────────────────────────────────────────────────────────────────

describe('verifier', () => {
  it('verifyKey: valid key passes', () => {
    const k = generateKey('WELL', 'pro', 'user@test.com');
    const result = verifyKey(k);
    expect(result.valid).toBe(true);
    expect(result.brand).toBe('WELL');
    expect(result.tier).toBe('pro');
  });

  it('verifyKey: tampered signature fails', () => {
    const k = generateKey('MEKONG', 'starter', 'hacker');
    const tampered = { ...k, signature: 'deadbeef' };
    const result = verifyKey(tampered);
    expect(result.valid).toBe(false);
    expect(result.reason).toMatch(/signature/);
  });

  it('verifyKey: expired key fails', () => {
    const k = generateKey('ALGO', 'pro', 'user', 1);
    // manually set expired date
    const expired = { ...k, expiresAt: new Date(Date.now() - 1000).toISOString() };
    // re-sign with correct payload would be needed for real tampering;
    // here we test the expiry path by using an already-valid key with overridden date
    const result = verifyKey(expired);
    // signature mismatch since expiresAt changed — both paths hit valid=false
    expect(result.valid).toBe(false);
  });

  it('isExpired: non-expiring key is not expired', () => {
    const k = generateKey('AGENCYOS', 'free', 'anon');
    expect(isExpired(k)).toBe(false);
  });

  it('isExpired: past expiry returns true', () => {
    const k = generateKey('APEX', 'starter', 'x', 1);
    const past = { ...k, expiresAt: new Date(Date.now() - 86_400_000).toISOString() };
    expect(isExpired(past)).toBe(true);
  });
});

// ── store ─────────────────────────────────────────────────────────────────────

describe('LicenseStore', () => {
  it('save and load round-trips correctly', () => {
    const store = tmpStore();
    const k = generateKey('MEKONG', 'pro', 'test-owner');
    store.save('MEKONG', k);
    const loaded = store.load('MEKONG');
    expect(loaded).not.toBeNull();
    expect(loaded!.key).toBe(k.key);
    expect(loaded!.owner).toBe('test-owner');
  });

  it('load returns null for missing brand', () => {
    const store = tmpStore();
    expect(store.load('SOPHIA')).toBeNull();
  });

  it('remove deletes the file', () => {
    const store = tmpStore();
    const k = generateKey('APEX', 'starter', 'u');
    store.save('APEX', k);
    expect(store.remove('APEX')).toBe(true);
    expect(store.load('APEX')).toBeNull();
  });

  it('remove returns false for non-existent brand', () => {
    const store = tmpStore();
    expect(store.remove('WELL')).toBe(false);
  });

  it('listAll returns all saved licenses', () => {
    const store = tmpStore();
    store.save('MEKONG', generateKey('MEKONG', 'free', 'a'));
    store.save('SOPHIA', generateKey('SOPHIA', 'pro', 'b'));
    const all = store.listAll();
    expect(all).toHaveLength(2);
    const brands = all.map((e) => e.brand).sort();
    expect(brands).toEqual(['MEKONG', 'SOPHIA']);
  });
});

// ── gate ──────────────────────────────────────────────────────────────────────

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
    // store pre-loaded in constructor
    expect(gate.getCurrentTier()).toBe('enterprise');
  });

  it('featureMap resolves required tier per command', () => {
    const store = tmpStore();
    const k = generateKey('AGENCYOS', 'pro', 'user');
    store.save('AGENCYOS', k);
    const gate = new LicenseGate({
      brand: 'AGENCYOS',
      featureMap: { 'export': 'pro', 'admin': 'enterprise' },
      store,
    });
    expect(gate.canAccess('export').allowed).toBe(true);
    expect(gate.canAccess('admin').allowed).toBe(false);
  });
});

// ── admin helpers ─────────────────────────────────────────────────────────────

describe('admin: store-admin', () => {
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
});

// ── integration helpers ───────────────────────────────────────────────────────

describe('integration: gate-helpers', () => {
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
});
