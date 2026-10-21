import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { Context, Next } from 'hono'
import { rateLimitMiddleware } from '../src/middleware/rate-limit'
import type { Tenant } from '../src/types/raas'

export interface MockKV {
  get: ReturnType<typeof vi.fn>
  put: ReturnType<typeof vi.fn>
  delete?: ReturnType<typeof vi.fn>
  _store?: Map<string, string>
  _clear?: () => void
}

export const createMockKV = (): MockKV => {
  const store = new Map<string, string>()
  return {
    get: vi.fn(async (key: string, options?: string) => {
      const value = store.get(key)
      if (value === undefined) return null
      if (options === 'json') {
        try {
          return JSON.parse(value) as unknown
        } catch {
          return null
        }
      }
      return value
    }),
    put: vi.fn(async (key: string, value: string) => {
      store.set(key, value)
    }),
    delete: vi.fn(async (key: string) => {
      store.delete(key)
    }),
    _store: store,
    _clear: () => store.clear(),
  }
}

export interface MockRateLimitContext {
  get: ReturnType<typeof vi.fn>
  json: ReturnType<typeof vi.fn>
  header: ReturnType<typeof vi.fn>
  env: Record<string, unknown>
  next: Next
  _headers: Record<string, string>
  _kv: MockKV
  status: number
  readonly jsonBody: unknown
  res: Response | null
  req: {
    method: string
    path: string
    header: ReturnType<typeof vi.fn>
  }
}

export const createMockContext = (overrides?: {
  tenant?: Tenant | null
  kv?: MockKV | null
  env?: Record<string, unknown>
}): MockRateLimitContext & Context => {
  const mockKV = overrides?.kv || createMockKV()
  const headers: Record<string, string> = {}
  let status = 200
  let jsonBody: unknown = null

  const ctx: MockRateLimitContext = {
    get: vi.fn((key: string) => {
      if (key === 'tenant') return overrides?.tenant ?? null
      return null
    }),
    json: vi.fn((body: unknown, newStatus?: number) => {
      jsonBody = body
      status = newStatus ?? status
      const resp = new Response(JSON.stringify(body), {
        status,
        headers: { ...headers },
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
    get status() {
      return status
    },
    set status(v: number) {
      status = v
    },
    get jsonBody() {
      return jsonBody
    },
    res: null,
    req: {
      method: 'GET',
      path: '/test',
      header: vi.fn(),
    },
  }
  return ctx as unknown as MockRateLimitContext & Context
}

export const defaultTenant: Tenant = {
  id: 'tenant-123',
  name: 'Test Tenant',
  api_key_hash: 'hash-abc',
  tier: 'free',
  created_at: '2024-01-01T00:00:00Z',
}

describe('rateLimitMiddleware — core windows', () => {
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
    const now = new Date('2024-01-15T10:30:00Z')
    vi.useFakeTimers()
    vi.setSystemTime(now)

    const windowStart = Math.floor(now.getTime() / 3600000) * 3600000
    const timestamp = Math.floor(windowStart / 3600000)
    const hourKey = `rate:tenant-123:hour:${timestamp}`

    await mockKV.put(hourKey, JSON.stringify({ count: 50, windowStart }))

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
})
