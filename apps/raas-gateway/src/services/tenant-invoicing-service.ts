/**
 * Tenant Invoicing Service — invoice creation, line items, payment tracking, and tenant summary
 * Admin queries: see tenant-invoicing-admin-queries.ts
 */

import type { D1Database } from '@cloudflare/workers-types';
export { getInvoiceSummary, getOverdueInvoices, getAdminInvoiceOverview } from './tenant-invoicing-admin-queries';

export interface InvoiceData {
  currency?: string;
  billing_period_start?: string;
  billing_period_end?: string;
  due_date?: string;
  notes?: string;
  metadata?: Record<string, unknown>;
  line_items?: LineItemInput[];
}

export interface LineItemInput {
  description: string;
  quantity?: number;
  unit_price: number; // cents
  item_type?: string;
  reference_id?: string;
  metadata?: Record<string, unknown>;
}

/** Generate sequential invoice number: INV-YYYYMM-XXXX */
export async function generateInvoiceNumber(db: D1Database): Promise<string> {
  const ym = new Date().toISOString().slice(0, 7).replace('-', '');
  const row = await db
    .prepare(`SELECT COUNT(*) as cnt FROM invoices WHERE invoice_number LIKE ?`)
    .bind(`INV-${ym}-%`)
    .first<{ cnt: number }>();
  const seq = String((row?.cnt ?? 0) + 1).padStart(4, '0');
  return `INV-${ym}-${seq}`;
}

/** Create invoice with optional line items; returns full invoice object */
export async function createInvoice(
  db: D1Database,
  tenantId: string,
  data: InvoiceData
) {
  const invoiceNumber = await generateInvoiceNumber(db);
  const now = new Date().toISOString();
  const meta = JSON.stringify(data.metadata ?? {});

  await db
    .prepare(
      `INSERT INTO invoices
        (tenant_id, invoice_number, currency, billing_period_start, billing_period_end,
         due_date, notes, metadata, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(
      tenantId,
      invoiceNumber,
      data.currency ?? 'USD',
      data.billing_period_start ?? null,
      data.billing_period_end ?? null,
      data.due_date ?? null,
      data.notes ?? null,
      meta,
      now,
      now
    )
    .run();

  const invoice = await db
    .prepare(`SELECT * FROM invoices WHERE invoice_number = ?`)
    .bind(invoiceNumber)
    .first();

  // Insert line items if provided
  if (data.line_items?.length && invoice) {
    const inv = invoice as { id: string };
    for (const item of data.line_items) {
      await addLineItem(db, inv.id, item);
    }
    await calculateInvoiceTotal(db, inv.id);
    return db.prepare(`SELECT * FROM invoices WHERE id = ?`).bind(inv.id).first();
  }

  return invoice;
}

/** List invoices for tenant, optionally filtered by status */
export async function listInvoices(
  db: D1Database,
  tenantId: string,
  status?: string
) {
  if (status) {
    const { results } = await db
      .prepare(`SELECT * FROM invoices WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT 100`)
      .bind(tenantId, status)
      .all();
    return results;
  }
  const { results } = await db
    .prepare(`SELECT * FROM invoices WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 100`)
    .bind(tenantId)
    .all();
  return results;
}

/** Get invoice with its line items */
export async function getInvoice(db: D1Database, invoiceId: string, tenantId: string) {
  const invoice = await db
    .prepare(`SELECT * FROM invoices WHERE id = ? AND tenant_id = ?`)
    .bind(invoiceId, tenantId)
    .first();
  if (!invoice) return null;

  const { results: line_items } = await db
    .prepare(`SELECT * FROM invoice_line_items WHERE invoice_id = ? ORDER BY created_at ASC`)
    .bind(invoiceId)
    .all();

  return { ...invoice, line_items };
}

/** Add a single line item to an existing invoice */
export async function addLineItem(db: D1Database, invoiceId: string, item: LineItemInput) {
  const qty = item.quantity ?? 1;
  const amount = Math.round(qty * item.unit_price);
  const now = new Date().toISOString();

  await db
    .prepare(
      `INSERT INTO invoice_line_items
        (invoice_id, description, quantity, unit_price, amount, item_type, reference_id, metadata, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(
      invoiceId,
      item.description,
      qty,
      item.unit_price,
      amount,
      item.item_type ?? 'usage',
      item.reference_id ?? null,
      JSON.stringify(item.metadata ?? {}),
      now
    )
    .run();
}

/** Recalculate invoice totals from line items (sum of non-tax items = subtotal) */
export async function calculateInvoiceTotal(db: D1Database, invoiceId: string) {
  const row = await db
    .prepare(
      `SELECT
         COALESCE(SUM(CASE WHEN item_type != 'tax' THEN amount ELSE 0 END), 0) as subtotal,
         COALESCE(SUM(CASE WHEN item_type = 'tax' THEN amount ELSE 0 END), 0) as tax_amount
       FROM invoice_line_items WHERE invoice_id = ?`
    )
    .bind(invoiceId)
    .first<{ subtotal: number; tax_amount: number }>();

  const subtotal = row?.subtotal ?? 0;
  const taxAmount = row?.tax_amount ?? 0;
  const total = subtotal + taxAmount;
  const now = new Date().toISOString();

  await db
    .prepare(
      `UPDATE invoices SET subtotal = ?, tax_amount = ?, total = ?, updated_at = ? WHERE id = ?`
    )
    .bind(subtotal, taxAmount, total, now, invoiceId)
    .run();

  return { subtotal, tax_amount: taxAmount, total };
}

/** Update invoice status; optionally record payment reference and paid_at timestamp */
export async function updateInvoiceStatus(
  db: D1Database,
  invoiceId: string,
  tenantId: string,
  status: string,
  paymentRef?: string
) {
  const now = new Date().toISOString();
  const paidAt = status === 'paid' ? now : null;

  const result = await db
    .prepare(
      `UPDATE invoices
       SET status = ?, payment_reference = COALESCE(?, payment_reference),
           paid_at = COALESCE(?, paid_at), updated_at = ?
       WHERE id = ? AND tenant_id = ?`
    )
    .bind(status, paymentRef ?? null, paidAt, now, invoiceId, tenantId)
    .run();

  return result.meta.changes > 0;
}
