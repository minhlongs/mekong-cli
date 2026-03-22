/**
 * Tenant API Changelog Service
 * Manage per-tenant API changelog entries and email subscriptions.
 *
 * listEntries    — list changelog entries for a tenant
 * createEntry    — create a new changelog entry
 * getSubscriptions — list email subscriptions for a tenant
 * getAdminOverview — cross-tenant stats (admin only)
 */

export interface ApiChangelogEntry {
  id: string;
  tenant_id: string;
  change_type: string;
  endpoint: string;
  description: string;
  breaking: number;
  version: string;
  created_at: string;
}

export interface ApiChangelogSubscription {
  id: string;
  tenant_id: string;
  email: string;
  notify_breaking: number;
  created_at: string;
}

export interface CreateEntryData {
  change_type?: string;
  endpoint: string;
  description: string;
  breaking?: number;
  version: string;
}

/** List all changelog entries for a tenant, newest first */
async function listEntries(db: any, tenantId: string): Promise<ApiChangelogEntry[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM api_changelog_entries WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as ApiChangelogEntry[];
  } catch (err) {
    throw new Error(`Failed to list changelog entries: ${err}`);
  }
}

/** Create a new changelog entry for a tenant */
async function createEntry(
  db: any,
  tenantId: string,
  data: CreateEntryData
): Promise<ApiChangelogEntry> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const change_type = data.change_type ?? 'update';
    const breaking = data.breaking ?? 0;

    await db
      .prepare(
        `INSERT INTO api_changelog_entries
           (id, tenant_id, change_type, endpoint, description, breaking, version, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, change_type, data.endpoint, data.description, breaking, data.version, now)
      .run();

    return { id, tenant_id: tenantId, change_type, endpoint: data.endpoint,
             description: data.description, breaking, version: data.version, created_at: now };
  } catch (err) {
    throw new Error(`Failed to create changelog entry: ${err}`);
  }
}

/** List all email subscriptions for a tenant */
async function getSubscriptions(db: any, tenantId: string): Promise<ApiChangelogSubscription[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM api_changelog_subscriptions WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return (result.results ?? []) as ApiChangelogSubscription[];
  } catch (err) {
    throw new Error(`Failed to get subscriptions: ${err}`);
  }
}

/** Admin overview — entry and subscription counts across all tenants */
async function getAdminOverview(db: any): Promise<{
  total_entries: number;
  breaking_entries: number;
  total_subscriptions: number;
  tenants_with_entries: number;
}> {
  try {
    const [entries, subs, tenants] = await Promise.all([
      db.prepare('SELECT COUNT(*) as total, SUM(breaking) as breaking FROM api_changelog_entries').first(),
      db.prepare('SELECT COUNT(*) as total FROM api_changelog_subscriptions').first(),
      db.prepare('SELECT COUNT(DISTINCT tenant_id) as total FROM api_changelog_entries').first(),
    ]);
    return {
      total_entries: Number(entries?.total ?? 0),
      breaking_entries: Number(entries?.breaking ?? 0),
      total_subscriptions: Number(subs?.total ?? 0),
      tenants_with_entries: Number(tenants?.total ?? 0),
    };
  } catch (err) {
    throw new Error(`Failed to get admin overview: ${err}`);
  }
}

export const tenantApiChangelogService = { listEntries, createEntry, getSubscriptions, getAdminOverview };
