import { describe, it, expect, vi, beforeEach } from 'vitest'
import { rateLimitMiddleware } from '../src/middleware/rate-limit'
import type { Tenant } from '../src/types/raas'
import { createMockContext, createMockKV, defaultTenant } from './rate-limit-middleware.test'

describe('rateLimitMiddleware — daily limits, headers, errors & tiers', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 429 when daily limit exceeded', async () => {
    const mockKV = createMockKV()
    const now = new Date('2024-01-15T10:30:00Z')
    vi.useFakeTimers()
    vi.setSystemTime(now)

    const hourWindowStart = Math.floor(now.getTime() / 3600000) * 3600000
    const hourTimestamp = Math.floor(hourWindowStart / 3600000)
    const hourKey = `rate:tenant-123:hour:${hourTimestamp}`

    const dayWindowStart = Math.floor(now.getTime() / 86400000) * 86400000
    const dayTimestamp = Math.floor(dayWindowStart / 86400000)
    const dayKey = `rate:tenant-123:day:${dayTimestamp}`

    await mockKV.put(hourKey, JSON.stringify({ count: 10, windowStart: hourWindowStart }))
    await mockKV.put(dayKey, JSON.stringify({ count: 500, windowStart: dayWindowStart }))

    const ctx = createMockContext({ tenant: defaultTenant, kv: mockKV })
    const middleware = rateLimitMiddleware()
    await middleware(ctx, ctx.next)

    expect(ctx.status).toBe(429)
    expect(ctx.jsonBody).toEqual({
      error: 'Rate limit exceeded',
      code: 'RATE_LIMIT_EXCEEDED',
      retry_after: 86400,
      limit: 500,
      remaining: 0,
      reset: Math.ceil((dayWindowStart + 86400000) / 1000),
    })

    vi.useRealTimers()
  })

  it('allows higher limits for pro tier', async () => {
    const mockKV = createMockKV()
    const proTenant: Tenant = { ...defaultTenant, tier: 'pro' }
    const ctx = createMockContext({ tenant: proTenant, kv: mockKV })
    const middleware = rateLimitMiddleware()

    await middleware(ctx, ctx.next)
    expect(ctx.next).toHaveBeenCalled()
  })

  it('sets rate limit headers on response', async () => {
    const mockKV = createMockKV()
    const ctx = createMockContext({ tenant: defaultTenant, kv: mockKV })
    const middleware = rateLimitMiddleware()

    await middleware(ctx, ctx.next)

    expect(ctx.header).toHaveBeenCalledWith('X-RateLimit-Limit', expect.any(String))
    expect(ctx.header).toHaveBeenCalledWith('X-RateLimit-Remaining', expect.any(String))
    expect(ctx.header).toHaveBeenCalledWith('X-RateLimit-Reset', expect.any(String))
  })

  it('handles KV errors gracefully (fail-open)', async () => {
    const errorKV = {
      get: vi.fn().mockRejectedValue(new Error('KV unavailable')),
      put: vi.fn().mockRejectedValue(new Error('KV unavailable')),
    }

    const ctx = createMockContext({ tenant: defaultTenant, kv: errorKV })
    const middleware = rateLimitMiddleware()

    await expect(middleware(ctx, ctx.next)).resolves.not.toThrow()
    expect(ctx.next).toHaveBeenCalled()
  })

  it('respects different tier limits', async () => {
    const tiers: Array<{ tier: Tenant['tier'] | 'starter'; expectedHourly: number }> = [
      { tier: 'free', expectedHourly: 50 },
      { tier: 'starter', expectedHourly: 100 },
      { tier: 'pro', expectedHourly: 500 },
      { tier: 'enterprise', expectedHourly: 2000 },
    ]

    for (const { tier } of tiers) {
      const mockKV = createMockKV()
      const tenant = { ...defaultTenant, tier } as unknown as Tenant

      const ctx = createMockContext({ tenant, kv: mockKV })
      const middleware = rateLimitMiddleware()

      await middleware(ctx, ctx.next)
      expect(ctx.next).toHaveBeenCalled()
      mockKV._clear?.()
      vi.clearAllMocks()
    }
  })
})
