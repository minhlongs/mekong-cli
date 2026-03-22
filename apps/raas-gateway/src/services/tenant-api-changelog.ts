/**
 * Tenant API Changelog Service — CRUD for per-tenant changelog entries and subscriptions
 *
 * All functions use `db: any` to stay consistent with Cloudflare D1 edge types.
 * Return shape: { success: true, data } | { success: false, error: string }
 */

import { randomUUID } from 'crypto';

// ---------------------------------------------------------------------------
// List changelog entries for a tenant (published only unless admin=true)
// ---------------------------------------------------------------------------

export async function listEntries(
  db: any,
  tenantId: string,
  opts: { adminView?: boolean; limit?: number; offset?: number } = {}
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const limit = Math.min(Math.max(opts.limit ?? 20, 1), 100);
    const offset = Math.max(opts.offset ?? 0, 0);

    const where = opts.adminView ? 'tenant_id = ?' : 'tenant_id = ? AND published = 1';
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, version, title, description, change_type, published, published_at, created_at
         FROM tenant_api_changelog_entries
         WHERE ${where}
         ORDER BY created_at DESC
         LIMIT ? OFFSET ?`
      )
      .bind(tenantId, limit, offset)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return { success: false, error };
  }
}

// ---------------------------------------------------------------------------
// Create a new changelog entry
// ---------------------------------------------------------------------------

export async function createEntry(
  db: any,
  tenantId: string,
  payload: {
    version: string;
    title: string;
    description?: string;
    change_type?: string;
    published?: boolean;
  }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const id = randomUUID();
    const changeType = payload.change_type ?? 'feature';
    const published = payload.published ? 1 : 0;
    const publishedAt = payload.published ? new Date().toISOString() : null;

    await db
      .prepare(
        `INSERT INTO tenant_api_changelog_entries
           (id, tenant_id, version, title, description, change_type, published, published_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        payload.version,
        payload.title,
        payload.description ?? null,
        changeType,
        published,
        publishedAt
      )
      .run();

    return {
      success: true,
      data: {
        id,
        tenant_id: tenantId,
        version: payload.version,
        title: payload.title,
        description: payload.description ?? null,
        change_type: changeType,
        published,
        published_at: publishedAt,
      },
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return { success: false, error };
  }
}

// ---------------------------------------------------------------------------
// Get subscriptions for a tenant
// ---------------------------------------------------------------------------

export async function getSubscriptions(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, user_id, notify_on, subscribed_at
         FROM tenant_api_changelog_subscriptions
         WHERE tenant_id = ?
         ORDER BY subscribed_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return { success: false, error };
  }
}

// ---------------------------------------------------------------------------
// Admin overview: entry counts + subscription counts across all tenants
// ---------------------------------------------------------------------------

export async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const entryStats = await db
      .prepare(
        `SELECT
           COUNT(*) AS total_entries,
           SUM(published) AS published_entries,
           COUNT(DISTINCT tenant_id) AS tenants_with_entries
         FROM tenant_api_changelog_entries`
      )
      .first();

    const subStats = await db
      .prepare(
        `SELECT
           COUNT(*) AS total_subscriptions,
           COUNT(DISTINCT tenant_id) AS tenants_with_subscriptions
         FROM tenant_api_changelog_subscriptions`
      )
      .first();

    return {
      success: true,
      data: {
        entries: entryStats ?? {},
        subscriptions: subStats ?? {},
      },
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'DB error';
    return { success: false, error };
  }
}

export const tenantApiChangelogService = {
  listEntries,
  createEntry,
  getSubscriptions,
  getAdminOverview,
};
