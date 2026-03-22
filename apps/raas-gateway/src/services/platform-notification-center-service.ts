/**
 * Platform Notification Center Service
 * Handles CRUD for notifications, preferences, templates, and admin overview
 */

// D1Database provided by @cloudflare/workers-types (ambient)

const listNotifications = async (
  db: D1Database,
  tenantId: string,
  filters?: { status?: string; channel?: string; limit?: number; offset?: number }
) => {
  const limit = filters?.limit ?? 50;
  const offset = filters?.offset ?? 0;
  let query = 'SELECT * FROM notifications WHERE tenant_id = ?';
  const params: any[] = [tenantId];

  if (filters?.status) {
    query += ' AND status = ?';
    params.push(filters.status);
  }
  if (filters?.channel) {
    query += ' AND channel = ?';
    params.push(filters.channel);
  }

  query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?';
  params.push(limit, offset);

  const results = await db.prepare(query).bind(...params).all();
  const countQuery = 'SELECT COUNT(*) as total FROM notifications WHERE tenant_id = ?';
  const countResult = await db.prepare(countQuery).bind(tenantId).first<{ total: number }>();

  return { notifications: results.results, total: countResult?.total ?? 0, limit, offset };
};

const getNotification = async (db: D1Database, tenantId: string, id: string) => {
  return db
    .prepare('SELECT * FROM notifications WHERE id = ? AND tenant_id = ?')
    .bind(id, tenantId)
    .first();
};

const createNotification = async (db: D1Database, tenantId: string, data: {
  title: string;
  body?: string;
  notification_type?: string;
  channel?: string;
}) => {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO notifications (id, tenant_id, title, body, notification_type, channel, status, created_at)
       VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)`
    )
    .bind(
      id,
      tenantId,
      data.title,
      data.body ?? null,
      data.notification_type ?? 'info',
      data.channel ?? 'in_app',
      now
    )
    .run();
  return { id, tenantId, ...data, status: 'pending', created_at: now };
};

const markAsRead = async (db: D1Database, tenantId: string, id: string) => {
  const now = new Date().toISOString();
  const result = await db
    .prepare(
      `UPDATE notifications SET status = 'read', read_at = ?
       WHERE id = ? AND tenant_id = ? AND status != 'read'`
    )
    .bind(now, id, tenantId)
    .run();
  return { success: result.meta.changes > 0, id };
};

const markAllAsRead = async (db: D1Database, tenantId: string) => {
  const now = new Date().toISOString();
  const result = await db
    .prepare(
      `UPDATE notifications SET status = 'read', read_at = ?
       WHERE tenant_id = ? AND status != 'read'`
    )
    .bind(now, tenantId)
    .run();
  return { success: true, updated: result.meta.changes };
};

const getPreferences = async (db: D1Database, tenantId: string) => {
  const results = await db
    .prepare('SELECT * FROM notification_preferences WHERE tenant_id = ? ORDER BY channel')
    .bind(tenantId)
    .all();
  return results.results;
};

const updatePreferences = async (db: D1Database, tenantId: string, channel: string, data: {
  enabled?: number;
  config_json?: string;
}) => {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO notification_preferences (id, tenant_id, channel, enabled, config_json, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(tenant_id, channel) DO UPDATE SET
         enabled = excluded.enabled,
         config_json = excluded.config_json,
         updated_at = excluded.updated_at`
    )
    .bind(
      id,
      tenantId,
      channel,
      data.enabled ?? 1,
      data.config_json ?? '{}',
      now,
      now
    )
    .run();
  return { tenantId, channel, ...data, updated_at: now };
};

const listTemplates = async (db: any) => {
  const results = await db
    .prepare('SELECT * FROM notification_templates ORDER BY template_type, name')
    .all();
  return results.results;
};

const getAdminOverview = async (db: D1Database) => {
  const [total, unread, byType, byChannel] = await Promise.all([
    db.prepare('SELECT COUNT(*) as count FROM notifications').first<{ count: number }>(),
    db.prepare("SELECT COUNT(*) as count FROM notifications WHERE status != 'read'").first<{ count: number }>(),
    db.prepare(
      'SELECT notification_type, COUNT(*) as count FROM notifications GROUP BY notification_type'
    ).all(),
    db.prepare(
      'SELECT channel, COUNT(*) as count FROM notifications GROUP BY channel'
    ).all(),
  ]);
  return {
    total: total?.count ?? 0,
    unread: unread?.count ?? 0,
    by_type: byType.results,
    by_channel: byChannel.results,
  };
};

export const notificationCenterService = {
  listNotifications,
  getNotification,
  createNotification,
  markAsRead,
  markAllAsRead,
  getPreferences,
  updatePreferences,
  listTemplates,
  getAdminOverview,
};
