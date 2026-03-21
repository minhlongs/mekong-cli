/**
 * Customer Portal — support ticket sub-routes
 * Registered on the main portal app under /tickets
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createTicket,
  getTickets,
  getTicket,
  addTicketMessage,
  updateTicketStatus,
  logActivity,
} from '../services/customer-portal-ticket-service';

const tickets = new Hono<{ Bindings: Env }>();

const VALID_STATUSES = ['open', 'in_progress', 'waiting', 'resolved', 'closed'];
const VALID_PRIORITIES = ['low', 'medium', 'high', 'urgent'];

/** POST / — create ticket */
tickets.post('/', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: { subject?: string; description?: string; priority?: string; category?: string };
  try { body = await c.req.json(); } catch {
    return c.json({ success: false, error: 'Invalid JSON body', code: 'INVALID_BODY' }, 400);
  }
  const { subject, description, priority, category } = body;
  if (!subject || !description)
    return c.json({ success: false, error: 'subject and description are required', code: 'MISSING_FIELDS' }, 400);
  if (priority && !VALID_PRIORITIES.includes(priority))
    return c.json({ success: false, error: `priority must be one of: ${VALID_PRIORITIES.join(', ')}`, code: 'INVALID_PRIORITY' }, 400);
  try {
    const data = await createTicket(c.env.DB, tenantId, { subject, description, priority, category });
    await logActivity(c.env.DB, tenantId, 'ticket.created', { ticketId: data.id, subject }, c.req.header('CF-Connecting-IP'));
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to create ticket', code: 'TICKET_CREATE_ERROR' }, 500);
  }
});

/** GET / — list tickets */
tickets.get('/', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const status = c.req.query('status');
  const limit = parseInt(c.req.query('limit') ?? '20', 10) || 20;
  if (status && !VALID_STATUSES.includes(status))
    return c.json({ success: false, error: `status must be one of: ${VALID_STATUSES.join(', ')}`, code: 'INVALID_STATUS' }, 400);
  try {
    const data = await getTickets(c.env.DB, tenantId, { status, limit });
    return c.json({ success: true, data, total: data.length });
  } catch (err: unknown) {
    return c.json({ success: false, error: err instanceof Error ? err.message : 'Failed to list tickets', code: 'TICKETS_ERROR' }, 500);
  }
});

/** GET /:id — ticket detail */
tickets.get('/:id', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const data = await getTicket(c.env.DB, tenantId, c.req.param('id'));
    return c.json({ success: true, data });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Ticket not found';
    return c.json({ success: false, error: msg, code: 'TICKET_ERROR' }, msg === 'Ticket not found' ? 404 : 500);
  }
});

/** POST /:id/messages — add message to thread */
tickets.post('/:id/messages', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: { message?: string; sender?: string };
  try { body = await c.req.json(); } catch {
    return c.json({ success: false, error: 'Invalid JSON body', code: 'INVALID_BODY' }, 400);
  }
  if (!body.message || !body.sender)
    return c.json({ success: false, error: 'message and sender are required', code: 'MISSING_FIELDS' }, 400);
  try {
    const data = await addTicketMessage(c.env.DB, tenantId, c.req.param('id'), { message: body.message, sender: body.sender });
    return c.json({ success: true, data }, 201);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to add message';
    return c.json({ success: false, error: msg, code: 'MESSAGE_ERROR' }, msg === 'Ticket not found' ? 404 : 500);
  }
});

/** PUT /:id/status — update ticket status */
tickets.put('/:id/status', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const ticketId = c.req.param('id');
  let body: { status?: string };
  try { body = await c.req.json(); } catch {
    return c.json({ success: false, error: 'Invalid JSON body', code: 'INVALID_BODY' }, 400);
  }
  if (!body.status || !VALID_STATUSES.includes(body.status))
    return c.json({ success: false, error: `status must be one of: ${VALID_STATUSES.join(', ')}`, code: 'INVALID_STATUS' }, 400);
  try {
    const data = await updateTicketStatus(c.env.DB, tenantId, ticketId, body.status);
    await logActivity(c.env.DB, tenantId, 'ticket.status.updated', { ticketId, status: body.status }, c.req.header('CF-Connecting-IP'));
    return c.json({ success: true, data });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Failed to update status';
    return c.json({ success: false, error: msg, code: 'STATUS_UPDATE_ERROR' }, msg === 'Ticket not found' ? 404 : 500);
  }
});

export { tickets as ticketRoutes };
