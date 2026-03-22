/**
 * Admin tenant migration service — migrate tenants between tiers/plans
 * Tracks upgrades, downgrades, and custom migrations with step-level audit trail
 */

/** List all migrations, optionally filtered by tenant_id or status */
async function listMigrations(
  db: any,
  opts: { tenantId?: string; status?: string; limit?: number } = {}
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const conditions: string[] = [];
    const binds: any[] = [];

    if (opts.tenantId) {
      conditions.push('tenant_id = ?');
      binds.push(opts.tenantId);
    }
    if (opts.status) {
      conditions.push('status = ?');
      binds.push(opts.status);
    }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
    const limit = opts.limit ?? 100;
    binds.push(limit);

    const { results } = await db
      .prepare(`SELECT * FROM tenant_migrations ${where} ORDER BY created_at DESC LIMIT ?`)
      .bind(...binds)
      .all();

    return { success: true, data: results };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** Create a new tenant migration record and seed default steps */
async function createMigration(
  db: any,
  payload: {
    tenantId: string;
    fromTier: string;
    toTier: string;
    migrationType?: string;
    initiatedBy?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const migrationType = payload.migrationType ?? 'upgrade';

    await db
      .prepare(
        `INSERT INTO tenant_migrations
          (id, tenant_id, from_tier, to_tier, migration_type, status, initiated_by, created_at)
         VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)`
      )
      .bind(id, payload.tenantId, payload.fromTier, payload.toTier, migrationType, payload.initiatedBy ?? null, now)
      .run();

    // Seed default migration steps
    const defaultSteps = [
      { name: 'validate_eligibility', order: 1 },
      { name: 'backup_tenant_data', order: 2 },
      { name: 'update_tier_record', order: 3 },
      { name: 'adjust_quota_limits', order: 4 },
      { name: 'notify_tenant', order: 5 },
    ];

    for (const step of defaultSteps) {
      const stepId = crypto.randomUUID();
      await db
        .prepare(
          `INSERT INTO tenant_migration_steps
            (id, migration_id, step_name, step_order, status, created_at)
           VALUES (?, ?, ?, ?, 'pending', ?)`
        )
        .bind(stepId, id, step.name, step.order, now)
        .run();
    }

    // Return newly created migration
    const record = await db
      .prepare(`SELECT * FROM tenant_migrations WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: record };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** Get all steps for a given migration_id */
async function getSteps(
  db: any,
  migrationId: string
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const { results } = await db
      .prepare(
        `SELECT * FROM tenant_migration_steps
         WHERE migration_id = ?
         ORDER BY step_order ASC`
      )
      .bind(migrationId)
      .all();

    return { success: true, data: results };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

/** Dashboard: aggregated migration stats across all tenants */
async function getDashboard(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const summary = await db
      .prepare(
        `SELECT
           COUNT(*) as total,
           SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
           SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
           SUM(CASE WHEN migration_type = 'upgrade' THEN 1 ELSE 0 END) as upgrades,
           SUM(CASE WHEN migration_type = 'downgrade' THEN 1 ELSE 0 END) as downgrades
         FROM tenant_migrations`
      )
      .first();

    const recentMigrations = await db
      .prepare(
        `SELECT id, tenant_id, from_tier, to_tier, migration_type, status, created_at
         FROM tenant_migrations
         ORDER BY created_at DESC
         LIMIT 10`
      )
      .all();

    return {
      success: true,
      data: {
        summary,
        recentMigrations: recentMigrations.results,
      },
    };
  } catch (err: any) {
    return { success: false, error: err.message };
  }
}

export const adminTenantMigrationService = {
  listMigrations,
  createMigration,
  getSteps,
  getDashboard,
};
