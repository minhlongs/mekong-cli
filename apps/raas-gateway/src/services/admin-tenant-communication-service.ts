// Admin Tenant Communication Service — send messages to tenants, manage templates, dashboard

const nanoid = () => crypto.randomUUID();

/** List messages for a tenant, or all messages if no tenant_id given */
async function listMessages(
  db: any,
  tenantId?: string,
  messageType?: string,
  limit = 50
): Promise<unknown[]> {
  const conditions: string[] = [];
  const binds: unknown[] = [];

  if (tenantId) { conditions.push('tenant_id = ?'); binds.push(tenantId); }
  if (messageType) { conditions.push('message_type = ?'); binds.push(messageType); }

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  binds.push(Math.min(limit, 200));

  const rows = await db.prepare(
    `SELECT * FROM tenant_messages ${where} ORDER BY created_at DESC LIMIT ?`
  ).bind(...binds).all();
  return rows.results as unknown[];
}

/** Send a new message to a tenant */
async function createMessage(
  db: any,
  tenantId: string,
  subject: string,
  body: string,
  opts: {
    messageType?: string;
    priority?: string;
    sentBy?: string;
  } = {}
): Promise<unknown> {
  const id = nanoid();
  const now = new Date().toISOString();
  return db.prepare(
    `INSERT INTO tenant_messages (id, tenant_id, subject, body, message_type, priority, sent_by, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id,
    tenantId,
    subject,
    body,
    opts.messageType ?? 'info',
    opts.priority ?? 'normal',
    opts.sentBy ?? 'admin',
    now
  ).first();
}

/** List all templates, optionally filtered by category */
async function getTemplates(db: any, category?: string): Promise<unknown[]> {
  const rows = category
    ? await db.prepare(
        `SELECT * FROM tenant_message_templates WHERE category = ? ORDER BY template_name ASC`
      ).bind(category).all()
    : await db.prepare(
        `SELECT * FROM tenant_message_templates ORDER BY template_name ASC`
      ).all();
  return rows.results as unknown[];
}

/** Dashboard: message counts by type and priority, unread count */
async function getDashboard(db: any): Promise<unknown> {
  const [total, unread, highPriority, byType] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM tenant_messages`).first() as Promise<{ count: number } | null>,
    db.prepare(`SELECT COUNT(*) as count FROM tenant_messages WHERE read_at IS NULL`).first() as Promise<{ count: number } | null>,
    db.prepare(
      `SELECT COUNT(*) as count FROM tenant_messages WHERE priority IN ('high','urgent') AND read_at IS NULL`
    ).first() as Promise<{ count: number } | null>,
    db.prepare(
      `SELECT message_type, COUNT(*) as count FROM tenant_messages GROUP BY message_type`
    ).all(),
  ]);

  return {
    messages: {
      total: (total as any)?.count ?? 0,
      unread: (unread as any)?.count ?? 0,
      unreadHighPriority: (highPriority as any)?.count ?? 0,
      byType: byType.results as unknown[],
    },
  };
}

export const adminTenantCommunicationService = {
  listMessages,
  createMessage,
  getTemplates,
  getDashboard,
};
