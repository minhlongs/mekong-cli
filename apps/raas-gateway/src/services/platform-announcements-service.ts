/**
 * Platform Announcements Service — system-wide banners, maintenance windows, and tenant notifications
 * Tables: platform_announcements, announcement_dismissals
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ──────────────────────────────────────────────────────────────────────

export type AnnouncementType = 'info' | 'warning' | 'maintenance' | 'feature' | 'critical';
export type AudienceTier = 'all' | 'free' | 'pro' | 'enterprise';

export interface Announcement {
  id: string;
  title: string;
  content: string;
  type: AnnouncementType;
  priority: number;
  target_audience: AudienceTier;
  starts_at: string;
  ends_at: string | null;
  is_active: number;
  created_by: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface AnnouncementStats {
  total: number;
  active: number;
  by_type: Record<string, number>;
  dismissal_rate: number;
}

// ── Audience matching ──────────────────────────────────────────────────────────

/** Map tenant tier to audience filter for SQL IN clause */
function audienceValues(tenantTier?: string): string[] {
  const base = ['all'];
  if (tenantTier === 'pro') return [...base, 'pro'];
  if (tenantTier === 'enterprise') return [...base, 'pro', 'enterprise'];
  return [...base, 'free']; // starter/unknown → free tier
}

// ── CRUD ───────────────────────────────────────────────────────────────────────

