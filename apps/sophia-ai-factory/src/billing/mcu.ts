import { z } from 'zod';

export const MCUConfigSchema = z.object({
  creditsPerSecond: z.number().positive().default(1),
  tierMultipliers: z.object({
    BASIC: z.number().positive().default(1),
    PREMIUM: z.number().positive().default(0.8),
    ENTERPRISE: z.number().positive().default(0.6),
    MASTER: z.number().positive().default(0.4),
  }).default({
    BASIC: 1,
    PREMIUM: 0.8,
    ENTERPRISE: 0.6,
    MASTER: 0.4,
  }),
});

export type MCUConfig = z.infer<typeof MCUConfigSchema>;

export const CreditBalanceSchema = z.object({
  userId: z.string(),
  balance: z.number().default(0),
  tier: z.enum(['BASIC', 'PREMIUM', 'ENTERPRISE', 'MASTER']).default('BASIC'),
  updatedAt: z.number(),
});

export type CreditBalance = z.infer<typeof CreditBalanceSchema>;

export const ChargeRequestSchema = z.object({
  userId: z.string(),
  seconds: z.number().positive(),
  tier: z.enum(['BASIC', 'PREMIUM', 'ENTERPRISE', 'MASTER']).optional(),
  idempotencyKey: z.string().optional(),
});

export type ChargeRequest = z.infer<typeof ChargeRequestSchema>;

export const ChargeResultSchema = z.object({
  success: z.boolean(),
  creditsCharged: z.number(),
  remainingBalance: z.number(),
  error: z.string().optional(),
});

export type ChargeResult = z.infer<typeof ChargeResultSchema>;

export const TopUpRequestSchema = z.object({
  userId: z.string(),
  credits: z.number().positive(),
  idempotencyKey: z.string().optional(),
});

export type TopUpRequest = z.infer<typeof TopUpRequestSchema>;

export class MCUBilling {
  private state: DurableObjectState;
  private config: MCUConfig;

  constructor(state: DurableObjectState, env: { MCU_CONFIG?: string }) {
    this.state = state;
    this.config = env.MCU_CONFIG ? MCUConfigSchema.parse(JSON.parse(env.MCU_CONFIG)) : MCUConfigSchema.parse({});
  }

  async getBalance(userId: string): Promise<CreditBalance> {
    const stored = await this.state.storage.get<CreditBalance>(`balance:${userId}`);
    if (stored) {
      return CreditBalanceSchema.parse(stored);
    }
    return CreditBalanceSchema.parse({ userId, balance: 0, tier: 'BASIC', updatedAt: Date.now() });
  }

  async charge(request: ChargeRequest): Promise<ChargeResult> {
    const validated = ChargeRequestSchema.parse(request);
    const idempotencyKey = validated.idempotencyKey || `charge:${validated.userId}:${Date.now()}:${validated.seconds}`;

    // Check idempotency
    const existing = await this.state.storage.get<ChargeResult>(`idempotent:${idempotencyKey}`);
    if (existing) {
      return existing;
    }

    const balance = await this.getBalance(validated.userId);
    // Use tier from request if provided, otherwise use user's stored tier
    const tier = validated.tier || balance.tier;
    const multiplier = this.config.tierMultipliers[tier];
    const creditsCharged = Math.ceil(validated.seconds * this.config.creditsPerSecond * multiplier);

    if (balance.balance < creditsCharged) {
      const result: ChargeResult = {
        success: false,
        creditsCharged: 0,
        remainingBalance: balance.balance,
        error: 'Insufficient credits',
      };
      await this.state.storage.put(`idempotent:${idempotencyKey}`, result);
      return result;
    }

    const newBalance = balance.balance - creditsCharged;
    const updatedBalance: CreditBalance = {
      ...balance,
      balance: newBalance,
      tier,
      updatedAt: Date.now(),
    };

    await this.state.storage.put(`balance:${validated.userId}`, updatedBalance);

    const result: ChargeResult = {
      success: true,
      creditsCharged,
      remainingBalance: newBalance,
    };

    await this.state.storage.put(`idempotent:${idempotencyKey}`, result);
    return result;
  }

  async topUp(request: TopUpRequest): Promise<CreditBalance> {
    const validated = TopUpRequestSchema.parse(request);
    const idempotencyKey = validated.idempotencyKey || `topup:${validated.userId}:${Date.now()}:${validated.credits}`;

    const existing = await this.state.storage.get<CreditBalance>(`idempotent:${idempotencyKey}`);
    if (existing) {
      return existing;
    }

    const balance = await this.getBalance(validated.userId);
    const newBalance = balance.balance + validated.credits;

    const updatedBalance: CreditBalance = {
      ...balance,
      balance: newBalance,
      updatedAt: Date.now(),
    };

    await this.state.storage.put(`balance:${validated.userId}`, updatedBalance);
    await this.state.storage.put(`idempotent:${idempotencyKey}`, updatedBalance);

    return updatedBalance;
  }

  async setTier(userId: string, tier: 'BASIC' | 'PREMIUM' | 'ENTERPRISE' | 'MASTER'): Promise<CreditBalance> {
    const balance = await this.getBalance(userId);
    const updatedBalance: CreditBalance = {
      ...balance,
      tier,
      updatedAt: Date.now(),
    };
    await this.state.storage.put(`balance:${userId}`, updatedBalance);
    return updatedBalance;
  }

  async getAllBalances(): Promise<CreditBalance[]> {
    const balances: CreditBalance[] = [];
    const allItems = await this.state.storage.list();
    for (const [key, value] of allItems) {
      if (key.startsWith('balance:')) {
        balances.push(CreditBalanceSchema.parse(value));
      }
    }
    return balances;
  }
}

export function createMCUBillingDO(state: DurableObjectState, env: { MCU_CONFIG?: string }): MCUBilling {
  return new MCUBilling(state, env);
}