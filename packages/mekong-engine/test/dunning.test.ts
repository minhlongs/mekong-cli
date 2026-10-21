import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { D1Database, D1PreparedStatement } from '@cloudflare/workers-types'
import * as dunning from '../src/raas/dunning'

export const createMockD1 = (): D1Database =>
  ({
    prepare: vi.fn(() => ({
      bind: vi.fn(() => ({
        first: vi.fn(),
        run: vi.fn(),
        all: vi.fn(),
      })),
    })),
    exec: vi.fn(),
  }) as unknown as D1Database

export const makeFirstStmt = (value: unknown): D1PreparedStatement =>
  ({
    bind: vi.fn().mockReturnValue({
      first: vi.fn().mockResolvedValue(value),
    }),
  }) as unknown as D1PreparedStatement

export const makeRunStmt = (impl: () => Promise<unknown>): D1PreparedStatement =>
  ({
    bind: vi.fn().mockReturnValue({
      run: vi.fn(impl),
    }),
  }) as unknown as D1PreparedStatement

describe('checkLicenseStatus', () => {
  let mockD1: D1Database

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('returns active for free tier tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ tier: 'free', dunning_status: null }))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('active')
  })

  it('returns active for pro tier tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ tier: 'pro', dunning_status: null }))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('active')
  })

  it('returns active for enterprise tier tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ tier: 'enterprise', dunning_status: null }))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('active')
  })

  it('returns suspended for suspended tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ tier: 'pro', dunning_status: 'suspended' }))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('suspended')
  })

  it('returns blocked for blocked tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ tier: 'blocked', dunning_status: null }))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('blocked')
  })

  it('returns blocked for tenant with dunning_status blocked', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ tier: 'pro', dunning_status: 'blocked' }))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('blocked')
  })

  it('returns expired for non-existent tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt(null))
    const status = await dunning.checkLicenseStatus(mockD1, 'tenant-1')
    expect(status).toBe('expired')
  })
})

describe('suspendTenant', () => {
  let mockD1: D1Database

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('successfully suspends tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeRunStmt(async () => ({ success: true })))
    const result = await dunning.suspendTenant(mockD1, 'tenant-1', 'Credit exhaustion')
    expect(result).toBe(true)
  })

  it('returns false on error', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(
      makeRunStmt(async () => {
        throw new Error('DB error')
      }),
    )
    const result = await dunning.suspendTenant(mockD1, 'tenant-1', 'Credit exhaustion')
    expect(result).toBe(false)
  })
})

describe('reactivateTenant', () => {
  let mockD1: D1Database

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('successfully reactivates tenant with default tier', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeRunStmt(async () => ({ success: true })))
    const result = await dunning.reactivateTenant(mockD1, 'tenant-1')
    expect(result).toBe(true)
  })

  it('successfully reactivates tenant with custom tier', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeRunStmt(async () => ({ success: true })))
    const result = await dunning.reactivateTenant(mockD1, 'tenant-1', 'pro')
    expect(result).toBe(true)
  })

  it('returns false on error', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(
      makeRunStmt(async () => {
        throw new Error('DB error')
      }),
    )
    const result = await dunning.reactivateTenant(mockD1, 'tenant-1')
    expect(result).toBe(false)
  })
})
