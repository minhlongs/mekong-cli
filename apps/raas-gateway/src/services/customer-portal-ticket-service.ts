/**
 * Customer Portal Ticket Service — CRUD for support tickets and activity log
 */

// D1Database provided by @cloudflare/workers-types (ambient)

/** Create a new support ticket */
export async function createTicket(
  db: D1Database,
  tenantId: string,
  opts: { subject: string; description: string; priority?: string; category?: string }
) {
  const id = crypto.randomUUID();
  const priority = opts.priority ?? 'medium';
  const category = opts.category ?? 'general';

  await db.prepare(
    `INSERT INTO support_tickets (id, tenant_id, subject, description, priority, category)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, opts.subject, opts.description, priority, category).run();

  return { id, subject: opts.subject, priority, category, status: 'open' };
}

/** List tickets for tenant, optionally filtered by status */
export async function getTickets(
  db: D1Database,
  tenantId: string,
  opts: { status?: string; limit?: number } = {}
) {
  const limit = Math.min(opts.limit ?? 20, 100);
  const rows = opts.status
    ? await db.prepare(
        `SELECT id, subject, priority, status, category, created_at, updated_at
         FROM support_tickets WHERE tenant_id = ? AND status = ? ORDER BY created_at DESC LIMIT ?`
      ).bind(tenantId, opts.status, limit).all()
    : await db.prepare(
        `SELECT id, subject, priority, status, category, created_at, updated_at
         FROM support_tickets WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?`
      ).bind(tenantId, limit).all();

  return rows.results ?? [];
}

/** Get single ticket with full message thread */
export async function getTicket(db: D1Database, tenantId: string, ticketId: string) {
  const ticket = await db.prepare(
    `SELECT id, subject, description, priority, status, category, messages, created_at, updated_at
     FROM support_tickets WHERE id = ? AND tenant_id = ?`
  ).bind(ticketId, tenantId).first<{ id: string; messages: string; [key: string]: unknown }>();

  if (!ticket) throw new Error('Ticket not found');
  return { ...ticket, messages: JSON.parse(ticket.messages as string) };
}

/** Append a message to ticket thread */
export async function addTicketMessage(
  db: D1Database,
  tenantId: string,
  ticketId: string,
  opts: { message: string; sender: string }
) {
  const ticket = await db.prepare(
    `SELECT messages FROM support_tickets WHERE id = ? AND tenant_id = ?`
  ).bind(ticketId, tenantId).first<{ messages: string }>();

  if (!ticket) throw new Error('Ticket not found');

  const messages: unknown[] = JSON.parse(ticket.messages);
  const entry = {
    id: crypto.randomUUID(),
    sender: opts.sender,
    message: opts.message,
    created_at: new Date().toISOString(),
  };
  messages.push(entry);

  await db.prepare(
    `UPDATE support_tickets SET messages = ?, updated_at = datetime('now') WHERE id = ? AND tenant_id = ?`
  ).bind(JSON.stringify(messages), ticketId, tenantId).run();

  return entry;
}

/** Update ticket status */
export async function updateTicketStatus(
  db: D1Database,
  tenantId: string,
  ticketId: string,
  status: string
) {
  const result = await db.prepare(
    `UPDATE support_tickets SET status = ?, updated_at = datetime('now')
     WHERE id = ? AND tenant_id = ?`
  ).bind(status, ticketId, tenantId).run();

  if (!result.meta.changes) throw new Error('Ticket not found');
  return { id: ticketId, status };
}

/** Recent portal activity log */
export async function getActivityLog(
  db: D1Database,
  tenantId: string,
  opts: { limit?: number } = {}
) {
  const limit = Math.min(opts.limit ?? 20, 100);
  const rows = await db.prepare(
    `SELECT id, action, details, ip_address, created_at FROM portal_activity
     WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?`
  ).bind(tenantId, limit).all();

  return rows.results ?? [];
}

/** Log a portal action */
export async function logActivity(
  db: D1Database,
  tenantId: string,
  action: string,
  details: Record<string, unknown> = {},
  ipAddress?: string
) {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO portal_activity (id, tenant_id, action, details, ip_address) VALUES (?, ?, ?, ?, ?)`
  ).bind(id, tenantId, action, JSON.stringify(details), ipAddress ?? null).run();
}
