/**
 * Tenant Invoicing Queries — tenant summary, platform-wide stats, and overdue invoice retrieval
 */

import type { D1Database } from '@cloudflare/workers-types';

/** Invoice summary for tenant: total paid, outstanding, overdue amounts */
export async function getInvoiceSummary(db: D1Database, tenantId: string) {
  const row = await db
    .prepare(
      `SELECT
         COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as total_paid,
         COALESCE(SUM(CASE WHEN status IN ('draft','sent') THEN total ELSE 0 END), 0) as total_outstanding,
         COALESCE(SUM(CASE WHEN status = 'overdue' THEN total ELSE 0 END), 0) as total_overdue,
         COUNT(*) as invoice_count
       FROM invoices WHERE tenant_id = ?`
    )
    .bind(tenantId)
    .first<{ total_paid: number; total_outstanding: number; total_overdue: number; invoice_count: number }>();

  return {
    total_paid_cents: row?.total_paid ?? 0,
    total_outstanding_cents: row?.total_outstanding ?? 0,
    total_overdue_cents: row?.total_overdue ?? 0,
    invoice_count: row?.invoice_count ?? 0,
  };
}

/** Platform-wide list of overdue invoices */
export async function getOverdueInvoices(db: D1Database) {
  const { results } = await db
    .prepare(`SELECT * FROM invoices WHERE status = 'overdue' ORDER BY due_date ASC LIMIT 500`)
    .all();
  return results;
}

/** Admin platform revenue overview stats */
export async function getAdminInvoiceOverview(db: D1Database) {
  const row = await db
    .prepare(
      `SELECT
         COUNT(*) as total_invoices,
         COALESCE(SUM(CASE WHEN status = 'paid' THEN total ELSE 0 END), 0) as revenue_paid,
         COALESCE(SUM(CASE WHEN status = 'overdue' THEN total ELSE 0 END), 0) as revenue_overdue,
         COALESCE(SUM(CASE WHEN status IN ('draft','sent') THEN total ELSE 0 END), 0) as revenue_outstanding,
         COUNT(DISTINCT tenant_id) as active_tenants
       FROM invoices`
    )
    .first<{
      total_invoices: number;
      revenue_paid: number;
      revenue_overdue: number;
      revenue_outstanding: number;
      active_tenants: number;
    }>();

  return {
    total_invoices: row?.total_invoices ?? 0,
    revenue_paid_cents: row?.revenue_paid ?? 0,
    revenue_overdue_cents: row?.revenue_overdue ?? 0,
    revenue_outstanding_cents: row?.revenue_outstanding ?? 0,
    active_tenants: row?.active_tenants ?? 0,
  };
}
