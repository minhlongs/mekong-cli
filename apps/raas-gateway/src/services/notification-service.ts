/**
 * Notification Service — send, track, and manage notifications across channels
 * Supports in_app, email, push, webhook channels with template rendering
 */

import type { D1Database } from '@cloudflare/workers-types';
import { mapNotification, mapPreference } from './notification-types';
import type {
  Notification,
  NotificationPreference,
  NotificationChannel,
  SendNotificationInput,
  ListNotificationsOptions,
  UpdatePreferenceInput,
} from './notification-types';

// Re-export types for consumers
export type {
  Notification,
  NotificationTemplate,
  NotificationPreference,
  NotificationChannel,
  NotificationStatus,
  SendNotificationInput,
  ListNotificationsOptions,
  CreateTemplateInput,
  SendFromTemplateInput,
  UpdatePreferenceInput,
} from './notification-types';

// Re-export template functions
export { createTemplate, getTemplates, sendFromTemplate } from './notification-template-service';

/** Insert a notification record and return it */
export async function sendNotification(
  db: D1Database,
  tenantId: string,
  input: SendNotificationInput
): Promise<Notification> {
  const id = crypto.randomUUID();
  const metadata = JSON.stringify(input.metadata ?? {});

  await db
    .prepare(
      `INSERT INTO notifications (id, tenant_id, template_id, channel, recipient, subject, body, status, metadata)
       VALUES (?, ?, ?, ?, ?, ?, ?, 'sent', ?)`
    )
    .bind(id, tenantId, input.templateId ?? null, input.channel, input.recipient, input.subject ?? null, input.body, metadata)
    .run();

  const row = await db
    .prepare('SELECT * FROM notifications WHERE id = ?')
    .bind(id)
    .first<Record<string, unknown>>();

  return mapNotification(row!);
}

/** List notifications for a tenant with optional status filter and pagination */
export async function getNotifications(
  db: D1Database,
  tenantId: string,
  options: ListNotificationsOptions = {}
): Promise<{ notifications: Notification[]; total: number }> {
  const limit = Math.min(options.limit ?? 20, 100);
  const offset = options.offset ?? 0;

  const hasStatus = Boolean(options.status);
  const whereClause = hasStatus ? 'WHERE tenant_id = ? AND status = ?' : 'WHERE tenant_id = ?';
  const bindings: unknown[] = hasStatus ? [tenantId, options.status] : [tenantId];

  const [rows, countRow] = await Promise.all([
    db
      .prepare(`SELECT * FROM notifications ${whereClause} ORDER BY created_at DESC LIMIT ? OFFSET ?`)
      .bind(...bindings, limit, offset)
      .all<Record<string, unknown>>(),
    db
      .prepare(`SELECT COUNT(*) as count FROM notifications ${whereClause}`)
      .bind(...bindings)
      .first<{ count: number }>(),
  ]);

  return {
    notifications: rows.results.map(mapNotification),
    total: countRow?.count ?? 0,
  };
}

/** Mark a single notification as read */
export async function markAsRead(
  db: D1Database,
  tenantId: string,
  notificationId: string
): Promise<boolean> {
  const result = await db
    .prepare(
      `UPDATE notifications SET status = 'read', read_at = datetime('now')
       WHERE id = ? AND tenant_id = ? AND status != 'read'`
    )
    .bind(notificationId, tenantId)
    .run();

  return (result.meta.changes ?? 0) > 0;
}

/** Mark all unread notifications as read for a tenant */
export async function markAllRead(db: D1Database, tenantId: string): Promise<number> {
  const result = await db
    .prepare(
      `UPDATE notifications SET status = 'read', read_at = datetime('now')
       WHERE tenant_id = ? AND status != 'read'`
    )
    .bind(tenantId)
    .run();

  return result.meta.changes ?? 0;
}

/** Count unread notifications for a tenant */
export async function getUnreadCount(db: D1Database, tenantId: string): Promise<number> {
  const row = await db
    .prepare(`SELECT COUNT(*) as count FROM notifications WHERE tenant_id = ? AND status != 'read'`)
    .bind(tenantId)
    .first<{ count: number }>();

  return row?.count ?? 0;
}

/** Get all notification preferences for a tenant */
export async function getPreferences(db: D1Database, tenantId: string): Promise<NotificationPreference[]> {
  const rows = await db
    .prepare('SELECT * FROM notification_preferences WHERE tenant_id = ?')
    .bind(tenantId)
    .all<Record<string, unknown>>();

  return rows.results.map(mapPreference);
}

/** Upsert notification preference for a specific channel */
export async function updatePreferences(
  db: D1Database,
  tenantId: string,
  channel: NotificationChannel,
  input: UpdatePreferenceInput
): Promise<NotificationPreference> {
  const id = crypto.randomUUID();

  await db
    .prepare(
      `INSERT INTO notification_preferences (id, tenant_id, channel, enabled, quiet_hours_start, quiet_hours_end)
       VALUES (?, ?, ?, ?, ?, ?)
       ON CONFLICT(tenant_id, channel) DO UPDATE SET
         enabled = excluded.enabled,
         quiet_hours_start = excluded.quiet_hours_start,
         quiet_hours_end = excluded.quiet_hours_end,
         updated_at = datetime('now')`
    )
    .bind(id, tenantId, channel, input.enabled ? 1 : 0, input.quietHoursStart ?? null, input.quietHoursEnd ?? null)
    .run();

  const row = await db
    .prepare('SELECT * FROM notification_preferences WHERE tenant_id = ? AND channel = ?')
    .bind(tenantId, channel)
    .first<Record<string, unknown>>();

  return mapPreference(row!);
}
