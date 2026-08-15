/** Customer lifecycle management — health, churn risk, MRR stats */
import { randomUUID } from 'node:crypto';
import type { Result } from '../types/common.js';
import { ok, err } from '../types/common.js';
import type { Customer } from './types.js';
import type { CrmStore } from './store.js';

export interface CustomerSummary {
  total: number;
  active: number;
  churned: number;
  trial: number;
  mrr: number;
  avgHealthScore: number;
}

export class CustomerManager {
  constructor(private store: CrmStore) {}

  async getAll(filter?: Partial<Customer>): Promise<Result<Customer[]>> {
    return this.store.getAll('customers', filter);
  }

  async getById(id: string): Promise<Result<Customer | null>> {
    return this.store.getById('customers', id);
  }

  async create(
    input: Omit<Customer, 'id' | 'createdAt' | 'updatedAt' | 'healthScore' | 'notes' | 'tags' | 'metadata'>,
  ): Promise<Result<Customer>> {
    const now = new Date().toISOString();
    const customer: Customer = {
      id: randomUUID(),
      healthScore: 50,
      notes: [],
      tags: [],
      metadata: {},
      createdAt: now,
      updatedAt: now,
      ...input,
    };
    return this.store.save('customers', customer);
  }

  async update(id: string, patch: Partial<Omit<Customer, 'id' | 'createdAt'>>): Promise<Result<Customer>> {
    try {
      const res = await this.store.getById('customers', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Customer ${id} not found`));
      const updated: Customer = {
        ...res.value,
        ...patch,
        updatedAt: new Date().toISOString(),
      };
      return this.store.save('customers', updated);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /**
   * Health score 0-100:
   * - Base 50
   * - Recent update within 30 days: +20
   * - Active status: +15
   * - Has MRR: +10
   * - Churned: -40
   * - No activity in 90+ days: -15
   */
  async calculateHealthScore(id: string): Promise<Result<number>> {
    try {
      const res = await this.store.getById('customers', id);
      if (!res.ok) return res;
      if (!res.value) return err(new Error(`Customer ${id} not found`));
      const c = res.value;

      let score = 50;
      const now = Date.now();
      const updatedAgo = now - new Date(c.updatedAt).getTime();
      const msPerDay = 86_400_000;

      if (updatedAgo < 30 * msPerDay) score += 20;
      else if (updatedAgo > 90 * msPerDay) score -= 15;

      if (c.status === 'active') score += 15;
      if (c.status === 'churned') score -= 40;
      if (c.mrr > 0) score += 10;

      // Penalise high ticket load (proxy via notes count as ticket count unknown here)
      if (c.notes.length > 10) score -= 5;

      score = Math.max(0, Math.min(100, score));

      const updated: Customer = { ...c, healthScore: score, updatedAt: new Date().toISOString() };
      await this.store.save('customers', updated);
      return ok(score);
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  /** Customers with healthScore < 30 */
  async getChurnRisk(): Promise<Result<Customer[]>> {
    try {
      const res = await this.store.getAll('customers');
      if (!res.ok) return res;
      return ok(res.value.filter((c) => c.healthScore < 30 && c.status !== 'churned'));
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }

  async getSummary(): Promise<Result<CustomerSummary>> {
    try {
      const res = await this.store.getAll('customers');
      if (!res.ok) return res;
      const customers = res.value;
      const active = customers.filter((c) => c.status === 'active');
      const churned = customers.filter((c) => c.status === 'churned');
      const trial = customers.filter((c) => c.status === 'trial');
      const mrr = active.reduce((s, c) => s + c.mrr, 0);
      const avgHealthScore =
        customers.length > 0
          ? Math.round(customers.reduce((s, c) => s + c.healthScore, 0) / customers.length)
          : 0;
      return ok({
        total: customers.length,
        active: active.length,
        churned: churned.length,
        trial: trial.length,
        mrr,
        avgHealthScore,
      });
    } catch (e) {
      return err(e instanceof Error ? e : new Error(String(e)));
    }
  }
}
