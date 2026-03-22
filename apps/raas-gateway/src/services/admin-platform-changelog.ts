/**
 * Admin Platform Changelog Service — manages platform release entries and subscriber tracking
 */

function newId(): string {
  return crypto.randomUUID();
}

function now(): string {
  return new Date().toISOString();
}

/** List all changelog entries, newest first */
async function listEntries(db: any): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM platform_changelog_entries ORDER BY created_at DESC')
      .all();
    return { success: true, data: (result.results ?? []) as any[] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Insert a new changelog entry */
async function createEntry(db: any, input: {
  version: string;
  title: string;
  description?: string;
  change_type?: string;
  severity?: string;
  author?: string;
  published_at?: string;
}): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = newId();
    const ts = now();
    await db
      .prepare(
        `INSERT INTO platform_changelog_entries
         (id, version, title, description, change_type, severity, author, published_at, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        input.version,
        input.title,
        input.description ?? null,
        input.change_type ?? 'feature',
        input.severity ?? 'minor',
        input.author ?? null,
        input.published_at ?? null,
        ts,
        ts
      )
      .run();
    return { success: true, data: { id, ...input, created_at: ts, updated_at: ts } };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** List all changelog subscribers */
async function getSubscribers(db: any): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM platform_changelog_subscribers ORDER BY subscribed_at DESC')
      .all();
    return { success: true, data: (result.results ?? []) as any[] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Dashboard: entry count by change_type, recent entries, subscriber count */
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [countResult, recentResult, subscriberResult] = await Promise.all([
      db
        .prepare('SELECT change_type, COUNT(*) as count FROM platform_changelog_entries GROUP BY change_type')
        .all(),
      db
        .prepare('SELECT * FROM platform_changelog_entries ORDER BY created_at DESC LIMIT 5')
        .all(),
      db
        .prepare('SELECT COUNT(*) as total FROM platform_changelog_subscribers')
        .first(),
    ]);
    return {
      success: true,
      data: {
        entries_by_type: (countResult.results ?? []) as any[],
        recent_entries: (recentResult.results ?? []) as any[],
        subscriber_count: (subscriberResult as any)?.total ?? 0,
      },
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export const adminPlatformChangelogService = {
  listEntries,
  createEntry,
  getSubscribers,
  getDashboard,
};
