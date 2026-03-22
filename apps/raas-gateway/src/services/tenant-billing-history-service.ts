/**
 * Tenant Billing History Service — invoices, payments, monthly statements
 */

import type { D1Database } from '@cloudflare/workers-types';

export type InvoiceStatus = 'draft' | 'sent' | 'paid' | 'overdue' | 'void';
export type PaymentStatus = 'success' | 'failed' | 'refunded';

export interface Invoice {
  id: string; tenant_id: string; invoice_number: string;
  amount_cents: number; currency: string; status: InvoiceStatus;
  period_start: string; period_end: string; line_items_json: string;
  issued_at: string | null; paid_at: string | null; created_at: string;
}

export interface Payment {
  id: string; tenant_id: string; invoice_id: string;
  amount_cents: number; currency: string; payment_method: string;
  provider_ref: string | null; status: PaymentStatus;
  paid_at: string; created_at: string;
}

export interface Statement {
  id: string; tenant_id: string; statement_month: string;
  total_charges_cents: number; total_payments_cents: number;
  balance_cents: number; generated_at: string; created_at: string;
}

export interface CreateInvoiceInput {
  invoice_number?: string; amount_cents: number; currency?: string;
  period_start: string; period_end: string; line_items?: unknown[];
}

export interface RecordPaymentInput {
  amount_cents: number; currency?: string;
  payment_method?: string; provider_ref?: string; status?: PaymentStatus;
}

/** List invoices with optional status filter */
export async function listInvoices(db: D1Database, tenantId: string, filters: { status?: InvoiceStatus }): Promise<Invoice[]> {
  const sql = filters.status
    ? 'SELECT * FROM billing_invoices WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC'
    : 'SELECT * FROM billing_invoices WHERE tenant_id = ? ORDER BY created_at DESC';
  const stmt = filters.status ? db.prepare(sql).bind(tenantId, filters.status) : db.prepare(sql).bind(tenantId);
  return (await stmt.all<Invoice>()).results;
}

/** Get single invoice by ID */
export async function getInvoice(db: D1Database, tenantId: string, invoiceId: string): Promise<Invoice | null> {
  return db.prepare('SELECT * FROM billing_invoices WHERE id = ? AND tenant_id = ?').bind(invoiceId, tenantId).first<Invoice>();
}

/** Create a new invoice */
export async function createInvoice(db: D1Database, tenantId: string, data: CreateInvoiceInput): Promise<Invoice> {
  const id = crypto.randomUUID();
  const invoiceNumber = data.invoice_number ?? `INV-${Date.now()}`;
  await db.prepare(
    `INSERT INTO billing_invoices (id, tenant_id, invoice_number, amount_cents, currency, period_start, period_end, line_items_json, issued_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
  ).bind(id, tenantId, invoiceNumber, data.amount_cents, data.currency ?? 'USD', data.period_start, data.period_end, JSON.stringify(data.line_items ?? [])).run();
  return (await getInvoice(db, tenantId, id))!;
}

/** Void an invoice — cannot void a paid invoice */
export async function voidInvoice(db: D1Database, tenantId: string, invoiceId: string): Promise<Invoice | null> {
  const invoice = await getInvoice(db, tenantId, invoiceId);
  if (!invoice || invoice.status === 'paid') return null;
  await db.prepare("UPDATE billing_invoices SET status = 'void' WHERE id = ? AND tenant_id = ?").bind(invoiceId, tenantId).run();
  return getInvoice(db, tenantId, invoiceId);
}

/** List all payments for tenant */
export async function listPayments(db: D1Database, tenantId: string): Promise<Payment[]> {
  return (await db.prepare('SELECT * FROM billing_payments WHERE tenant_id = ? ORDER BY paid_at DESC').bind(tenantId).all<Payment>()).results;
}

/** Record a payment against an invoice; marks invoice paid on success */
export async function recordPayment(db: D1Database, tenantId: string, invoiceId: string, data: RecordPaymentInput): Promise<Payment> {
  const id = crypto.randomUUID();
  const status = data.status ?? 'success';
  await db.prepare(
    'INSERT INTO billing_payments (id, tenant_id, invoice_id, amount_cents, currency, payment_method, provider_ref, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
  ).bind(id, tenantId, invoiceId, data.amount_cents, data.currency ?? 'USD', data.payment_method ?? 'card', data.provider_ref ?? null, status).run();
  if (status === 'success') {
    await db.prepare("UPDATE billing_invoices SET status = 'paid', paid_at = datetime('now') WHERE id = ? AND tenant_id = ?").bind(invoiceId, tenantId).run();
  }
  return (await db.prepare('SELECT * FROM billing_payments WHERE id = ?').bind(id).first<Payment>())!;
}

/** Get monthly statement for tenant (month: YYYY-MM) */
export async function getStatement(db: D1Database, tenantId: string, month: string): Promise<Statement | null> {
  return db.prepare('SELECT * FROM billing_statements WHERE tenant_id = ? AND statement_month = ?').bind(tenantId, month).first<Statement>();
}

/** Generate or regenerate a monthly statement */
export async function generateStatement(db: D1Database, tenantId: string, month: string): Promise<Statement> {
  const [year, mon] = month.split('-');
  const start = `${year}-${mon}-01`;
  const end = `${year}-${mon}-31`;
  const charges = ((await db.prepare(
    "SELECT COALESCE(SUM(amount_cents),0) as total FROM billing_invoices WHERE tenant_id = ? AND period_start >= ? AND period_end <= ? AND status != 'void'"
  ).bind(tenantId, start, end).first<{ total: number }>())?.total) ?? 0;
  const payments = ((await db.prepare(
    "SELECT COALESCE(SUM(amount_cents),0) as total FROM billing_payments WHERE tenant_id = ? AND status = 'success' AND paid_at >= ? AND paid_at <= ?"
  ).bind(tenantId, `${start} 00:00:00`, `${end} 23:59:59`).first<{ total: number }>())?.total) ?? 0;
  const balance = charges - payments;
  const existing = await getStatement(db, tenantId, month);
  if (existing) {
    await db.prepare(
      "UPDATE billing_statements SET total_charges_cents = ?, total_payments_cents = ?, balance_cents = ?, generated_at = datetime('now') WHERE id = ?"
    ).bind(charges, payments, balance, existing.id).run();
  } else {
    await db.prepare(
      'INSERT INTO billing_statements (id, tenant_id, statement_month, total_charges_cents, total_payments_cents, balance_cents) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(crypto.randomUUID(), tenantId, month, charges, payments, balance).run();
  }
  return (await getStatement(db, tenantId, month))!;
}

/** Admin overview — aggregate billing stats across all tenants */
export async function getAdminOverview(db: D1Database): Promise<Record<string, unknown>> {
  const [byStatus, payments, overdue, revenue] = await Promise.all([
    db.prepare('SELECT status, COUNT(*) as total FROM billing_invoices GROUP BY status').all<{ status: string; total: number }>(),
    db.prepare("SELECT COUNT(*) as total FROM billing_payments WHERE status = 'success'").first<{ total: number }>(),
    db.prepare("SELECT COUNT(*) as total FROM billing_invoices WHERE status = 'overdue'").first<{ total: number }>(),
    db.prepare("SELECT COALESCE(SUM(amount_cents),0) as total FROM billing_payments WHERE status = 'success'").first<{ total: number }>(),
  ]);
  return {
    invoices_by_status: byStatus.results,
    total_successful_payments: payments?.total ?? 0,
    total_revenue_cents: revenue?.total ?? 0,
    overdue_invoices: overdue?.total ?? 0,
  };
}
