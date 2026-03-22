/**
 * Tenant Billing History routes — invoices, payments, statements
 * Mounted at /v1/billing in parent router
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import * as svc from '../services/tenant-billing-history-service';
import type { InvoiceStatus } from '../services/tenant-billing-history-service';

const app = new Hono<{ Bindings: Env }>();

// GET /invoices — list invoices with optional ?status= filter
app.get('/invoices', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const status = c.req.query('status') as InvoiceStatus | undefined;
    const data = await svc.listInvoices(c.env.DB, tenantId, { status });
    return c.json({ success: true, data, total: data.length });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /invoices/:id — get single invoice
app.get('/invoices/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const invoice = await svc.getInvoice(c.env.DB, tenantId, c.req.param('id'));
    if (!invoice) return c.json({ success: false, error: 'Invoice not found' }, 404);
    return c.json({ success: true, data: invoice });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /invoices — create invoice
app.post('/invoices', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      amount_cents?: number;
      currency?: string;
      period_start?: string;
      period_end?: string;
      line_items?: unknown[];
      invoice_number?: string;
    }>();

    if (!body.amount_cents || !body.period_start || !body.period_end) {
      return c.json({ success: false, error: 'amount_cents, period_start, period_end required' }, 400);
    }

    const invoice = await svc.createInvoice(c.env.DB, tenantId, {
      amount_cents: body.amount_cents,
      currency: body.currency,
      period_start: body.period_start,
      period_end: body.period_end,
      line_items: body.line_items,
      invoice_number: body.invoice_number,
    });
    return c.json({ success: true, data: invoice }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /invoices/:id/void — void invoice
app.post('/invoices/:id/void', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const invoice = await svc.voidInvoice(c.env.DB, tenantId, c.req.param('id'));
    if (!invoice) return c.json({ success: false, error: 'Invoice not found or cannot be voided' }, 404);
    return c.json({ success: true, data: invoice });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /payments — list payments
app.get('/payments', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listPayments(c.env.DB, tenantId);
    return c.json({ success: true, data, total: data.length });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /payments — record payment
app.post('/payments', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      invoice_id?: string;
      amount_cents?: number;
      currency?: string;
      payment_method?: string;
      provider_ref?: string;
      status?: string;
    }>();

    if (!body.invoice_id || !body.amount_cents) {
      return c.json({ success: false, error: 'invoice_id and amount_cents required' }, 400);
    }

    const payment = await svc.recordPayment(c.env.DB, tenantId, body.invoice_id, {
      amount_cents: body.amount_cents,
      currency: body.currency,
      payment_method: body.payment_method,
      provider_ref: body.provider_ref,
      status: body.status as svc.PaymentStatus | undefined,
    });
    return c.json({ success: true, data: payment }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /statements/:month — get statement (format: YYYY-MM)
app.get('/statements/:month', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const statement = await svc.getStatement(c.env.DB, tenantId, c.req.param('month'));
    if (!statement) return c.json({ success: false, error: 'Statement not found' }, 404);
    return c.json({ success: true, data: statement });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /statements/generate — generate monthly statement
app.post('/statements/generate', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ month?: string }>();
    if (!body.month || !/^\d{4}-\d{2}$/.test(body.month)) {
      return c.json({ success: false, error: 'month required in YYYY-MM format' }, 400);
    }
    const statement = await svc.generateStatement(c.env.DB, tenantId, body.month);
    return c.json({ success: true, data: statement });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /admin/overview — admin billing stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    if (!key || key !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as tenantBillingHistory };
