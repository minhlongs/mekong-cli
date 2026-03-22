/**
 * Platform Cost Dashboard Service
 * Manages cost entries and monthly budgets for platform spending visibility.
 */

import { nanoid } from 'nanoid';

// ── Entries ────────────────────────────────────────────────────────────────────

async function listEntries(db: any, filters?: { category?: string; period?: string }): Promise<unknown[]> {
  try {
    let sql = 'SELECT * FROM platform_cost_entries';
    const binds: unknown[] = [];
    const where: string[] = [];
    if (filters?.category) { where.push('category = ?'); binds.push(filters.category); }
    if (filters?.period)   { where.push('period = ?');   binds.push(filters.period); }
    if (where.length) sql += ' WHERE ' + where.join(' AND ');
    sql += ' ORDER BY created_at DESC';
    const rows = await db.prepare(sql).bind(...binds).all();
    return (rows.results as unknown[]);
  } catch (err) {
    throw new Error(err instanceof Error ? err.message : 'Failed to list entries');
  }
}

async function createEntry(db: any, data: {
  category: string;
  provider: string;
  service_name: string;
  amount: number;
  currency?: string;
  period?: string;
}): Promise<unknown> {
  try {
    const id = nanoid();
    const now = new Date().toISOString();
    const result = await db.prepare(
      `INSERT INTO platform_cost_entries (id, category, provider, service_name, amount, currency, period, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(
      id,
      data.category,
      data.provider,
      data.service_name,
      data.amount,
      data.currency ?? 'USD',
      data.period ?? null,
      now
    ).first();
    return result as unknown;
  } catch (err) {
    throw new Error(err instanceof Error ? err.message : 'Failed to create entry');
  }
}

// ── Budgets ────────────────────────────────────────────────────────────────────

async function getBudgets(db: any, period?: string): Promise<unknown[]> {
  try {
    let sql = 'SELECT * FROM platform_cost_budgets';
    const binds: unknown[] = [];
    if (period) { sql += ' WHERE period = ?'; binds.push(period); }
    sql += ' ORDER BY category ASC';
    const rows = await db.prepare(sql).bind(...binds).all();
    return (rows.results as unknown[]);
  } catch (err) {
    throw new Error(err instanceof Error ? err.message : 'Failed to get budgets');
  }
}

// ── Dashboard summary ──────────────────────────────────────────────────────────

async function getDashboard(db: any, period?: string): Promise<unknown> {
  try {
    let entrySql = 'SELECT category, provider, SUM(amount) as total FROM platform_cost_entries';
    const binds: unknown[] = [];
    if (period) { entrySql += ' WHERE period = ?'; binds.push(period); }
    entrySql += ' GROUP BY category, provider ORDER BY total DESC';

    const [summaryRows, budgetRows] = await Promise.all([
      db.prepare(entrySql).bind(...binds).all(),
      getBudgets(db, period),
    ]);

    const summary = summaryRows.results as unknown[];
    const totalSpend = (summary as { total: number }[]).reduce((s, r) => s + (r.total ?? 0), 0);

    return { period: period ?? 'all', total_spend: totalSpend, by_category: summary, budgets: budgetRows };
  } catch (err) {
    throw new Error(err instanceof Error ? err.message : 'Failed to get dashboard');
  }
}

export const platformCostDashboardService = { listEntries, createEntry, getBudgets, getDashboard };
