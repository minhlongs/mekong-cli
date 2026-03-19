import { describe, it, expect, vi, beforeEach } from 'vitest'
import { requireActiveLicense } from '../src/raas/license-middleware'
import * as dunning from '../src/raas/dunning'

// Mock the dunning module
vi.mock('../src/raas/dunning')

describe('requireActiveLicense middleware', () => {
  const mockD1 = {
    prepare: vi.fn(() => ({
      bind: vi.fn(() => ({
        first: vi.fn(),
      })),
    })),
  }

  const createMockContext = (overrides?: Partial<{
    tenant: any
    env: any
    status: number
    jsonBody: any
    nextCalled: boolean
  }>) => {
    const ctx = {
      get: vi.fn((key: string) => {
        if (key === 'tenant') return overrides?.tenant ?? null
        return null
      }),
      json: vi.fn((body: any, status?: number) => {
        ctx.jsonBody = body
        ctx.status = status
        return new Response(JSON.stringify(body), { status })
      }),
      status: 200,
      jsonBody: null,
      env: overrides?.env ?? {},
      next: vi.fn().mockImplementation(() => Promise.resolve()),
    }
    return ctx as any
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns 401 when no tenant context', async () => {
    const ctx = createMockContext({ tenant: null })

    await requireActiveLicense(ctx, ctx.next)

    expect(ctx.status).toBe(401)
    expect(ctx.jsonBody).toEqual({ error: 'Authentication required' })
  })

  it('returns 503 when no D1 binding', async () => {
    const ctx = createMockContext({
      tenant: { id: 'tenant-1' },
      env: {}
    })

    await requireActiveLicense(ctx, ctx.next)

    expect(ctx.status).toBe(503)
    expect(ctx.jsonBody).toEqual({ error: 'D1 not configured' })
  })

  it('calls next() when license is active', async () => {
    vi.mocked(dunning.checkLicenseStatus).mockResolvedValue('active')

    const ctx = createMockContext({
      tenant: { id: 'tenant-1' },
      env: { DB: mockD1 }
    })

    await requireActiveLicense(ctx, ctx.next)

    expect(dunning.checkLicenseStatus).toHaveBeenCalledWith(mockD1, 'tenant-1')
    expect(ctx.next).toHaveBeenCalled()
    expect(ctx.status).toBe(200)
  })

  it('returns 403 when license is suspended', async () => {
    vi.mocked(dunning.checkLicenseStatus).mockResolvedValue('suspended')

    const ctx = createMockContext({
      tenant: { id: 'tenant-1' },
      env: { DB: mockD1 }
    })

    await requireActiveLicense(ctx, ctx.next)

    expect(ctx.status).toBe(403)
    expect(ctx.jsonBody).toEqual({
      error: 'Account suspended',
      code: 'ACCOUNT_SUSPENDED',
      message: 'Your account has been suspended. Please contact support or add credits to reactivate.',
    })
  })

  it('returns 403 when license is blocked', async () => {
    vi.mocked(dunning.checkLicenseStatus).mockResolvedValue('blocked')

    const ctx = createMockContext({
      tenant: { id: 'tenant-1' },
      env: { DB: mockD1 }
    })

    await requireActiveLicense(ctx, ctx.next)

    expect(ctx.status).toBe(403)
    expect(ctx.jsonBody).toEqual({
      error: 'Account suspended',
      code: 'ACCOUNT_SUSPENDED',
      message: 'Your account has been suspended. Please contact support or add credits to reactivate.',
    })
  })

  it('returns 403 when license is expired', async () => {
    vi.mocked(dunning.checkLicenseStatus).mockResolvedValue('expired')

    const ctx = createMockContext({
      tenant: { id: 'tenant-1' },
      env: { DB: mockD1 }
    })

    await requireActiveLicense(ctx, ctx.next)

    expect(ctx.status).toBe(403)
    expect(ctx.jsonBody).toEqual({
      error: 'Account expired',
      code: 'ACCOUNT_EXPIRED',
      message: 'Your account has expired. Please create a new account or contact support.',
    })
  })
})
