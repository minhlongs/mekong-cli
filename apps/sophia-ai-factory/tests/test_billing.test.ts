import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MCUBilling } from '../src/billing/mcu';

// Mock DurableObjectState
const createMockState = () => {
  const storage = new Map<string, unknown>();
  return {
    storage: {
      get: vi.fn(async (key: string) => storage.get(key)),
      put: vi.fn(async (key: string, value: unknown) => { storage.set(key, value); }),
      delete: vi.fn(async (key: string) => { storage.delete(key); }),
      list: vi.fn(async () => Array.from(storage.entries())),
    },
    blockConcurrencyWhile: vi.fn(async (cb: () => Promise<void>) => cb()),
  };
};

describe('MCUBilling', () => {
  let state: ReturnType<typeof createMockState>;
  let billing: MCUBilling;

  beforeEach(() => {
    state = createMockState();
    billing = new MCUBilling(state as any, { MCU_CONFIG: JSON.stringify({}) });
  });

  it('should return zero balance for new user', async () => {
    const balance = await billing.getBalance('user-123');
    expect(balance.userId).toBe('user-123');
    expect(balance.balance).toBe(0);
    expect(balance.tier).toBe('BASIC');
  });

  it('should top up credits', async () => {
    const balance = await billing.topUp({ userId: 'user-123', credits: 100 });
    expect(balance.balance).toBe(100);
    expect(balance.userId).toBe('user-123');
  });

  it('should charge credits successfully', async () => {
    await billing.topUp({ userId: 'user-123', credits: 100 });
    const result = await billing.charge({ userId: 'user-123', seconds: 10 });

    expect(result.success).toBe(true);
    expect(result.creditsCharged).toBe(10); // 1 credit per second at BASIC tier
    expect(result.remainingBalance).toBe(90);
  });

  it('should apply tier multipliers', async () => {
    await billing.topUp({ userId: 'user-123', credits: 100 });
    await billing.setTier('user-123', 'PREMIUM');

    const result = await billing.charge({ userId: 'user-123', seconds: 10 });

    expect(result.success).toBe(true);
    expect(result.creditsCharged).toBe(8); // 10 * 0.8 = 8 at PREMIUM tier
    expect(result.remainingBalance).toBe(92);
  });

  it('should fail charge when insufficient credits', async () => {
    await billing.topUp({ userId: 'user-123', credits: 5 });
    const result = await billing.charge({ userId: 'user-123', seconds: 10 });

    expect(result.success).toBe(false);
    expect(result.creditsCharged).toBe(0);
    expect(result.remainingBalance).toBe(5);
    expect(result.error).toBe('Insufficient credits');
  });

  it('should be idempotent for charges', async () => {
    await billing.topUp({ userId: 'user-123', credits: 100 });

    const idempotencyKey = 'charge:test-key';
    const result1 = await billing.charge({ userId: 'user-123', seconds: 10, idempotencyKey });
    const result2 = await billing.charge({ userId: 'user-123', seconds: 10, idempotencyKey });

    expect(result1).toEqual(result2);
    expect(result1.creditsCharged).toBe(10);
  });

  it('should be idempotent for topups', async () => {
    const idempotencyKey = 'topup:test-key';
    const result1 = await billing.topUp({ userId: 'user-123', credits: 50, idempotencyKey });
    const result2 = await billing.topUp({ userId: 'user-123', credits: 50, idempotencyKey });

    expect(result1).toEqual(result2);
    expect(result1.balance).toBe(50);
  });

  it('should set user tier', async () => {
    await billing.setTier('user-123', 'ENTERPRISE');
    const balance = await billing.getBalance('user-123');
    expect(balance.tier).toBe('ENTERPRISE');
  });

  it('should calculate credits correctly for all tiers', async () => {
    const tiers = ['BASIC', 'PREMIUM', 'ENTERPRISE', 'MASTER'] as const;
    const expectedMultipliers = [1, 0.8, 0.6, 0.4];

    for (let i = 0; i < tiers.length; i++) {
      const tier = tiers[i];
      const state = createMockState();
      const billing = new MCUBilling(state as any, { MCU_CONFIG: JSON.stringify({}) });

      await billing.topUp({ userId: `user-${i}`, credits: 100 });
      await billing.setTier(`user-${i}`, tier);

      const result = await billing.charge({ userId: `user-${i}`, seconds: 10 });
      expect(result.creditsCharged).toBe(Math.ceil(10 * expectedMultipliers[i]));
    }
  });

  it('should list all balances', async () => {
    await billing.topUp({ userId: 'user-1', credits: 100 });
    await billing.topUp({ userId: 'user-2', credits: 200 });
    await billing.setTier('user-2', 'PREMIUM');

    const balances = await billing.getAllBalances();
    expect(balances).toHaveLength(2);

    const user1 = balances.find(b => b.userId === 'user-1');
    const user2 = balances.find(b => b.userId === 'user-2');

    expect(user1?.balance).toBe(100);
    expect(user1?.tier).toBe('BASIC');
    expect(user2?.balance).toBe(200);
    expect(user2?.tier).toBe('PREMIUM');
  });
});