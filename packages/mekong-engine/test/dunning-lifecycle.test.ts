import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { D1Database } from '@cloudflare/workers-types'
import * as dunning from '../src/raas/dunning'
import { createMockD1, makeFirstStmt, makeRunStmt } from './dunning.test'

describe('getDunningSchedule', () => {
  let mockD1: D1Database

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('returns expired for non-existent tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt(null))

    const schedule = await dunning.getDunningSchedule(mockD1, 'tenant-1')
    expect(schedule.status).toBe('expired')
    expect(schedule.daysUntilSuspension).toBe(0)
  })

  it('returns suspended schedule for suspended tenant', async () => {
    const now = new Date().toISOString()
    vi.mocked(mockD1.prepare).mockReturnValue(
      makeFirstStmt({ tier: 'pro', dunning_status: 'suspended', updated_at: now }),
    )

    const schedule = await dunning.getDunningSchedule(mockD1, 'tenant-1')
    expect(schedule.status).toBe('suspended')
    expect(schedule.daysUntilSuspension).toBe(0)
  })

  it('returns blocked schedule for blocked tenant', async () => {
    const now = new Date().toISOString()
    vi.mocked(mockD1.prepare).mockReturnValue(
      makeFirstStmt({ tier: 'blocked', dunning_status: null, updated_at: now }),
    )

    const schedule = await dunning.getDunningSchedule(mockD1, 'tenant-1')
    expect(schedule.status).toBe('blocked')
    expect(schedule.daysUntilSuspension).toBe(0)
  })

  it('returns active schedule with grace period for active tenant', async () => {
    const now = new Date()
    vi.mocked(mockD1.prepare).mockReturnValue(
      makeFirstStmt({ tier: 'pro', dunning_status: null, updated_at: now.toISOString() }),
    )

    const schedule = await dunning.getDunningSchedule(mockD1, 'tenant-1')
    expect(schedule.status).toBe('active')
    expect(schedule.daysUntilSuspension).toBeGreaterThanOrEqual(0)
    expect(schedule.daysUntilSuspension).toBeLessThanOrEqual(7)
    expect(schedule.gracePeriodEnds).toBeDefined()
  })
})

describe('shouldSuspendForCreditExhaustion', () => {
  let mockD1: D1Database

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('returns false when tenant has positive balance', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeFirstStmt({ balance: 100 }))

    const result = await dunning.shouldSuspendForCreditExhaustion(mockD1, 'tenant-1')
    expect(result.shouldSuspend).toBe(false)
    expect(result.balance).toBe(100)
    expect(result.daysOverdue).toBe(0)
  })

  it('returns false when tenant has zero balance but within grace period', async () => {
    const now = new Date().toISOString()
    vi.mocked(mockD1.prepare)
      .mockReturnValueOnce(makeFirstStmt({ balance: 0 }))
      .mockReturnValueOnce(makeFirstStmt({ tier: 'pro', dunning_status: null, updated_at: now }))

    const result = await dunning.shouldSuspendForCreditExhaustion(mockD1, 'tenant-1')
    expect(result.shouldSuspend).toBe(false)
    expect(result.balance).toBe(0)
  })

  it('returns true when tenant has zero balance and grace period expired', async () => {
    const oldDate = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString()
    vi.mocked(mockD1.prepare)
      .mockReturnValueOnce(makeFirstStmt({ balance: 0 }))
      .mockReturnValueOnce(makeFirstStmt({ tier: 'pro', dunning_status: null, updated_at: oldDate }))

    const result = await dunning.shouldSuspendForCreditExhaustion(mockD1, 'tenant-1')
    expect(result.shouldSuspend).toBe(true)
    expect(result.balance).toBe(0)
    expect(result.daysOverdue).toBeGreaterThan(0)
  })
})

describe('emitLicenseEvent', () => {
  let mockD1: D1Database

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('successfully emits license event', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(makeRunStmt(async () => ({ success: true })))

    await expect(
      dunning.emitLicenseEvent(mockD1, 'tenant-1', 'license.suspended', { reason: 'test' }),
    ).resolves.toBeUndefined()
  })

  it('silently ignores errors', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue(
      makeRunStmt(async () => {
        throw new Error('DB error')
      }),
    )

    await expect(
      dunning.emitLicenseEvent(mockD1, 'tenant-1', 'license.suspended', { reason: 'test' }),
    ).resolves.toBeUndefined()
  })
})
