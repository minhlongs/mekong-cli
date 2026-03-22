/**
 * Notifications Hub Service — channel management, dispatch, and log queries
 * Templates and seeding handled in notifications-hub-templates-service.ts
 */

import type { D1Database } from '@cloudflare/workers-types';
import { getTemplate } from './notifications-hub-templates-service';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface NotificationChannel {
  id: string;
  tenant_id: string;
  channel_type: string;
  config: string;
  is_active: number;
  created_at: string;
}

export interface NotificationLogEntry {
  id: string;
  tenant_id: string;
  channel_id: string | null;
  channel_type: string;
  event_type: string;
  subject: string | null;
  body: string | null;
  status: string;
  error: string | null;
  created_at: string;
  sent_at: string | null;
}

export interface NotificationStats {
  total: number;
  sent: number;
  failed: number;
  pending: number;
  by_channel: Record<string, number>;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

/** Interpolate {{key}} placeholders in template strings */
function render(template: string, data: Record<string, unknown>): string {
  return template.replace(/\{\{(\w+)\}\}/g, (_, k) => String(data[k] ?? ''));
}

// ── Channel Management ──────────────────────────────────────────────────────────

/** Register a new notification channel for a tenant */
export async function addChannel(
  db: D1Database,
  tenantId: string,
  channelType: string,
  config: Record<string, unknown>
): Promise<NotificationChannel> {
  const id = crypto.randomUUID();
  await db
    .prepare('INSERT INTO notification_channels (id, tenant_id, channel_type, config) VALUES (?, ?, ?, ?)')
    .bind(id, tenantId, channelType, JSON.stringify(config))
    .run();

  return (await db.prepare('SELECT * FROM notification_channels WHERE id = ?').bind(id).first<NotificationChannel>())!;
}

/** List all channels for a tenant */
export async function listChannels(db: D1Database, tenantId: string): Promise<NotificationChannel[]> {
  const rows = await db
    .prepare('SELECT * FROM notification_channels WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all<NotificationChannel>();
  return rows.results;
}

/** Update channel config or active state */
export async function updateChannel(
  db: D1Database,
  tenantId: string,
  channelId: string,
  updates: { config?: Record<string, unknown>; is_active?: boolean }
): Promise<NotificationChannel | null> {
  const existing = await db
    .prepare('SELECT * FROM notification_channels WHERE id = ? AND tenant_id = ?')
    .bind(channelId, tenantId)
    .first<NotificationChannel>();

  if (!existing) return null;

  const newConfig = updates.config ? JSON.stringify(updates.config) : existing.config;
  const newActive = updates.is_active !== undefined ? (updates.is_active ? 1 : 0) : existing.is_active;

  await db
    .prepare('UPDATE notification_channels SET config = ?, is_active = ? WHERE id = ? AND tenant_id = ?')
    .bind(newConfig, newActive, channelId, tenantId)
    .run();

  return db.prepare('SELECT * FROM notification_channels WHERE id = ?').bind(channelId).first<NotificationChannel>();
}

/** Remove a notification channel */
export async function removeChannel(db: D1Database, tenantId: string, channelId: string): Promise<boolean> {
  const result = await db
    .prepare('DELETE FROM notification_channels WHERE id = ? AND tenant_id = ?')
    .bind(channelId, tenantId)
    .run();
  return (result.meta.changes ?? 0) > 0;
}

// ── Dispatch ───────────────────────────────────────────────────────────────────

/** Deliver to one channel and write a log entry; returns the log row */
async function dispatchOne(
  db: D1Database,
  tenantId: string,
  channel: NotificationChannel,
  eventType: string,
  subject: string,
  body: string,
  data: Record<string, unknown>
): Promise<NotificationLogEntry | null> {
  const logId = crypto.randomUUID();
  try {
    if (channel.channel_type === 'webhook') {
      const cfg = JSON.parse(channel.config) as { url?: string };
      if (cfg.url) {
        const resp = await fetch(cfg.url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ event_type: eventType, subject, body, data }),
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      }
    }
    await db
      .prepare(
        `INSERT INTO notification_log (id, tenant_id, channel_id, channel_type, event_type, subject, body, status, sent_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, 'sent', datetime('now'))`
      )
      .bind(logId, tenantId, channel.id, channel.channel_type, eventType, subject, body)
      .run();
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Unknown error';
    await db
      .prepare(
        `INSERT INTO notification_log (id, tenant_id, channel_id, channel_type, event_type, subject, body, status, error)
         VALUES (?, ?, ?, ?, ?, ?, ?, 'failed', ?)`
      )
      .bind(logId, tenantId, channel.id, channel.channel_type, eventType, subject, body, error)
      .run();
  }
  return db.prepare('SELECT * FROM notification_log WHERE id = ?').bind(logId).first<NotificationLogEntry>();
}

/** Dispatch notification to all active tenant channels matching the template's channel list */
export async function sendNotification(
  db: D1Database,
  tenantId: string,
  eventType: string,
  data: Record<string, unknown>
): Promise<NotificationLogEntry[]> {
  const template = await getTemplate(db, eventType);
  const allActive = await db
    .prepare('SELECT * FROM notification_channels WHERE tenant_id = ? AND is_active = 1')
    .bind(tenantId)
    .all<NotificationChannel>();

  const targetTypes: string[] = template
    ? (JSON.parse(template.channels) as string[])
    : allActive.results.map((c) => c.channel_type);

  const channels = allActive.results.filter((c) => targetTypes.includes(c.channel_type));
  const subject = template ? render(template.subject_template, data) : eventType;
  const body = template ? render(template.body_template, data) : JSON.stringify(data);

  const results = await Promise.all(
    channels.map((ch) => dispatchOne(db, tenantId, ch, eventType, subject, body, data))
  );
  return results.filter((r): r is NotificationLogEntry => r !== null);
}

// ── Log & Stats ────────────────────────────────────────────────────────────────

/** Notification history for a tenant with optional event_type filter */
export async function getNotificationLog(
  db: D1Database,
  tenantId: string,
  limit = 50,
  eventType?: string
): Promise<NotificationLogEntry[]> {
  const cap = Math.min(limit, 200);
  if (eventType) {
    const rows = await db
      .prepare('SELECT * FROM notification_log WHERE tenant_id = ? AND event_type = ? ORDER BY created_at DESC LIMIT ?')
      .bind(tenantId, eventType, cap)
      .all<NotificationLogEntry>();
    return rows.results;
  }
  const rows = await db
    .prepare('SELECT * FROM notification_log WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?')
    .bind(tenantId, cap)
    .all<NotificationLogEntry>();
  return rows.results;
}

/** Aggregated stats per tenant */
export async function getNotificationStats(db: D1Database, tenantId: string): Promise<NotificationStats> {
  const [totals, byChannel] = await Promise.all([
    db
      .prepare(
        `SELECT COUNT(*) as total,
           SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) as sent,
           SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
           SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending
         FROM notification_log WHERE tenant_id = ?`
      )
      .bind(tenantId)
      .first<{ total: number; sent: number; failed: number; pending: number }>(),
    db
      .prepare('SELECT channel_type, COUNT(*) as count FROM notification_log WHERE tenant_id = ? GROUP BY channel_type')
      .bind(tenantId)
      .all<{ channel_type: string; count: number }>(),
  ]);

  const by_channel: Record<string, number> = {};
  for (const row of byChannel.results) by_channel[row.channel_type] = row.count;

  return {
    total: totals?.total ?? 0,
    sent: totals?.sent ?? 0,
    failed: totals?.failed ?? 0,
    pending: totals?.pending ?? 0,
    by_channel,
  };
}

/** Admin: platform-wide overview across all tenants */
export async function getAdminNotificationOverview(db: D1Database): Promise<{
  total: number;
  sent: number;
  failed: number;
  tenants: number;
  top_events: { event_type: string; count: number }[];
}> {
  const [summary, topEvents] = await Promise.all([
    db
      .prepare(
        `SELECT COUNT(*) as total,
           SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) as sent,
           SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed,
           COUNT(DISTINCT tenant_id) as tenants
         FROM notification_log`
      )
      .first<{ total: number; sent: number; failed: number; tenants: number }>(),
    db
      .prepare(
        'SELECT event_type, COUNT(*) as count FROM notification_log GROUP BY event_type ORDER BY count DESC LIMIT 10'
      )
      .all<{ event_type: string; count: number }>(),
  ]);

  return {
    total: summary?.total ?? 0,
    sent: summary?.sent ?? 0,
    failed: summary?.failed ?? 0,
    tenants: summary?.tenants ?? 0,
    top_events: topEvents.results,
  };
}
