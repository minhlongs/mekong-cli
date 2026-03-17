/**
 * roiaas-delegation.test.ts — Full-chain RaaS delegation tests
 * Tests: Gateway delegation, RaaS pricing, license validation, API handlers
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { Gateway, ROIAAS_LEVELS } from './gateway.js';
import type { RoiaasLevel } from './gateway.js';

// Note: We import from openclaw-engine's raas module
// In a real monorepo these would be workspace deps, but for the test
// we use relative paths since both packages are in the same repo
import {
  TIER_CONFIGS,
  hasCreditsRemaining,
  calculateMonthlyCost,
  getOverageCredits,
} from '../../../openclaw-engine/src/raas/raas-pricing.js';
import type { RaasTier, UsageRecord } from '../../../openclaw-engine/src/raas/raas-pricing.js';

import {
  registerTenant,
  getTenant,
  validateAndMeter,
  resetTenantUsage,
} from '../../../openclaw-engine/src/raas/raas-gateway.js';

import {
  handleValidate,
  handleGetBalance,
  handleRegisterTenant,
  handleListTiers,
} from '../../../openclaw-engine/src/raas/raas-api.js';

import {
  handleOnboardTenant,
  validateApiKey,
  revokeApiKey,
  listTenantApiKeys,
} from '../../../openclaw-engine/src/raas/raas-onboarding.js';

// --- Gateway Delegation Tests ---
describe('Gateway ROIaaS Delegation', () => {
  let gateway: Gateway;
  const mockEngine = { run: async (input: string) => `executed: ${input}` } as any;

  beforeEach(() => {
    gateway = new Gateway(mockEngine);
  });

  it('should define all 5 ROIaaS levels', () => {
    const levels: RoiaasLevel[] = ['studio', 'cto', 'pm', 'dev', 'worker'];
    for (const level of levels) {
      expect(ROIAAS_LEVELS[level]).toBeDefined();
    }
  });

  it('should cascade studio → cto → pm → dev → worker → null', () => {
    expect(gateway.getCascadeTarget('studio')).toBe('cto');
    expect(gateway.getCascadeTarget('cto')).toBe('pm');
    expect(gateway.getCascadeTarget('pm')).toBe('dev');
    expect(gateway.getCascadeTarget('dev')).toBe('worker');
    expect(gateway.getCascadeTarget('worker')).toBeNull();
  });

  it('should dispatch registered route', async () => {
    gateway.route('studio:audit', async () => 'audit-result');
    const result = await gateway.dispatch('studio:audit');
    expect(result).toBe('audit-result');
  });

  it('should fall back to engine.run for unregistered commands', async () => {
    const result = await gateway.dispatch('unknown:cmd', ['arg1']);
    expect(result).toBe('executed: unknown:cmd arg1');
  });

  it('should delegate down from studio to cto', async () => {
    gateway.route('cto:review', async () => 'review-done');
    const result = await gateway.delegateDown('studio', 'cto:review');
    expect(result).toBe('review-done');
  });

  it('should reject delegation to wrong level', async () => {
    await expect(gateway.delegateDown('studio', 'dev:feature')).rejects.toThrow(
      'can only delegate to "cto"'
    );
  });

  it('should reject delegation from atomic level', async () => {
    await expect(gateway.delegateDown('worker', 'worker:code')).rejects.toThrow(
      'cannot delegate further'
    );
  });

  it('should parse namespaced commands', () => {
    expect(gateway.parseCommand('studio:audit')).toEqual({ level: 'studio', command: 'studio:audit' });
    expect(gateway.parseCommand('plain-cmd')).toEqual({ level: null, command: 'plain-cmd' });
  });

  it('should list routes by level', () => {
    gateway.route('dev:feature', async () => 'ok');
    gateway.route('dev:fix', async () => 'ok');
    gateway.route('pm:plan', async () => 'ok');
    expect(gateway.listRoutesByLevel('dev')).toEqual(['dev:feature', 'dev:fix']);
    expect(gateway.listRoutesByLevel('pm')).toEqual(['pm:plan']);
  });
});

// --- RaaS Pricing Tests ---
describe('RaaS Pricing', () => {
  it('should define 3 tiers', () => {
    expect(Object.keys(TIER_CONFIGS)).toEqual(['starter', 'pro', 'enterprise']);
  });

  it('starter: 200 credits at $49', () => {
    expect(TIER_CONFIGS.starter.creditsPerMonth).toBe(200);
    expect(TIER_CONFIGS.starter.priceUsd).toBe(49);
  });

  it('enterprise: unlimited credits', () => {
    expect(TIER_CONFIGS.enterprise.creditsPerMonth).toBe(-1);
    expect(hasCreditsRemaining('enterprise', 999999)).toBe(true);
  });

  it('should calculate monthly cost from usage records', () => {
    const records: UsageRecord[] = [
      { tenantId: 't1', command: 'dev:feature', creditsCost: 8, timestamp: 1, success: true },
      { tenantId: 't1', command: 'dev:fix', creditsCost: 3, timestamp: 2, success: true },
      { tenantId: 't1', command: 'dev:test', creditsCost: 3, timestamp: 3, success: false }, // failed, not counted
    ];
    expect(calculateMonthlyCost(records)).toBe(11);
  });

  it('should detect credit exhaustion', () => {
    expect(hasCreditsRemaining('starter', 199)).toBe(true);
    expect(hasCreditsRemaining('starter', 200)).toBe(false);
  });

  it('should calculate overage', () => {
    expect(getOverageCredits('starter', 250)).toBe(50);
    expect(getOverageCredits('enterprise', 99999)).toBe(0);
  });
});

// --- RaaS Gateway (License + Metering) Tests ---
describe('RaaS Gateway - License Validation', () => {
  beforeEach(() => {
    // Register a fresh test tenant
    registerTenant({
      tenantId: 'test-tenant',
      tier: 'pro',
      active: true,
      expiresAt: Date.now() + 86400000, // 1 day from now
      usedCredits: 0,
    });
  });

  it('should validate and deduct credits', () => {
    const result = validateAndMeter('test-tenant', 5);
    expect(result.allowed).toBe(true);
    expect(result.remainingCredits).toBe(995); // 1000 - 5
  });

  it('should reject unknown tenant', () => {
    const result = validateAndMeter('ghost', 1);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('not found');
  });

  it('should reject inactive license', () => {
    registerTenant({ tenantId: 'inactive', tier: 'starter', active: false, expiresAt: 0, usedCredits: 0 });
    const result = validateAndMeter('inactive', 1);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('inactive');
  });

  it('should reject expired license', () => {
    registerTenant({ tenantId: 'expired', tier: 'starter', active: true, expiresAt: 1, usedCredits: 0 });
    const result = validateAndMeter('expired', 1);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('expired');
  });

  it('should reject when credits exhausted', () => {
    registerTenant({ tenantId: 'broke', tier: 'starter', active: true, expiresAt: Date.now() + 86400000, usedCredits: 200 });
    const result = validateAndMeter('broke', 1);
    expect(result.allowed).toBe(false);
    expect(result.reason).toContain('Credit limit');
  });

  it('should reset tenant usage', () => {
    validateAndMeter('test-tenant', 100);
    expect(getTenant('test-tenant')?.usedCredits).toBe(100);
    resetTenantUsage('test-tenant');
    expect(getTenant('test-tenant')?.usedCredits).toBe(0);
  });
});

// --- RaaS API Handler Tests ---
describe('RaaS API Handlers', () => {
  beforeEach(() => {
    registerTenant({
      tenantId: 'api-tenant',
      tier: 'pro',
      active: true,
      expiresAt: Date.now() + 86400000,
      usedCredits: 0,
    });
  });

  it('handleValidate — success', () => {
    const res = handleValidate('api-tenant', 'dev:feature', 8);
    expect(res.ok).toBe(true);
    expect(res.status).toBe(200);
  });

  it('handleValidate — 402 on exhausted credits', () => {
    registerTenant({ tenantId: 'empty', tier: 'starter', active: true, expiresAt: Date.now() + 86400000, usedCredits: 200 });
    const res = handleValidate('empty', 'dev:feature', 8);
    expect(res.ok).toBe(false);
    expect(res.status).toBe(402);
  });

  it('handleGetBalance — returns tier info', () => {
    const res = handleGetBalance('api-tenant');
    expect(res.ok).toBe(true);
    expect(res.data?.tier).toBe('pro');
    expect(res.data?.limit).toBe(1000);
  });

  it('handleRegisterTenant — creates tenant', () => {
    const res = handleRegisterTenant({ tenantId: 'new-t', tier: 'starter', active: true, expiresAt: 0, usedCredits: 0 });
    expect(res.ok).toBe(true);
    expect(res.status).toBe(201);
  });

  it('handleRegisterTenant — rejects invalid tier', () => {
    const res = handleRegisterTenant({ tenantId: 'bad', tier: 'mega' as any, active: true, expiresAt: 0, usedCredits: 0 });
    expect(res.ok).toBe(false);
    expect(res.status).toBe(400);
  });

  it('handleListTiers — returns all tiers', () => {
    const res = handleListTiers();
    expect(res.ok).toBe(true);
    expect(Object.keys(res.data!)).toEqual(['starter', 'pro', 'enterprise']);
  });
});

// --- RaaS Onboarding Tests ---
describe('RaaS Onboarding', () => {
  it('handleOnboardTenant — full onboarding flow', () => {
    const res = handleOnboardTenant({
      tenantId: 'onboard-test-1',
      tier: 'pro',
      email: 'test@example.com',
    });
    expect(res.ok).toBe(true);
    expect(res.status).toBe(201);
    expect(res.data?.apiKey).toMatch(/^mk_/);
    expect(res.data?.creditsPerMonth).toBe(1000);
  });

  it('handleOnboardTenant — rejects duplicate tenant', () => {
    handleOnboardTenant({ tenantId: 'dup-tenant', tier: 'starter', email: 'a@b.com' });
    const res = handleOnboardTenant({ tenantId: 'dup-tenant', tier: 'starter', email: 'a@b.com' });
    expect(res.ok).toBe(false);
    expect(res.status).toBe(409);
  });

  it('handleOnboardTenant — rejects invalid tier', () => {
    const res = handleOnboardTenant({ tenantId: 'bad-tier', tier: 'mega' as any, email: 'a@b.com' });
    expect(res.ok).toBe(false);
    expect(res.status).toBe(400);
  });

  it('handleOnboardTenant — rejects missing email', () => {
    const res = handleOnboardTenant({ tenantId: 'no-email', tier: 'starter', email: '' });
    expect(res.ok).toBe(false);
    expect(res.status).toBe(400);
  });

  it('validateApiKey — validates generated key', () => {
    const onboard = handleOnboardTenant({ tenantId: 'key-test-1', tier: 'pro', email: 'k@t.com' });
    const res = validateApiKey(onboard.data!.apiKey);
    expect(res.ok).toBe(true);
    expect(res.data?.tenantId).toBe('key-test-1');
    expect(res.data?.tier).toBe('pro');
  });

  it('validateApiKey — rejects invalid key', () => {
    const res = validateApiKey('mk_invalid_key');
    expect(res.ok).toBe(false);
    expect(res.status).toBe(401);
  });

  it('revokeApiKey — revokes and blocks subsequent validation', () => {
    const onboard = handleOnboardTenant({ tenantId: 'revoke-test', tier: 'starter', email: 'r@t.com' });
    const revoke = revokeApiKey(onboard.data!.apiKey);
    expect(revoke.ok).toBe(true);

    const validate = validateApiKey(onboard.data!.apiKey);
    expect(validate.ok).toBe(false);
    expect(validate.status).toBe(403);
  });

  it('listTenantApiKeys — lists keys for tenant', () => {
    const onboard = handleOnboardTenant({ tenantId: 'list-keys-test', tier: 'pro', email: 'l@t.com' });
    const res = listTenantApiKeys('list-keys-test');
    expect(res.ok).toBe(true);
    expect(res.data!.length).toBe(1);
    expect(res.data![0].apiKey).toBe(onboard.data!.apiKey);
  });
});