/** Create a new platform announcement */
export async function createAnnouncement(
  db: D1Database,
  title: string,
  content: string,
  type: AnnouncementType = 'info',
  priority: number = 0,
  targetAudience: AudienceTier = 'all',
  startsAt?: string,
  endsAt?: string,
  createdBy?: string,
): Promise<Announcement> {
  const id = crypto.randomUUID();
  const starts = startsAt ?? new Date().toISOString();

  await db.prepare(`
    INSERT INTO platform_announcements
      (id, title, content, type, priority, target_audience, starts_at, ends_at, created_by)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(id, title, content, type, priority, targetAudience, starts, endsAt ?? null, createdBy ?? null).run();

  const row = await db.prepare('SELECT * FROM platform_announcements WHERE id = ?')
    .bind(id).first<Announcement>();
  return row!;
}

/** List active announcements, optionally filtered by tenant tier */
export async function listActiveAnnouncements(
  db: D1Database,
  tenantTier?: string,
): Promise<Announcement[]> {
  const audiences = audienceValues(tenantTier);
  const placeholders = audiences.map(() => '?').join(', ');

  const rows = await db.prepare(`
    SELECT * FROM platform_announcements
    WHERE is_active = 1
      AND starts_at <= datetime('now')
      AND (ends_at IS NULL OR ends_at > datetime('now'))
      AND target_audience IN (${placeholders})
    ORDER BY priority DESC, starts_at DESC
  `).bind(...audiences).all<Announcement>();

  return rows.results;
}

/** Get a single announcement by ID */
export async function getAnnouncement(
  db: D1Database,
  announcementId: string,
): Promise<Announcement | null> {
  return db.prepare('SELECT * FROM platform_announcements WHERE id = ?')
    .bind(announcementId).first<Announcement>();
}

/** Update announcement fields (partial update) */
export async function updateAnnouncement(
  db: D1Database,
  announcementId: string,
  updates: Partial<Pick<Announcement, 'title' | 'content' | 'type' | 'priority' | 'target_audience' | 'starts_at' | 'ends_at' | 'is_active'>>,
): Promise<Announcement | null> {
  const fields = Object.keys(updates) as Array<keyof typeof updates>;
  if (fields.length === 0) return getAnnouncement(db, announcementId);

  const setClauses = [...fields.map((f) => `${f} = ?`), "updated_at = datetime('now')"].join(', ');
  const values = fields.map((f) => updates[f]);

  await db.prepare(`UPDATE platform_announcements SET ${setClauses} WHERE id = ?`)
    .bind(...values, announcementId).run();

  return getAnnouncement(db, announcementId);
}

/** Hard delete an announcement and its dismissals */
export async function deleteAnnouncement(db: D1Database, announcementId: string): Promise<void> {
  await db.prepare('DELETE FROM announcement_dismissals WHERE announcement_id = ?')
    .bind(announcementId).run();
  await db.prepare('DELETE FROM platform_announcements WHERE id = ?')
    .bind(announcementId).run();
}

// ── Dismissals ─────────────────────────────────────────────────────────────────

/** Record a tenant dismissing an announcement */
export async function dismissAnnouncement(
  db: D1Database,
  tenantId: string,
  announcementId: string,
): Promise<void> {
  await db.prepare(`
    INSERT OR IGNORE INTO announcement_dismissals (id, announcement_id, tenant_id)
    VALUES (?, ?, ?)
  `).bind(crypto.randomUUID(), announcementId, tenantId).run();
}

/** Return active announcements not yet dismissed by the tenant */
export async function getUndismissedAnnouncements(
  db: D1Database,
  tenantId: string,
  tenantTier?: string,
): Promise<Announcement[]> {
  const audiences = audienceValues(tenantTier);
  const placeholders = audiences.map(() => '?').join(', ');

  const rows = await db.prepare(`
    SELECT a.* FROM platform_announcements a
    WHERE a.is_active = 1
      AND a.starts_at <= datetime('now')
      AND (a.ends_at IS NULL OR a.ends_at > datetime('now'))
      AND a.target_audience IN (${placeholders})
      AND NOT EXISTS (
        SELECT 1 FROM announcement_dismissals d
        WHERE d.announcement_id = a.id AND d.tenant_id = ?
      )
    ORDER BY a.priority DESC, a.starts_at DESC
  `).bind(...audiences, tenantId).all<Announcement>();

  return rows.results;
}

// ── Analytics ──────────────────────────────────────────────────────────────────

/** Stats: total, active count, counts by type, dismissal rate */
export async function getAnnouncementStats(db: D1Database): Promise<AnnouncementStats> {
  const [totalsRow, typeRows, dismissalRow] = await Promise.all([
    db.prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN is_active=1 THEN 1 ELSE 0 END) as active
      FROM platform_announcements
    `).first<{ total: number; active: number }>(),
    db.prepare(`
      SELECT type, COUNT(*) as count FROM platform_announcements GROUP BY type
    `).all<{ type: string; count: number }>(),
    db.prepare(`
      SELECT
        COUNT(*) as dismissals,
        (SELECT COUNT(*) FROM platform_announcements WHERE is_active=1) as active_count
      FROM announcement_dismissals
    `).first<{ dismissals: number; active_count: number }>(),
  ]);

  const by_type: Record<string, number> = {};
  for (const row of typeRows.results) by_type[row.type] = row.count;

  const active = totalsRow?.active ?? 0;
  const dismissals = dismissalRow?.dismissals ?? 0;
  const dismissal_rate = active > 0 ? Math.round((dismissals / active) * 100) / 100 : 0;

  return {
    total: totalsRow?.total ?? 0,
    active,
    by_type,
    dismissal_rate,
  };
}

/** Return upcoming and ongoing maintenance announcements */
export async function getMaintenanceWindows(db: D1Database): Promise<Announcement[]> {
  const rows = await db.prepare(`
    SELECT * FROM platform_announcements
    WHERE type = 'maintenance'
      AND is_active = 1
      AND (ends_at IS NULL OR ends_at > datetime('now'))
    ORDER BY starts_at ASC
  `).all<Announcement>();
  return rows.results;
}

/** Deactivate announcements whose ends_at has passed */
export async function cleanExpiredAnnouncements(db: D1Database): Promise<number> {
  const result = await db.prepare(`
    UPDATE platform_announcements
    SET is_active = 0, updated_at = datetime('now')
    WHERE is_active = 1 AND ends_at IS NOT NULL AND ends_at <= datetime('now')
  `).run();
  return result.meta?.changes ?? 0;
}
