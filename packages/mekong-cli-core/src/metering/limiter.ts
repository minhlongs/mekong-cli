/**
 * UsageLimiter — enforce tier quotas in real-time.
 * Daily limits reset at midnight UTC.
 * Enterprise tier (-1 quotas) = unlimited.
 */
import { MeteringStore } from './store.js';
import { UsageAnalyzer } from './analyzer.js';
import type { UsageCategory, LimitCheckResult } from './types.js';
import type { LicenseTier } from '../license/types.js';
import { TIER_QUOTAS } from '../license/types.js';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';

export class UsageLimiter {
  private analyzer = new UsageAnalyzer();
  /** Cache today's counts to avoid re-reading disk on every check */
  private cache: { date: string; llmCalls: number; toolRuns: number; sopRuns: number } | null = null;

  constructor(private readonly store: MeteringStore) {}

  /**
   * Check if an operation is allowed under the tier quota.
   * Returns Result<LimitCheckResult>:
   *   ok(result) where result.allowed === false means "blocked but no internal error"
   */
  async checkLimit(category: UsageCategory, tier: LicenseTier): Promise<Result<LimitCheckResult, Error>> {
    try {
      const quota = TIER_QUOTAS[tier];
      const limit = this.limitForCategory(category, quota);

      if (limit === -1) {
        // Enterprise = unlimited
        return ok({ allowed: true, category, remaining: Infinity, limit: -1, used: 0 });
      }

      const used = await this.getUsedToday(category);
      const remaining = Math.max(0, limit - used);
      const allowed = used < limit;

      const result: LimitCheckResult = {
        allowed,
        category,
        remaining,
        limit,
        used,
        message: allowed
          ? undefined
          : `Daily limit reached: ${used}/${limit} ${category.replace('_', ' ')}s used today`,
      };
      return ok(result);
    } catch (e) {
      return err(new Error(`UsageLimiter.checkLimit failed: ${String(e)}`));
    }
  }

  /** Get remaining quota for a category today */
  async getRemaining(category: UsageCategory, tier: LicenseTier): Promise<number> {
    const quota = TIER_QUOTAS[tier];
    const limit = this.limitForCategory(category, quota);
    if (limit === -1) return Infinity;
    const used = await this.getUsedToday(category);
    return Math.max(0, limit - used);
  }

  /** Invalidate the daily cache (call after recording events) */
  invalidateCache(): void {
    this.cache = null;
  }

  /** Force-refresh the cache from disk */
  async refreshCache(): Promise<void> {
    this.cache = null;
    await this.buildCache();
  }

  private async getUsedToday(category: UsageCategory): Promise<number> {
    await this.ensureCache();
    if (!this.cache) return 0;
    switch (category) {
      case 'llm_call': return this.cache.llmCalls;
      case 'tool_run': return this.cache.toolRuns;
      case 'sop_run': return this.cache.sopRuns;
    }
  }

  private async ensureCache(): Promise<void> {
    const today = new Date().toISOString().slice(0, 10);
    if (this.cache?.date === today) return;
    await this.buildCache();
  }

  private async buildCache(): Promise<void> {
    const today = new Date().toISOString().slice(0, 10);
    const result = await this.store.readToday();
    if (!result.ok) {
      this.cache = { date: today, llmCalls: 0, toolRuns: 0, sopRuns: 0 };
      return;
    }
    const reading = this.analyzer.todayReading(result.value);
    this.cache = {
      date: today,
      llmCalls: reading.llmCalls,
      toolRuns: reading.toolRuns,
      sopRuns: reading.sopRuns,
    };
  }

  private limitForCategory(category: UsageCategory, quota: import('../license/types.js').UsageQuota): number {
    switch (category) {
      case 'llm_call': return quota.llmCallsPerDay;
      case 'tool_run': return quota.toolRunsPerDay;
      case 'sop_run': return quota.sopRunsPerDay;
    }
  }
}
