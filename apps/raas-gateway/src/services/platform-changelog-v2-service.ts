/**
 * Platform Changelog V2 Service — versioned entries, subscriptions, read tracking
 */

export interface ChangelogEntry {
  id: string;
  version: string;
  title: string;
  content: string;
  category: string;
  severity: string;
  tags: string;
  is_published: number;
  published_at: string | null;
  author: string | null;
  related_api_versions: string;
  created_at: string;
  updated_at: string;
}

export interface CreateEntryData {
  version: string;
  title: string;
  content: string;
  category?: string;
  severity?: string;
  tags?: string[];
  author?: string;
  related_api_versions?: string[];
}

export interface ListEntriesOptions {
  category?: string;
  severity?: string;
  limit?: number;
  offset?: number;
}

export interface SubscriptionConfig {
  categories?: string[];
  notify_via?: string;
  webhook_url?: string;
}

/** Create a new changelog entry (admin) */
export async function createEntry(db: D1Database, data: CreateEntryData): Promise<ChangelogEntry> {
  const result = await db.prepare(
    `INSERT INTO changelog_entries_v2 (version, title, content, category, severity, tags, author, related_api_versions)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     RETURNING *`
  )
    .bind(
      data.version,
      data.title,
      data.content,
      data.category ?? 'feature',
      data.severity ?? 'minor',
      JSON.stringify(data.tags ?? []),
      data.author ?? null,
      JSON.stringify(data.related_api_versions ?? [])
    )
    .first<ChangelogEntry>();
  if (!result) throw new Error('Failed to create changelog entry');
  return result;
}

/** List published entries with optional filters */
export async function listEntries(db: D1Database, options: ListEntriesOptions = {}): Promise<ChangelogEntry[]> {
  const { category, severity, limit = 20, offset = 0 } = options;
  let query = `SELECT * FROM changelog_entries_v2 WHERE is_published = 1`;
  const binds: (string | number)[] = [];
  if (category) { query += ` AND category = ?`; binds.push(category); }
  if (severity) { query += ` AND severity = ?`; binds.push(severity); }
  query += ` ORDER BY published_at DESC LIMIT ? OFFSET ?`;
  binds.push(limit, offset);
  const result = await db.prepare(query).bind(...binds).all<ChangelogEntry>();
  return result.results;
}

/** Get a single entry by id (published or not) */
export async function getEntry(db: D1Database, entryId: string): Promise<ChangelogEntry | null> {
  return db.prepare(`SELECT * FROM changelog_entries_v2 WHERE id = ?`).bind(entryId).first<ChangelogEntry>();
}

/** Update an existing entry */
export async function updateEntry(db: D1Database, entryId: string, updates: Partial<CreateEntryData>): Promise<ChangelogEntry> {
  const sets: string[] = [];
  const binds: (string | number | null)[] = [];
  if (updates.version !== undefined) { sets.push('version = ?'); binds.push(updates.version); }
  if (updates.title !== undefined) { sets.push('title = ?'); binds.push(updates.title); }
  if (updates.content !== undefined) { sets.push('content = ?'); binds.push(updates.content); }
  if (updates.category !== undefined) { sets.push('category = ?'); binds.push(updates.category); }
  if (updates.severity !== undefined) { sets.push('severity = ?'); binds.push(updates.severity); }
  if (updates.tags !== undefined) { sets.push('tags = ?'); binds.push(JSON.stringify(updates.tags)); }
  if (updates.author !== undefined) { sets.push('author = ?'); binds.push(updates.author ?? null); }
  if (updates.related_api_versions !== undefined) { sets.push('related_api_versions = ?'); binds.push(JSON.stringify(updates.related_api_versions)); }
  if (sets.length === 0) throw new Error('No fields to update');
  sets.push(`updated_at = datetime('now')`);
  binds.push(entryId);
  const result = await db.prepare(
    `UPDATE changelog_entries_v2 SET ${sets.join(', ')} WHERE id = ? RETURNING *`
  ).bind(...binds).first<ChangelogEntry>();
  if (!result) throw new Error('Entry not found');
  return result;
}

/** Publish an entry — sets is_published=1 and records published_at */
export async function publishEntry(db: D1Database, entryId: string): Promise<ChangelogEntry> {
  const result = await db.prepare(
    `UPDATE changelog_entries_v2
     SET is_published = 1, published_at = datetime('now'), updated_at = datetime('now')
     WHERE id = ? RETURNING *`
  ).bind(entryId).first<ChangelogEntry>();
  if (!result) throw new Error('Entry not found');
  return result;
}

/** Create or replace a tenant subscription */
export async function subscribeToChangelog(db: D1Database, tenantId: string, config: SubscriptionConfig): Promise<{ id: string }> {
  // Deactivate existing subscription first
  await db.prepare(`UPDATE changelog_subscriptions SET is_active = 0 WHERE tenant_id = ?`).bind(tenantId).run();
  const result = await db.prepare(
    `INSERT INTO changelog_subscriptions (tenant_id, categories, notify_via, webhook_url)
     VALUES (?, ?, ?, ?) RETURNING id`
  )
    .bind(
      tenantId,
      JSON.stringify(config.categories ?? ['feature', 'breaking', 'security']),
      config.notify_via ?? 'in_app',
      config.webhook_url ?? null
    )
    .first<{ id: string }>();
  if (!result) throw new Error('Failed to create subscription');
  return result;
}

/** Get active subscription for a tenant */
export async function getSubscription(db: D1Database, tenantId: string): Promise<object | null> {
  return db.prepare(
    `SELECT id, tenant_id, categories, notify_via, webhook_url, is_active, created_at
     FROM changelog_subscriptions WHERE tenant_id = ? AND is_active = 1`
  ).bind(tenantId).first();
}

/** Mark a changelog entry as read for a tenant (idempotent) */
export async function markAsRead(db: D1Database, tenantId: string, entryId: string): Promise<void> {
  const existing = await db.prepare(
    `SELECT id FROM changelog_reads WHERE tenant_id = ? AND entry_id = ?`
  ).bind(tenantId, entryId).first();
  if (!existing) {
    await db.prepare(
      `INSERT INTO changelog_reads (tenant_id, entry_id) VALUES (?, ?)`
    ).bind(tenantId, entryId).run();
  }
}

/** Count unread published entries for a tenant */
export async function getUnreadCount(db: D1Database, tenantId: string): Promise<number> {
  const result = await db.prepare(
    `SELECT COUNT(*) as count FROM changelog_entries_v2
     WHERE is_published = 1
       AND id NOT IN (SELECT entry_id FROM changelog_reads WHERE tenant_id = ?)`
  ).bind(tenantId).first<{ count: number }>();
  return result?.count ?? 0;
}

/** Admin stats: entry counts by category and overall read rate */
export async function getAdminChangelogStats(db: D1Database): Promise<object> {
  const byCategoryResult = await db.prepare(
    `SELECT category, COUNT(*) as total,
            SUM(is_published) as published
     FROM changelog_entries_v2 GROUP BY category`
  ).all<{ category: string; total: number; published: number }>();

  const totalPublished = await db.prepare(
    `SELECT COUNT(*) as count FROM changelog_entries_v2 WHERE is_published = 1`
  ).first<{ count: number }>();

  const totalReads = await db.prepare(
    `SELECT COUNT(DISTINCT entry_id || tenant_id) as count FROM changelog_reads`
  ).first<{ count: number }>();

  return {
    by_category: byCategoryResult.results,
    total_published: totalPublished?.count ?? 0,
    total_read_events: totalReads?.count ?? 0,
  };
}
