/**
 * Usage export and invoice management routes
 * GET /v1/usage/export — CSV export of credit transactions
 * GET /v1/invoices     — List billing events as invoices
 * GET /v1/invoices/:id — Single invoice detail
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limiter';
import { json } from '../utils/response';

export const usageExport = new Hono<{ Bindings: Env }>();

usageExport.use('/*', auth());
usageExport.use('/*', rateLimit());

// Tier prices in cents — matches MCU billing tiers
const TIER_PRICE: Record<string, number> = { starter: 4900, pro: 14900, enterprise: 49900 };

function formatPeriod(dateStr: string | null): string {
  if (!dateStr) return 'Subscription';
  return new Date(dateStr).toLocaleString('en-US', { month: 'long', year: 'numeric' });
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

/**
 * GET /v1/usage/export?from=YYYY-MM-DD&to=YYYY-MM-DD
 * Returns CSV of credit transactions for the authenticated tenant.
 */
usageExport.get('/export', async (c) => {
  const tenant = getTenant(c);
  const from = c.req.query('from');
  const to = c.req.query('to');

  let query = 'SELECT id, type, amount, description, created_at FROM credit_transactions WHERE tenant_id = ?';
  const params: string[] = [tenant.tenantId];
  if (from) { query += ' AND created_at >= ?'; params.push(from); }
  if (to)   { query += ' AND created_at <= ?'; params.push(`${to}T23:59:59`); }
  query += ' ORDER BY created_at DESC LIMIT 10000';

  try {
    const result = await c.env.DB.prepare(query).bind(...params).all<{
      id: string; type: string; amount: number; description: string | null; created_at: string;
    }>();

    const lines = ['id,type,amount,description,created_at'];
    for (const row of result.results ?? []) {
      const desc = (row.description ?? '').replace(/"/g, '""');
      lines.push(`${row.id},${row.type},${row.amount},"${desc}",${row.created_at}`);
    }

    return new Response(lines.join('\n'), {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': `attachment; filename="usage-${tenant.tenantId}.csv"`,
      },
    });
  } catch {
    return json({ error: 'Failed to export usage data', code: 'EXPORT_FAILED' }, { status: 500 });
  }
});

/**
 * GET /v1/invoices — List subscriptions + credit purchases as invoices.
 */
usageExport.get('/', async (c) => {
  const tenant = getTenant(c);
  try {
    const [txResult, subResult] = await Promise.all([
      c.env.DB.prepare(
        `SELECT id, amount, description, metadata, created_at FROM credit_transactions
         WHERE tenant_id = ? AND type = 'purchase' ORDER BY created_at DESC LIMIT 100`
      ).bind(tenant.tenantId).all<{ id: string; amount: number; description: string | null; metadata: string | null; created_at: string }>(),
      c.env.DB.prepare(
        `SELECT id, tier, status, current_period_start, created_at FROM subscriptions
         WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 50`
      ).bind(tenant.tenantId).all<{ id: string; tier: string; status: string; current_period_start: string | null; created_at: string }>(),
    ]);

    const purchaseInvoices = (txResult.results ?? []).map((tx) => {
      let meta: Record<string, unknown> = {};
      try { meta = JSON.parse(tx.metadata ?? '{}'); } catch { /* ignore */ }
      const amt = (meta.price_cents as number) ?? Math.abs(tx.amount) * 500;
      const desc = tx.description ?? 'Credit purchase';
      return { id: `inv-${tx.id}`, date: tx.created_at.slice(0, 10), amount: amt, currency: 'usd', status: 'paid', description: desc, items: [{ description: desc, amount: amt }] };
    });

    const subInvoices = (subResult.results ?? []).map((sub) => {
      const price = TIER_PRICE[sub.tier] ?? 0;
      const desc = `${capitalize(sub.tier)} Plan - ${formatPeriod(sub.current_period_start)}`;
      return { id: `inv-sub-${sub.id}`, date: (sub.current_period_start ?? sub.created_at).slice(0, 10), amount: price, currency: 'usd', status: sub.status === 'active' ? 'paid' : sub.status, description: desc, items: [{ description: `${sub.tier} subscription`, amount: price }] };
    });

    const invoices = [...subInvoices, ...purchaseInvoices].sort((a, b) => b.date.localeCompare(a.date));
    return json({ invoices });
  } catch {
    return json({ error: 'Failed to fetch invoices', code: 'FETCH_FAILED' }, { status: 500 });
  }
});

/**
 * GET /v1/invoices/:id — Single invoice detail.
 * Resolves inv-sub-<subId> or inv-<txnId>.
 */
usageExport.get('/:id', async (c) => {
  const tenant = getTenant(c);
  const invoiceId = c.req.param('id');
  try {
    if (invoiceId.startsWith('inv-sub-')) {
      const sub = await c.env.DB.prepare(
        'SELECT id, tier, status, current_period_start, current_period_end, credits_per_period, created_at FROM subscriptions WHERE id = ? AND tenant_id = ?'
      ).bind(invoiceId.replace('inv-sub-', ''), tenant.tenantId).first<{
        id: string; tier: string; status: string; current_period_start: string | null;
        current_period_end: string | null; credits_per_period: number; created_at: string;
      }>();
      if (!sub) return json({ error: 'Invoice not found' }, { status: 404 });
      const price = TIER_PRICE[sub.tier] ?? 0;
      const desc = `${capitalize(sub.tier)} Plan - ${formatPeriod(sub.current_period_start)}`;
      return json({ id: invoiceId, date: (sub.current_period_start ?? sub.created_at).slice(0, 10), amount: price, currency: 'usd', status: sub.status === 'active' ? 'paid' : sub.status, description: desc, items: [{ description: `${sub.tier} subscription`, amount: price }], period: { start: sub.current_period_start, end: sub.current_period_end }, creditsIncluded: sub.credits_per_period });
    }

    const tx = await c.env.DB.prepare(
      `SELECT id, amount, description, metadata, created_at FROM credit_transactions
       WHERE id = ? AND tenant_id = ? AND type = 'purchase'`
    ).bind(invoiceId.replace(/^inv-/, ''), tenant.tenantId).first<{
      id: string; amount: number; description: string | null; metadata: string | null; created_at: string;
    }>();
    if (!tx) return json({ error: 'Invoice not found' }, { status: 404 });

    let meta: Record<string, unknown> = {};
    try { meta = JSON.parse(tx.metadata ?? '{}'); } catch { /* ignore */ }
    const amt = (meta.price_cents as number) ?? Math.abs(tx.amount) * 500;
    const desc = tx.description ?? 'Credit purchase';
    return json({ id: invoiceId, date: tx.created_at.slice(0, 10), amount: amt, currency: 'usd', status: 'paid', description: desc, items: [{ description: desc, amount: amt }], credits: Math.abs(tx.amount) });
  } catch {
    return json({ error: 'Failed to fetch invoice', code: 'FETCH_FAILED' }, { status: 500 });
  }
});
