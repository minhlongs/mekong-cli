/**
 * Tenant Invoicing routes — invoice CRUD, line items, payment status, and admin overview
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { auth, getTenant } from '../middleware/auth';
import {
  createInvoice,
  listInvoices,
  getInvoice,
  addLineItem,
  updateInvoiceStatus,
  calculateInvoiceTotal,
  getInvoiceSummary,
  getOverdueInvoices,
  getAdminInvoiceOverview,
} from '../services/tenant-invoicing-service';

export const tenantInvoicing = new Hono<{ Bindings: Env }>();

const VALID_STATUSES = new Set(['draft', 'sent', 'paid', 'overdue', 'cancelled', 'refunded']);

/** GET /invoices — list invoices for authenticated tenant */
tenantInvoicing.get('/invoices', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const status = c.req.query('status');
    const invoices = await listInvoices(c.env.DB, tenant.tenantId, status);
    return json({ invoices, count: invoices.length });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /invoices — create a new invoice with optional line items */
tenantInvoicing.post('/invoices', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json().catch(() => ({}));
    const invoice = await createInvoice(c.env.DB, tenant.tenantId, body);
    return json({ invoice }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /invoices/:invoiceId — get invoice with line items */
tenantInvoicing.get('/invoices/:invoiceId', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const invoiceId = c.req.param('invoiceId');
    const invoice = await getInvoice(c.env.DB, invoiceId, tenant.tenantId);
    if (!invoice) {
      return json({ error: 'Invoice not found' }, { status: 404 });
    }
    return json({ invoice });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /invoices/:invoiceId/items — add a line item to an invoice */
tenantInvoicing.post('/invoices/:invoiceId/items', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const invoiceId = c.req.param('invoiceId');

    // Verify ownership
    const existing = await getInvoice(c.env.DB, invoiceId, tenant.tenantId);
    if (!existing) {
      return json({ error: 'Invoice not found' }, { status: 404 });
    }

    const body = await c.req.json().catch(() => ({}));
    if (!body.description || body.unit_price === undefined) {
      return json({ error: 'description and unit_price are required' }, { status: 400 });
    }

    await addLineItem(c.env.DB, invoiceId, body);
    const totals = await calculateInvoiceTotal(c.env.DB, invoiceId);
    return json({ added: true, invoiceId, totals }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** PUT /invoices/:invoiceId/status — update invoice status */
tenantInvoicing.put('/invoices/:invoiceId/status', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const invoiceId = c.req.param('invoiceId');
    const body = await c.req.json().catch(() => ({}));
    const { status, payment_reference } = body;

    if (!status || !VALID_STATUSES.has(status)) {
      return json({ error: `status must be one of: ${[...VALID_STATUSES].join(', ')}` }, { status: 400 });
    }

    const updated = await updateInvoiceStatus(c.env.DB, invoiceId, tenant.tenantId, status, payment_reference);
    if (!updated) {
      return json({ error: 'Invoice not found' }, { status: 404 });
    }
    return json({ updated: true, invoiceId, status });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /invoices/:invoiceId/recalculate — recalculate invoice totals from line items */
tenantInvoicing.post('/invoices/:invoiceId/recalculate', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const invoiceId = c.req.param('invoiceId');

    const existing = await getInvoice(c.env.DB, invoiceId, tenant.tenantId);
    if (!existing) {
      return json({ error: 'Invoice not found' }, { status: 404 });
    }

    const totals = await calculateInvoiceTotal(c.env.DB, invoiceId);
    return json({ recalculated: true, invoiceId, totals });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /summary — invoice summary for tenant */
tenantInvoicing.get('/summary', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const summary = await getInvoiceSummary(c.env.DB, tenant.tenantId);
    return json(summary);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /admin/overview — platform revenue stats (admin only) */
tenantInvoicing.get('/admin/overview', async (c) => {
  try {
    if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
      return json({ error: 'Unauthorized' }, { status: 401 });
    }
    const overview = await getAdminInvoiceOverview(c.env.DB);
    return json(overview);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /admin/overdue — all overdue invoices platform-wide (admin only) */
tenantInvoicing.get('/admin/overdue', async (c) => {
  try {
    if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
      return json({ error: 'Unauthorized' }, { status: 401 });
    }
    const invoices = await getOverdueInvoices(c.env.DB);
    return json({ invoices, count: invoices.length });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});
