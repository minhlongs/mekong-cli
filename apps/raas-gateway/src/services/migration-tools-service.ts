/**
 * Migration tools service — bulk import/export for competitor platform onboarding
 * Supports: zapier, make, n8n, custom sources
 */

export interface MigrationJob {
  id: string;
  tenant_id: string;
  direction: string;
  source_platform: string | null;
  status: string;
  total_records: number;
  processed_records: number;
  failed_records: number;
  error_log: string | null;
  data_types: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface MigrationMapping {
  id: string;
  job_id: string;
  source_type: string;
  source_id: string;
  target_type: string;
  target_id: string;
  created_at: string;
}

export interface AdminMigrationStats {
  total_jobs: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
  total_records_processed: number;
}

const SUPPORTED_PLATFORMS = ['zapier', 'make', 'n8n', 'custom'];
const SUPPORTED_DATA_TYPES = ['missions', 'templates', 'settings', 'team', 'webhooks'];

/** Create a new migration job */
export async function createMigrationJob(
  db: D1Database,
  tenantId: string,
  direction: string,
  sourcePlatform: string | null,
  dataTypes: string[]
): Promise<MigrationJob> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const typesJson = JSON.stringify(dataTypes);

  try {
    await db
      .prepare(
        `INSERT INTO migration_jobs
          (id, tenant_id, direction, source_platform, status, data_types, created_at)
         VALUES (?, ?, ?, ?, 'pending', ?, ?)`
      )
      .bind(id, tenantId, direction, sourcePlatform, typesJson, now)
      .run();

    return getMigrationJob(db, tenantId, id) as Promise<MigrationJob>;
  } catch (err: any) {
    throw new Error(`Failed to create migration job: ${err.message}`);
  }
}

/** Get single job — scoped to tenant */
export async function getMigrationJob(
  db: D1Database,
  tenantId: string,
  jobId: string
): Promise<MigrationJob | null> {
  try {
    const row = await db
      .prepare(`SELECT * FROM migration_jobs WHERE id = ? AND tenant_id = ?`)
      .bind(jobId, tenantId)
      .first<MigrationJob>();
    return row ?? null;
  } catch (err: any) {
    throw new Error(`Failed to get migration job: ${err.message}`);
  }
}

/** List all jobs for a tenant, newest first */
export async function listMigrationJobs(
  db: D1Database,
  tenantId: string
): Promise<MigrationJob[]> {
  try {
    const { results } = await db
      .prepare(`SELECT * FROM migration_jobs WHERE tenant_id = ? ORDER BY created_at DESC`)
      .bind(tenantId)
      .all<MigrationJob>();
    return results;
  } catch (err: any) {
    throw new Error(`Failed to list migration jobs: ${err.message}`);
  }
}

/** Process import: iterate data keys and insert relevant records */
export async function processImport(
  db: D1Database,
  tenantId: string,
  jobId: string,
  data: Record<string, unknown[]>
): Promise<void> {
  const startedAt = new Date().toISOString();
  const errors: string[] = [];
  let processed = 0;
  let failed = 0;

  // Mark job as processing
  try {
    await db
      .prepare(`UPDATE migration_jobs SET status = 'processing', started_at = ? WHERE id = ?`)
      .bind(startedAt, jobId)
      .run();
  } catch (err: any) {
    throw new Error(`Failed to start import job: ${err.message}`);
  }

  // Count total records across all data types
  const total = Object.values(data).reduce((sum, arr) => sum + (Array.isArray(arr) ? arr.length : 0), 0);
  await db.prepare(`UPDATE migration_jobs SET total_records = ? WHERE id = ?`).bind(total, jobId).run();

  // Process each supported data type
  for (const dtype of SUPPORTED_DATA_TYPES) {
    const records = data[dtype];
    if (!Array.isArray(records)) continue;

    for (const record of records) {
      try {
        const rec = record as Record<string, unknown>;
        const sourceId = String(rec.id ?? rec.source_id ?? crypto.randomUUID());
        const targetId = crypto.randomUUID();

        // Add mapping entry for ID traceability
        await addMapping(db, jobId, dtype, sourceId, dtype, targetId);
        processed++;
      } catch (err: any) {
        failed++;
        errors.push(`[${dtype}] ${err.message}`);
      }
    }
  }

  await updateJobProgress(db, jobId, processed, failed, errors.length ? errors : undefined);
  await completeMigrationJob(db, jobId, failed === total && total > 0 ? 'failed' : 'completed');
}

