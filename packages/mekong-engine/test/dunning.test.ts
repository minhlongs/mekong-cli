import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as dunning from '../src/raas/dunning'

// Mock D1Database
const createMockD1 = () => ({
  prepare: vi.fn(() => ({
    bind: vi.fn(() => ({
      first: vi.fn(),
      run: vi.fn(),
      all: vi.fn(),
    })),
  })),
  exec: vi.fn(),
})

describe('checkLicenseStatus', () => {
  let mockD1: ReturnType<typeof createMockD1>

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('returns active for free tier tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'free', dunning_status: null }),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('active')
  })

  it('returns active for pro tier tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: null }),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('active')
  })

  it('returns active for enterprise tier tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'enterprise', dunning_status: null }),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('active')
  })

  it('returns suspended for suspended tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: 'suspended' }),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('suspended')
  })

  it('returns blocked for blocked tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'blocked', dunning_status: null }),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('blocked')
  })

  it('returns blocked for tenant with dunning_status blocked', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: 'blocked' }),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('blocked')
  })

  it('returns expired for non-existent tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue(null),
      }),
    } as any)

    const status = await dunning.checkLicenseStatus(mockD1 as any, 'tenant-1')
    expect(status).toBe('expired')
  })
})

describe('suspendTenant', () => {
  let mockD1: ReturnType<typeof createMockD1>

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('successfully suspends tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockResolvedValue({ success: true }),
      }),
    } as any)

    const result = await dunning.suspendTenant(mockD1 as any, 'tenant-1', 'Credit exhaustion')
    expect(result).toBe(true)
  })

  it('returns false on error', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockRejectedValue(new Error('DB error')),
      }),
    } as any)

    const result = await dunning.suspendTenant(mockD1 as any, 'tenant-1', 'Credit exhaustion')
    expect(result).toBe(false)
  })
})

describe('reactivateTenant', () => {
  let mockD1: ReturnType<typeof createMockD1>

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('successfully reactivates tenant with default tier', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockResolvedValue({ success: true }),
      }),
    } as any)

    const result = await dunning.reactivateTenant(mockD1 as any, 'tenant-1')
    expect(result).toBe(true)
  })

  it('successfully reactivates tenant with custom tier', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockResolvedValue({ success: true }),
      }),
    } as any)

    const result = await dunning.reactivateTenant(mockD1 as any, 'tenant-1', 'pro')
    expect(result).toBe(true)
  })

  it('returns false on error', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockRejectedValue(new Error('DB error')),
      }),
    } as any)

    const result = await dunning.reactivateTenant(mockD1 as any, 'tenant-1')
    expect(result).toBe(false)
  })
})

describe('getDunningSchedule', () => {
  let mockD1: ReturnType<typeof createMockD1>

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('returns expired for non-existent tenant', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue(null),
      }),
    } as any)

    const schedule = await dunning.getDunningSchedule(mockD1 as any, 'tenant-1')
    expect(schedule.status).toBe('expired')
    expect(schedule.daysUntilSuspension).toBe(0)
  })

  it('returns suspended schedule for suspended tenant', async () => {
    const now = new Date().toISOString()
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: 'suspended', updated_at: now }),
      }),
    } as any)

    const schedule = await dunning.getDunningSchedule(mockD1 as any, 'tenant-1')
    expect(schedule.status).toBe('suspended')
    expect(schedule.daysUntilSuspension).toBe(0)
  })

  it('returns blocked schedule for blocked tenant', async () => {
    const now = new Date().toISOString()
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'blocked', dunning_status: null, updated_at: now }),
      }),
    } as any)

    const schedule = await dunning.getDunningSchedule(mockD1 as any, 'tenant-1')
    expect(schedule.status).toBe('blocked')
    expect(schedule.daysUntilSuspension).toBe(0)
  })

  it('returns active schedule with grace period for active tenant', async () => {
    const now = new Date()
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: null, updated_at: now.toISOString() }),
      }),
    } as any)

    const schedule = await dunning.getDunningSchedule(mockD1 as any, 'tenant-1')
    expect(schedule.status).toBe('active')
    expect(schedule.daysUntilSuspension).toBeGreaterThanOrEqual(0)
    expect(schedule.daysUntilSuspension).toBeLessThanOrEqual(7)
    expect(schedule.gracePeriodEnds).toBeDefined()
  })
})

describe('shouldSuspendForCreditExhaustion', () => {
  let mockD1: ReturnType<typeof createMockD1>

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('returns false when tenant has positive balance', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        first: vi.fn().mockResolvedValue({ balance: 100 }),
      }),
    } as any)

    const result = await dunning.shouldSuspendForCreditExhaustion(mockD1 as any, 'tenant-1')
    expect(result.shouldSuspend).toBe(false)
    expect(result.balance).toBe(100)
    expect(result.daysOverdue).toBe(0)
  })

  it('returns false when tenant has zero balance but within grace period', async () => {
    const now = new Date().toISOString()
    vi.mocked(mockD1.prepare)
      .mockReturnValueOnce({
        bind: vi.fn().mockReturnValue({
          first: vi.fn().mockResolvedValue({ balance: 0 }),
        }),
      } as any)
      .mockReturnValueOnce({
        bind: vi.fn().mockReturnValue({
          first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: null, updated_at: now }),
        }),
      } as any)

    const result = await dunning.shouldSuspendForCreditExhaustion(mockD1 as any, 'tenant-1')
    expect(result.shouldSuspend).toBe(false)
    expect(result.balance).toBe(0)
  })

  it('returns true when tenant has zero balance and grace period expired', async () => {
    const oldDate = new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString() // 10 days ago
    vi.mocked(mockD1.prepare)
      .mockReturnValueOnce({
        bind: vi.fn().mockReturnValue({
          first: vi.fn().mockResolvedValue({ balance: 0 }),
        }),
      } as any)
      .mockReturnValueOnce({
        bind: vi.fn().mockReturnValue({
          first: vi.fn().mockResolvedValue({ tier: 'pro', dunning_status: null, updated_at: oldDate }),
        }),
      } as any)

    const result = await dunning.shouldSuspendForCreditExhaustion(mockD1 as any, 'tenant-1')
    expect(result.shouldSuspend).toBe(true)
    expect(result.balance).toBe(0)
    expect(result.daysOverdue).toBeGreaterThan(0)
  })
})

describe('emitLicenseEvent', () => {
  let mockD1: ReturnType<typeof createMockD1>

  beforeEach(() => {
    mockD1 = createMockD1()
  })

  it('successfully emits license event', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockResolvedValue({ success: true }),
      }),
    } as any)

    await expect(
      dunning.emitLicenseEvent(mockD1 as any, 'tenant-1', 'license.suspended', { reason: 'test' })
    ).resolves.toBeUndefined()
  })

  it('silently ignores errors', async () => {
    vi.mocked(mockD1.prepare).mockReturnValue({
      bind: vi.fn().mockReturnValue({
        run: vi.fn().mockRejectedValue(new Error('DB error')),
      }),
    } as any)

    await expect(
      dunning.emitLicenseEvent(mockD1 as any, 'tenant-1', 'license.suspended', { reason: 'test' })
    ).resolves.toBeUndefined()
  })
})
