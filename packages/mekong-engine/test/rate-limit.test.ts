import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { TIER_LIMITS, getRateLimitConfig, getRetryAfterSeconds, getWindowKey } from '../src/lib/tenant-limits'
import type { TenantTier } from '../src/lib/tenant-limits'

describe('tenant-limits', () => {
  describe('TIER_LIMITS', () => {
    it('defines correct limits for free tier', () => {
      expect(TIER_LIMITS.free.requestsPerHour).toBe(50)
      expect(TIER_LIMITS.free.requestsPerDay).toBe(500)
    })

    it('defines correct limits for starter tier', () => {
      expect(TIER_LIMITS.starter.requestsPerHour).toBe(100)
      expect(TIER_LIMITS.starter.requestsPerDay).toBe(2000)
    })

    it('defines correct limits for pro tier', () => {
      expect(TIER_LIMITS.pro.requestsPerHour).toBe(500)
      expect(TIER_LIMITS.pro.requestsPerDay).toBe(10000)
    })

    it('defines correct limits for enterprise tier', () => {
      expect(TIER_LIMITS.enterprise.requestsPerHour).toBe(2000)
      expect(TIER_LIMITS.enterprise.requestsPerDay).toBe(50000)
    })

    it('has increasing limits across tiers', () => {
      const tiers: TenantTier[] = ['free', 'starter', 'pro', 'enterprise']
      for (let i = 1; i < tiers.length; i++) {
        expect(TIER_LIMITS[tiers[i]].requestsPerHour)
          .toBeGreaterThan(TIER_LIMITS[tiers[i - 1]].requestsPerHour)
        expect(TIER_LIMITS[tiers[i]].requestsPerDay)
          .toBeGreaterThan(TIER_LIMITS[tiers[i - 1]].requestsPerDay)
      }
    })
  })

  describe('getRateLimitConfig', () => {
    it('returns correct config for each tier', () => {
      expect(getRateLimitConfig('free')).toEqual(TIER_LIMITS.free)
      expect(getRateLimitConfig('starter')).toEqual(TIER_LIMITS.starter)
      expect(getRateLimitConfig('pro')).toEqual(TIER_LIMITS.pro)
      expect(getRateLimitConfig('enterprise')).toEqual(TIER_LIMITS.enterprise)
    })
  })

  describe('getRetryAfterSeconds', () => {
    it('returns 3600 for hour window', () => {
      expect(getRetryAfterSeconds('hour')).toBe(3600)
    })

    it('returns 86400 for day window', () => {
      expect(getRetryAfterSeconds('day')).toBe(86400)
    })
  })

  describe('getWindowKey', () => {
    beforeEach(() => {
      // Mock Date to have predictable UTC values
      vi.useFakeTimers()
      vi.setSystemTime(new Date('2024-01-15T10:30:00Z'))
    })

    afterEach(() => {
      vi.useRealTimers()
    })

    it('generates hour key with current hour', () => {
      const key = getWindowKey('tenant-123', 'hour')
      // Date is set to 10:30 UTC, so hour is 10
      expect(key).toBe('rate:tenant-123:hour:10')
    })

    it('generates day key with current date', () => {
      const key = getWindowKey('tenant-123', 'day')
      // Date is set to Jan 15, so date is 15
      expect(key).toBe('rate:tenant-123:day:15')
    })

    it('uses different keys for different tenants', () => {
      const key1 = getWindowKey('tenant-1', 'hour')
      const key2 = getWindowKey('tenant-2', 'hour')
      expect(key1).not.toBe(key2)
    })
  })
})