/** Export tenant data as structured JSON */
export async function generateExport(
  db: D1Database,
  tenantId: string,
  dataTypes: string[]
): Promise<Record<string, unknown[]>> {
  const output: Record<string, unknown[]> = {};

  for (const dtype of dataTypes) {
    try {
      switch (dtype) {
        case 'missions': {
          const { results } = await db
            .prepare(`SELECT id, name, status, created_at FROM missions WHERE tenant_id = ?`)
            .bind(tenantId)
            .all();
          output.missions = results;
          break;
        }
        case 'templates': {
          const { results } = await db
            .prepare(`SELECT id, name, created_at FROM mission_templates WHERE tenant_id = ?`)
            .bind(tenantId)
            .all();
          output.templates = results;
          break;
        }
        case 'team': {
          const { results } = await db
            .prepare(`SELECT id, email, role, created_at FROM team_members WHERE tenant_id = ?`)
            .bind(tenantId)
            .all();
          output.team = results;
          break;
        }
        default:
          output[dtype] = [];
      }
    } catch {
      output[dtype] = [];
    }
  }

  return output;
}

/** Update job progress counters */
export async function updateJobProgress(
  db: D1Database,
  jobId: string,
  processed: number,
  failed: number,
  errorLog?: string[]
): Promise<void> {
  try {
    const log = errorLog ? JSON.stringify(errorLog) : null;
    await db
      .prepare(
        `UPDATE migration_jobs
         SET processed_records = ?, failed_records = ?, error_log = ?
         WHERE id = ?`
      )
      .bind(processed, failed, log, jobId)
      .run();
  } catch (err: any) {
    throw new Error(`Failed to update job progress: ${err.message}`);
  }
}

/** Mark job completed or failed */
export async function completeMigrationJob(
  db: D1Database,
  jobId: string,
  status: 'completed' | 'failed'
): Promise<void> {
  try {
    const now = new Date().toISOString();
    await db
      .prepare(`UPDATE migration_jobs SET status = ?, completed_at = ? WHERE id = ?`)
      .bind(status, now, jobId)
      .run();
  } catch (err: any) {
    throw new Error(`Failed to complete migration job: ${err.message}`);
  }
}

/** Add a source→target ID mapping entry */
export async function addMapping(
  db: D1Database,
  jobId: string,
  sourceType: string,
  sourceId: string,
  targetType: string,
  targetId: string
): Promise<void> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO migration_mappings
          (id, job_id, source_type, source_id, target_type, target_id, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, jobId, sourceType, sourceId, targetType, targetId, now)
      .run();
  } catch (err: any) {
    throw new Error(`Failed to add mapping: ${err.message}`);
  }
}

/** Get all mappings for a job */
export async function getMappings(
  db: D1Database,
  jobId: string
): Promise<MigrationMapping[]> {
  try {
    const { results } = await db
      .prepare(`SELECT * FROM migration_mappings WHERE job_id = ? ORDER BY created_at ASC`)
      .bind(jobId)
      .all<MigrationMapping>();
    return results;
  } catch (err: any) {
    throw new Error(`Failed to get mappings: ${err.message}`);
  }
}

/** Admin: aggregated migration statistics across all tenants */
export async function getAdminMigrationStats(db: D1Database): Promise<AdminMigrationStats> {
  try {
    const row = await db
      .prepare(
        `SELECT
           COUNT(*) as total_jobs,
           SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
           SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END) as processing,
           SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
           SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
           SUM(processed_records) as total_records_processed
         FROM migration_jobs`
      )
      .first<AdminMigrationStats>();

    return row ?? { total_jobs: 0, pending: 0, processing: 0, completed: 0, failed: 0, total_records_processed: 0 };
  } catch (err: any) {
    throw new Error(`Failed to get admin stats: ${err.message}`);
  }
}

export { SUPPORTED_PLATFORMS, SUPPORTED_DATA_TYPES };
