/**
 * Admin Platform Migration Service — CRUD for platform_migrations + rollback history
 * Used by admin-platform-migration route to manage D1 schema migration records.
 */

interface MigrationRow {
  id: string;
  migration_name: string;
  version: string;
  migration_type: string;
  status: string;
  sql_content: string | null;
  applied_by: string | null;
  applied_at: string | null;
  created_at: string;
}

interface RollbackRow {
  id: string;
  migration_id: string;
  rollback_reason: string | null;
  rolled_back_by: string | null;
  created_at: string;
}

// List all migrations, optionally filtered by status or version
async function listMigrations(
  db: any,
  filters: { status?: string; version?: string } = {}
): Promise<MigrationRow[]> {
  try {
    let query = 'SELECT * FROM platform_migrations';
    const conditions: string[] = [];
    const params: string[] = [];

    if (filters.status) {
      conditions.push('status = ?');
      params.push(filters.status);
    }
    if (filters.version) {
      conditions.push('version = ?');
      params.push(filters.version);
    }
    if (conditions.length) query += ' WHERE ' + conditions.join(' AND ');
    query += ' ORDER BY created_at DESC';

    const result = await db.prepare(query).bind(...params).all();
    return result.results as MigrationRow[];
  } catch (err) {
    throw new Error(`listMigrations failed: ${(err as Error).message}`);
  }
}

// Insert a new migration record with status 'pending'
async function createMigration(
  db: any,
  data: {
    id: string;
    migration_name: string;
    version: string;
    migration_type?: string;
    sql_content?: string;
    applied_by?: string;
  }
): Promise<MigrationRow> {
  try {
    await db
      .prepare(
        `INSERT INTO platform_migrations
           (id, migration_name, version, migration_type, status, sql_content, applied_by, created_at)
         VALUES (?, ?, ?, ?, 'pending', ?, ?, CURRENT_TIMESTAMP)`
      )
      .bind(
        data.id,
        data.migration_name,
        data.version,
        data.migration_type ?? 'schema',
        data.sql_content ?? null,
        data.applied_by ?? null
      )
      .run();

    const row = await db
      .prepare('SELECT * FROM platform_migrations WHERE id = ?')
      .bind(data.id)
      .first();
    return row as MigrationRow;
  } catch (err) {
    throw new Error(`createMigration failed: ${(err as Error).message}`);
  }
}

// List rollback history, optionally scoped to a migration_id
async function getRollbacks(
  db: any,
  migration_id?: string
): Promise<RollbackRow[]> {
  try {
    let query = 'SELECT * FROM migration_rollback_history';
    const params: string[] = [];
    if (migration_id) {
      query += ' WHERE migration_id = ?';
      params.push(migration_id);
    }
    query += ' ORDER BY created_at DESC';
    const result = await db.prepare(query).bind(...params).all();
    return result.results as RollbackRow[];
  } catch (err) {
    throw new Error(`getRollbacks failed: ${(err as Error).message}`);
  }
}

// Dashboard summary: counts by status + recent activity
async function getDashboard(db: any): Promise<{
  total: number;
  byStatus: Record<string, number>;
  recentMigrations: MigrationRow[];
  recentRollbacks: RollbackRow[];
}> {
  try {
    const [statusCounts, recent, rollbacks] = await Promise.all([
      db.prepare('SELECT status, COUNT(*) as cnt FROM platform_migrations GROUP BY status').all(),
      db.prepare('SELECT * FROM platform_migrations ORDER BY created_at DESC LIMIT 5').all(),
      db.prepare('SELECT * FROM migration_rollback_history ORDER BY created_at DESC LIMIT 5').all(),
    ]);

    const byStatus: Record<string, number> = {};
    let total = 0;
    for (const row of statusCounts.results as any[]) {
      byStatus[row.status] = row.cnt;
      total += row.cnt;
    }

    return {
      total,
      byStatus,
      recentMigrations: recent.results as MigrationRow[],
      recentRollbacks: rollbacks.results as RollbackRow[],
    };
  } catch (err) {
    throw new Error(`getDashboard failed: ${(err as Error).message}`);
  }
}

export const adminPlatformMigrationService = {
  listMigrations,
  createMigration,
  getRollbacks,
  getDashboard,
};
