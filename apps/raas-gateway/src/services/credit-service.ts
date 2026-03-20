/**
 * Credit Service — Manages tenant credit balances and transactions
 */

import type { Env } from '../index';

export interface CreditAccount {
  tenantId: string;
  balance: number;
  totalEarned: number;
  totalSpent: number;
}

export interface CreditTransaction {
  id: string;
  tenantId: string;
  amount: number; // positive = credit, negative = debit
  type: 'purchase' | 'mission' | 'refund' | 'rollover' | 'adjustment' | 'webhook';
  description: string;
  missionId?: string;
  metadata: Record<string, unknown>;
  createdAt: string;
}

export interface DeductResult {
  success: boolean;
  balance?: number;
  error?: 'INSUFFICIENT_CREDITS' | 'TENANT_NOT_FOUND';
}

// Mission complexity to credit cost mapping
export const MISSION_COSTS: Record<string, number> = {
  simple: 1,
  standard: 3,
  complex: 5,
};

export class CreditService {
  constructor(private env: Env) {}

  /**
   * Get tenant credit balance
   */
  async getBalance(tenantId: string): Promise<number> {
    const result = await this.env.DB.prepare(
      'SELECT balance FROM tenants WHERE id = ?'
    )
      .bind(tenantId)
      .first<{ balance: number }>();

    return result?.balance ?? 0;
  }

  /**
   * Get full credit account info
   */
  async getAccount(tenantId: string): Promise<CreditAccount | null> {
    const result = await this.env.DB.prepare(
      'SELECT id as tenantId, balance, total_earned as totalEarned, total_spent as totalSpent FROM tenants WHERE id = ?'
    )
      .bind(tenantId)
      .first<CreditAccount>();

    return result || null;
  }

  /**
   * Deduct credits from tenant account (atomic)
   * Returns false if insufficient balance
   */
  async deduct(
    tenantId: string,
    amount: number,
    type: 'mission' | 'adjustment',
    description: string,
    missionId?: string
  ): Promise<DeductResult> {
    if (amount <= 0) {
      throw new Error('Deduction amount must be positive');
    }

    // Get current balance
    const tenant = await this.env.DB.prepare(
      'SELECT id, balance, total_spent FROM tenants WHERE id = ?'
    )
      .bind(tenantId)
      .first<{ id: string; balance: number; total_spent: number }>();

    if (!tenant) {
      return { success: false, error: 'TENANT_NOT_FOUND' as const };
    }

    if (tenant.balance < amount) {
      return { success: false, error: 'INSUFFICIENT_CREDITS' as const };
    }

    // Update tenant balance
    const newBalance = tenant.balance - amount;
    await this.env.DB.prepare(
      'UPDATE tenants SET balance = ?, total_spent = total_spent + ? WHERE id = ?'
    )
      .bind(newBalance, amount, tenantId)
      .run();

    // Record transaction
    const transactionId = crypto.randomUUID();
    await this.env.DB.prepare(
      `INSERT INTO credit_transactions
       (id, tenant_id, amount, type, mission_id, description, metadata, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        transactionId,
        tenantId,
        -amount, // Negative for debit
        type,
        missionId || null,
        description,
        JSON.stringify({}),
        new Date().toISOString()
      )
      .run();

    // Record usage log if mission
    if (type === 'mission' && missionId) {
      await this.env.DB.prepare(
        `INSERT INTO usage_logs (id, tenant_id, mission_id, credits_cost, timestamp, success, metadata)
         VALUES (?, ?, ?, ?, ?, 1, ?)`
      )
        .bind(
          crypto.randomUUID(),
          tenantId,
          missionId,
          amount,
          new Date().toISOString(),
          JSON.stringify({ type, description })
        )
        .run();
    }

    return { success: true, balance: newBalance };
  }

  /**
   * Add credits to tenant account
   */
  async addCredits(
    tenantId: string,
    amount: number,
    type: 'purchase' | 'refund' | 'rollover' | 'adjustment' | 'webhook',
    description: string,
    metadata: Record<string, unknown> = {}
  ): Promise<number> {
    if (amount <= 0) {
      throw new Error('Credit amount must be positive');
    }

    // Check if tenant exists
    const existing = await this.env.DB.prepare(
      'SELECT id, balance, total_earned FROM tenants WHERE id = ?'
    )
      .bind(tenantId)
      .first<{ id: string; balance: number; total_earned: number }>();

    let newBalance: number;

    if (existing) {
      // Update existing tenant
      newBalance = existing.balance + amount;
      await this.env.DB.prepare(
        'UPDATE tenants SET balance = ?, total_earned = total_earned + ? WHERE id = ?'
      )
        .bind(newBalance, amount, tenantId)
        .run();
    } else {
      // Create new tenant with credits
      newBalance = amount;
      await this.env.DB.prepare(
        `INSERT INTO tenants (id, balance, total_earned, total_spent, tier, name, email, created_at)
         VALUES (?, ?, 0, 0, 'starter', ?, ?, datetime('now'))`
      )
        .bind(tenantId, amount, `tenant-${tenantId}`, `${tenantId}@raas.local`)
        .run();
    }

    // Record transaction
    const transactionId = crypto.randomUUID();
    await this.env.DB.prepare(
      `INSERT INTO credit_transactions
       (id, tenant_id, amount, type, description, metadata, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    )
      .bind(
        transactionId,
        tenantId,
        amount, // Positive for credit
        type,
        description,
        JSON.stringify(metadata),
        new Date().toISOString()
      )
      .run();

    return newBalance;
  }

  /**
   * Get transaction history for tenant
   */
  async getHistory(
    tenantId: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<CreditTransaction[]> {
    const safeLimit = Math.max(1, Math.min(200, limit));
    const safeOffset = Math.max(0, offset);

    const results = await this.env.DB.prepare(
      `SELECT id, tenant_id as tenantId, amount, type, mission_id as missionId,
              description, metadata, created_at as createdAt
       FROM credit_transactions
       WHERE tenant_id = ?
       ORDER BY created_at DESC
       LIMIT ? OFFSET ?`
    )
      .bind(tenantId, safeLimit, safeOffset)
      .all<CreditTransaction>();

    return results.results.map(row => ({
      ...row,
      metadata: row.metadata ? JSON.parse(row.metadata as unknown as string) : {},
    }));
  }

  /**
   * Get usage logs for tenant
   */
  async getUsageLogs(
    tenantId: string,
    limit: number = 50,
    missionId?: string
  ): Promise<any[]> {
    let query = `
      SELECT id, tenant_id as tenantId, mission_id as missionId,
             credits_cost as creditsCost, timestamp, success, metadata
      FROM usage_logs
      WHERE tenant_id = ?
    `;

    const bindings: any[] = [tenantId];

    if (missionId) {
      query += ' AND mission_id = ?';
      bindings.push(missionId);
    }

    query += ' ORDER BY timestamp DESC LIMIT ?';
    bindings.push(Math.max(1, Math.min(200, limit)));

    const results = await this.env.DB.prepare(query)
      .bind(...bindings)
      .all();

    return results.results.map(row => ({
      ...row,
      metadata: row.metadata ? JSON.parse(row.metadata as unknown as string) : {},
    }));
  }

  /**
   * Check if tenant has sufficient credits
   */
  async hasSufficientCredits(tenantId: string, amount: number): Promise<boolean> {
    const balance = await this.getBalance(tenantId);
    return balance >= amount;
  }

  /**
   * Get mission cost by complexity
   */
  getMissionCost(complexity: 'simple' | 'standard' | 'complex'): number {
    return MISSION_COSTS[complexity] || MISSION_COSTS.standard;
  }
}
