/**
 * coverage-gaps.test.ts — tests for untested paths in license, payments,
 * metering, and analytics modules.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdtemp, rm, writeFile, mkdir } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { randomUUID } from 'node:crypto';

// ─── LicenseStore error path ──────────────────────────────────────────────────

describe('LicenseStore — error paths', () => {
  it('load returns err when file contains invalid JSON', async () => {
    const { LicenseStore } = await import('../license/store.js');
    const dir = await mkdtemp(join(tmpdir(), 'lstore-'));
    const path = join(dir, 'bad.json');
    await writeFile(path, 'NOT JSON', 'utf-8');
    const store = new LicenseStore(path);
    const result = await store.load();
    expect(result.ok).toBe(false);
    await rm(dir, { recursive: true, force: true });
  });

  it('save returns err when path is a directory (not writable as file)', async () => {
    const { LicenseStore } = await import('../license/store.js');
    const dir = await mkdtemp(join(tmpdir(), 'lstore-'));
    // Use the dir itself as the file path — write will fail
    const store = new LicenseStore(dir);
    const { computeSignature } = await import('../license/verifier.js');
    const partial = {
      key: 'RAAS-ERR-001', tier: 'free' as const, status: 'active' as const,
      issuedAt: new Date().toISOString(), expiresAt: new Date(Date.now() + 86400000).toISOString(), owner: 'x',
    };
    const lic = { ...partial, signature: computeSignature(partial) };
    const result = await store.save(lic);
    expect(result.ok).toBe(false);
    await rm(dir, { recursive: true, force: true });
  });
});

// ─── RemoteLicenseClient — network mocking ────────────────────────────────────

describe('RemoteLicenseClient — validate paths', () => {
  it('falls back to cache when network fails and cache matches key', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'remote-'));
    const cachePath = join(dir, 'cache.json');
    const { computeSignature } = await import('../license/verifier.js');
    const partial = {
      key: 'RAAS-CACHE-001', tier: 'pro' as const, status: 'active' as const,
      issuedAt: new Date().toISOString(), expiresAt: new Date(Date.now() + 86400000).toISOString(), owner: 'test',
    };
    const lic = { ...partial, signature: computeSignature(partial) };
    // Pre-populate cache
    const entry = { license: lic, fetchedAt: Date.now() };
    await writeFile(cachePath, JSON.stringify(entry), 'utf-8');

    const { RemoteLicenseClient } = await import('../license/remote.js');
    const client = new RemoteLicenseClient('http://localhost:1', cachePath);
    // fetch will fail (connection refused) → should fall back to cache
    const result = await client.validate('RAAS-CACHE-001');
    expect(result.ok).toBe(true);
    if (result.ok) expect(result.value.key).toBe('RAAS-CACHE-001');
    await rm(dir, { recursive: true, force: true });
  });

  it('returns err when network fails and no cache exists', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'remote-'));
    const { RemoteLicenseClient } = await import('../license/remote.js');
    const client = new RemoteLicenseClient('http://localhost:1', join(dir, 'no-cache.json'));
    const result = await client.validate('RAAS-NOCACHE-001');
    expect(result.ok).toBe(false);
    await rm(dir, { recursive: true, force: true });
  });

  it('returns err when cache exists but key does not match', async () => {
    const dir = await mkdtemp(join(tmpdir(), 'remote-'));
    const cachePath = join(dir, 'cache.json');
    const { computeSignature } = await import('../license/verifier.js');
    const partial = {
      key: 'RAAS-OTHER-001', tier: 'pro' as const, status: 'active' as const,
      issuedAt: new Date().toISOString(), expiresAt: new Date(Date.now() + 86400000).toISOString(), owner: 'test',
    };
    const lic = { ...partial, signature: computeSignature(partial) };
    await writeFile(cachePath, JSON.stringify({ license: lic, fetchedAt: Date.now() }), 'utf-8');
    const { RemoteLicenseClient } = await import('../license/remote.js');
    const client = new RemoteLicenseClient('http://localhost:1', cachePath);
    const result = await client.validate('RAAS-DIFFERENT-KEY');
    expect(result.ok).toBe(false);
    await rm(dir, { recursive: true, force: true });
  });
});

// ─── PolarClient — retry and error paths ──────────────────────────────────────

describe('PolarClient — createPolarClientFromEnv', () => {
  afterEach(() => { delete process.env['POLAR_API_KEY']; });

  it('returns err when POLAR_API_KEY not set', async () => {
    delete process.env['POLAR_API_KEY'];
    const { createPolarClientFromEnv } = await import('../payments/polar-client.js');
    const result = createPolarClientFromEnv();
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.error.message).toContain('POLAR_API_KEY');
  });

  it('returns ok(PolarClient) when POLAR_API_KEY set', async () => {
    process.env['POLAR_API_KEY'] = 'test-key-123';
    const { createPolarClientFromEnv } = await import('../payments/polar-client.js');
    const result = createPolarClientFromEnv();
    expect(result.ok).toBe(true);
  });
});

describe('PolarClient — HTTP errors', () => {
  it('returns err on non-ok response', async () => {
    const { PolarClient } = await import('../payments/polar-client.js');
    const client = new PolarClient({
      apiKey: 'test', baseUrl: 'http://localhost:1', timeoutMs: 500, maxRetries: 0,
    });
    const result = await client.listProducts();
    expect(result.ok).toBe(false);
  });

  it('returns err when subscription check fails', async () => {
    const { PolarClient } = await import('../payments/polar-client.js');
    const client = new PolarClient({
      apiKey: 'test', baseUrl: 'http://localhost:1', timeoutMs: 500, maxRetries: 0,
    });
    const result = await client.checkSubscription('cust_123');
    expect(result.ok).toBe(false);
  });

  it('returns err when getSubscription fails', async () => {
    const { PolarClient } = await import('../payments/polar-client.js');
    const client = new PolarClient({
      apiKey: 'test', baseUrl: 'http://localhost:1', timeoutMs: 500, maxRetries: 0,
    });
    const result = await client.getSubscription('sub_123');
    expect(result.ok).toBe(false);
  });
});

// ─── ReportGenerator — markdown and CLI output ────────────────────────────────

describe('ReportGenerator — toMarkdown', () => {
  function makeBundle() {
    const period = { label: '2026-03', startDate: '2026-03-01T00:00:00Z', endDate: '2026-03-31T23:59:59Z' };
    return {
      roi: {
        roiPercent: 42.5, timeSavedHours: 8, hourlyRate: 100, timeSavedValue: 800,
        revenueGenerated: 500, totalCost: 0.025, netValue: 1300, period,
        computedAt: new Date().toISOString(),
      },
      agents: [{
        agentName: 'CookAgent', agiScore: 85, phaseProgressScore: 90, activityScore: 80,
        successRateScore: 85, resilienceScore: 75, totalExecutions: 20,
        successfulExecutions: 17, failedExecutions: 2, successRate: 0.85,
        errorRecoveryRate: 0.5, recentCommits: 10, phasesCompleted: 8,
        totalPhases: 10, computedAt: new Date().toISOString(),
      }],
      revenue: {
        period, mrr: 1200, arr: 14400, arpu: 150, activeCustomers: 8,
        totalRevenue: 1200, tierDistribution: { free: 2, starter: 3, pro: 2, enterprise: 1 },
        computedAt: new Date().toISOString(),
      },
      growth: {
        period, momGrowthPercent: 12.5, wowGrowthPercent: 3.1, churnRate: 0.02,
        expansionRevenue: 100, nrrPercent: 110, newCustomers: 2, churnedCustomers: 1,
        computedAt: new Date().toISOString(),
      },
    };
  }

  it('toMarkdown contains ROI Summary heading', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const md = gen.toMarkdown(makeBundle());
    expect(md).toContain('## ROI Summary');
    expect(md).toContain('+42.5%');
  });

  it('toMarkdown contains Agent Leaderboard', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const md = gen.toMarkdown(makeBundle());
    expect(md).toContain('CookAgent');
    expect(md).toContain('## Agent Leaderboard');
  });

  it('toMarkdown contains Revenue Breakdown and tier distribution', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const md = gen.toMarkdown(makeBundle());
    expect(md).toContain('## Revenue Breakdown');
    expect(md).toContain('Starter');
  });

  it('toMarkdown shows negative ROI with minus sign', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const bundle = makeBundle();
    bundle.roi.roiPercent = -15.3;
    const md = gen.toMarkdown(bundle);
    expect(md).toContain('-15.3%');
  });

  it('toCliSummary returns non-empty string', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const summary = gen.toCliSummary(makeBundle());
    expect(summary.length).toBeGreaterThan(50);
    expect(summary).toContain('ROI');
  });

  it('agentSection with empty agents shows no-data message', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const result = gen.agentSection([]);
    expect(result).toContain('no data');
  });

  it('roiSection formats negative ROI without leading plus', async () => {
    const { ReportGenerator } = await import('../analytics/report-generator.js');
    const gen = new ReportGenerator();
    const period = { label: '2026-03', startDate: '', endDate: '' };
    const roi = {
      roiPercent: -5, timeSavedHours: 2, hourlyRate: 50,
      timeSavedValue: 100, revenueGenerated: 0, totalCost: 0.5,
      netValue: -0.5, period, computedAt: '',
    };
    const out = gen.roiSection(roi);
    expect(out).not.toMatch(/\+\-/);
    expect(out).toContain('-5.0%');
  });
});

// ─── feature-map edge cases ───────────────────────────────────────────────────

describe('getRequiredTier — edge cases', () => {
  it('returns free for empty string command', async () => {
    const { getRequiredTier } = await import('../license/feature-map.js');
    expect(getRequiredTier('')).toBe('free');
  });

  it('returns free for command with special chars', async () => {
    const { getRequiredTier } = await import('../license/feature-map.js');
    expect(getRequiredTier('some-completely-unknown-cmd-xyz')).toBe('free');
  });

  it('all FEATURE_MAP entries are retrievable by getRequiredTier', async () => {
    const { getRequiredTier, FEATURE_MAP } = await import('../license/feature-map.js');
    for (const entry of FEATURE_MAP) {
      expect(getRequiredTier(entry.command)).toBe(entry.minTier);
    }
  });
});
