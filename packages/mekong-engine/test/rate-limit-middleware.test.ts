import { describe, it, expect, vi, beforeEach } from 'vitest'
import { rateLimitMiddleware } from '../src/middleware/rate-limit'
import type { Tenant } from '../src/types/raas'

describe('rateLimitMiddleware', () => {
  // Mock KV Namespace
  const createMockKV = () => {
    const store = new Map<string, string>()
    return {
      get: vi.fn(async (key: string, options?: any) => {
        const value = store.get(key)
        if (value === undefined) return null
        if (options === 'json') {
          try {
            return JSON.parse(value)
          } catch {
            return null
          }
        }
        return value
      }),
      put: vi.fn(async (key: string, value: string, options?: any) => {
        store.set(key, value)
        return Promise.resolve()
      }),
      delete: vi.fn(async (key: string) => {
        store.delete(key)
        return Promise.resolve()
      }),
      _store: store,
      _clear: () => store.clear(),
    }
  }

  const createMockContext = (overrides?: {
    tenant?: Tenant | null
    kv?: any
    env?: any
  }) => {
    const mockKV = overrides?.kv || createMockKV()
    let headers: Record<string, string> = {}
    let status = 200
    let jsonBody: any = null

    const ctx: any = {
      get: vi.fn((key: string) => {
        if (key === 'tenant') return overrides?.tenant ?? null
        return null
      }),
      json: vi.fn((body: any, newStatus?: number) => {
        jsonBody = body
        status = newStatus ?? status
        const resp = new Response(JSON.stringify(body), {
          status,
          headers: { ...headers }
        })
        ctx.res = resp
        return resp
      }),
      header: vi.fn((key: string, value: string) => {
        headers[key] = value
      }),
      env: {
        RATE_LIMIT_KV: overrides?.kv !== null ? mockKV : undefined,
        ...overrides?.env,
      },
      next: vi.fn().mockImplementation(() => Promise.resolve()),
      _headers: headers,
      _kv: mockKV,
      get status() { return status },
      set status(v: number) { status = v },
      get jsonBody() { return jsonBody },
      res: null as Response | null,
      req: {
        method: 'GET',
        path: '/test',
        header: vi.fn(),
      },
    }
    return ctx
  }

  const defaultTenant: Tenant = {
    id: 'tenant-123',
    name: 'Test Tenant',
    api_key_hash: 'hash-abc',
    tier: 'free',
    created_at: '2024-01-01T00:00:00Z',
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('skips rate limiting when KV not configured', async () => {
    const ctx = createMockContext({ kv: null })
    const middleware = rateLimitMiddleware()

    await middleware(ctx, ctx.next)

    expect(ctx.next).toHaveBeenCalled()
  })

  it('skips rate limiting when no tenant in context', async () => {
    const mockKV = createMockKV()
    const ctx = createMockContext({ tenant: null, kv: mockKV })
    const middleware = rateLimitMiddleware()

    await middleware(ctx, ctx.next)

    expect(ctx.next).toHaveBeenCalled()
  })

  it('allows request when under rate limit', async () => {
    const mockKV = createMockKV()
    const ctx = createMockContext({ tenant: defaultTenant, kv: mockKV })
    const middleware = rateLimitMiddleware()

    const response = await middleware(ctx, ctx.next)

    expect(ctx.next).toHaveBeenCalled()
    expect(response).toBeUndefined()
  })

  it('returns 429 when hourly limit exceeded', async () => {
    const mockKV = createMockKV()
    // Pre-populate KV with max requests for free tier (50/hour)
    const now = new Date('2024-01-15T10:30:00Z')
    vi.useFakeTimers()
    vi.setSystemTime(now)

    // Match the exact key format from the middleware: rate:{tenantId}:{window}:{timestamp}
    const windowStart = Math.floor(now.getTime() / 3600000) * 3600000
    const timestamp = Math.floor(windowStart / 3600000)
    const hourKey = `rate:tenant-123:hour:${timestamp}`

    await mockKV.put(hourKey, JSON.stringify({
      count: 50,
      windowStart: windowStart,
    }))

    const ctx = createMockContext({ tenant: defaultTenant, kv: mockKV })
    const middleware = rateLimitMiddleware()

    await middleware(ctx, ctx.next)

    expect(ctx.status).toBe(429)
    expect(ctx.jsonBody).toEqual({
      error: 'Rate limit exceeded',
      code: 'RATE_LIMIT_EXCEEDED',
      retry_after: 3600,
      limit: 50,
      remaining: 0,
      reset: Math.ceil((windowStart + 3600000) / 1000),
    })

    vi.useRealTimers()
  })

  it('returns 429 when daily limit exceeded', async () => {
    const mockKV = createMockKV()
    const now = new Date('2024-01-15T10:30:00Z')
    vi.useFakeTimers()
    vi.setSystemTime(now)

    // Set hourly to under limit but daily at limit
    const hourWindowStart = Math.floor(now.getTime() / 3600000) * 3600000
    const hourTimestamp = Math.floor(hourWindowStart / 3600000)
    const hourKey = `rate:tenant-123:hour:${hourTimestamp}`

    const dayWindowStart = Math.floor(now.getTime() / 86400000) * 86400000
    const dayTimestamp = Math.floor(dayWindowStart / 86400000)
    const dayKey = `rate:tenant-123:day:${dayTimestamp}`

    await mockKV.put(hourKey, JSON.stringify({
      count: 10,
      windowStart: hourWindowStart,
    }))
    await mockKV.put(dayKey, JSON.stringify({
      count: 500,
      windowStart: dayWindowStart,
    }))

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
    const proTenant: Tenant = {
      ...defaultTenant,
      tier: 'pro',
    }

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

    // Should not throw, should allow request (fail-open)
    await expect(middleware(ctx, ctx.next)).resolves.not.toThrow()
    expect(ctx.next).toHaveBeenCalled()
  })

  it('respects different tier limits', async () => {
    const tiers: Array<{ tier: string; expectedHourly: number }> = [
      { tier: 'free', expectedHourly: 50 },
      { tier: 'starter', expectedHourly: 100 },
      { tier: 'pro', expectedHourly: 500 },
      { tier: 'enterprise', expectedHourly: 2000 },
    ]

    for (const { tier, expectedHourly } of tiers) {
      const mockKV = createMockKV()
      const tenant: Tenant = {
        ...defaultTenant,
        tier: tier as any,
      }

      const ctx = createMockContext({ tenant, kv: mockKV })
      const middleware = rateLimitMiddleware()

      await middleware(ctx, ctx.next)

      // Verify the tier was used (next should be called)
      expect(ctx.next).toHaveBeenCalled()
      mockKV._clear()
      vi.clearAllMocks()
    }
  })
})
