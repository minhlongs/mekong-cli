/**
 * Mission Batch Processing Service — create and track batches of missions
 * Supports listing batches, creating new batches, fetching items, and admin overview
 */

/**
 * List all batch jobs for a tenant
 */
async function listBatches(db: any, tenantId: string): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM mission_batch_jobs WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to list batches' };
  }
}

/**
 * Create a new batch job with optional mission items
 * Body: { batch_name, missions: Array<{ mission_id? }> }
 */
async function createBatch(
  db: any,
  tenantId: string,
  batchName: string,
  missions: Array<{ mission_id?: string }>
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const batchId = crypto.randomUUID();
    const now = new Date().toISOString();
    const total = missions.length;

    await db
      .prepare(
        `INSERT INTO mission_batch_jobs (id, tenant_id, batch_name, total_missions, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, 'pending', ?, ?)`
      )
      .bind(batchId, tenantId, batchName, total, now, now)
      .run();

    // Insert batch items
    for (const m of missions) {
      const itemId = crypto.randomUUID();
      await db
        .prepare(
          `INSERT INTO mission_batch_items (id, tenant_id, batch_id, mission_id, status, created_at)
           VALUES (?, ?, ?, ?, 'pending', ?)`
        )
        .bind(itemId, tenantId, batchId, m.mission_id ?? null, now)
        .run();
    }

    const batch = await db
      .prepare('SELECT * FROM mission_batch_jobs WHERE id = ?')
      .bind(batchId)
      .first();

    return { success: true, data: batch };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to create batch' };
  }
}

/**
 * Get items for a specific batch (tenant-scoped)
 */
async function getItems(
  db: any,
  tenantId: string,
  batchId: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const batch = await db
      .prepare('SELECT id FROM mission_batch_jobs WHERE id = ? AND tenant_id = ?')
      .bind(batchId, tenantId)
      .first();

    if (!batch) {
      return { success: false, error: 'Batch not found' };
    }

    const result = await db
      .prepare('SELECT * FROM mission_batch_items WHERE batch_id = ? ORDER BY created_at ASC')
      .bind(batchId)
      .all();

    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to get batch items' };
  }
}

/**
 * Admin overview — aggregate stats across all tenants
 */
async function getAdminOverview(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const totals = await db
      .prepare(
        `SELECT
           COUNT(*) AS total_batches,
           SUM(total_missions) AS total_missions,
           SUM(completed_missions) AS total_completed,
           SUM(failed_missions) AS total_failed,
           COUNT(DISTINCT tenant_id) AS tenant_count
         FROM mission_batch_jobs`
      )
      .first();

    const byStatus = await db
      .prepare(
        `SELECT status, COUNT(*) AS count FROM mission_batch_jobs GROUP BY status`
      )
      .all();

    return {
      success: true,
      data: {
        totals,
        by_status: byStatus.results,
      },
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to get admin overview' };
  }
}

export const missionBatchProcessingService = {
  listBatches,
  createBatch,
  getItems,
  getAdminOverview,
};
