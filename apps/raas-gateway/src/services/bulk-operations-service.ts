/**
 * Bulk operations service — batch import/export for missions, api_keys, team_members, webhooks
 * CF Workers sync execution (no background jobs), max 500 items per import batch
 */

export interface BulkJob {
  id: string;
  tenant_id: string;
  type: 'import' | 'export';
  resource: 'missions' | 'api_keys' | 'team_members' | 'webhooks';
  status: 'pending' | 'processing' | 'completed' | 'failed';
  total_items: number;
  processed_items: number;
  failed_items: number;
  errors: string[];
  created_at: string;
  completed_at: string | null;
}

interface BulkJobRow extends Omit<BulkJob, 'errors'> {
  errors: string; // JSON string in DB
}

interface ImportResult {
  imported: number;
  failed: number;
  errors: string[];
}

function parseBulkJob(row: BulkJobRow): BulkJob {
  return { ...row, errors: JSON.parse(row.errors || '[]') };
}

/** Save job record to D1 */
async function saveJob(db: D1Database, job: Omit<BulkJob, 'errors'> & { errors: string; result_data?: string }): Promise<void> {
  await db.prepare(
    `INSERT INTO bulk_jobs (id, tenant_id, type, resource, status, total_items, processed_items, failed_items, errors, result_data, created_at, completed_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    job.id, job.tenant_id, job.type, job.resource, job.status,
    job.total_items, job.processed_items, job.failed_items,
    job.errors, job.result_data ?? null, job.created_at, job.completed_at
  ).run();
}

/** Update job status after processing */
async function updateJob(db: D1Database, jobId: string, updates: Partial<BulkJob> & { result_data?: string }): Promise<void> {
  await db.prepare(
    `UPDATE bulk_jobs SET status=?, processed_items=?, failed_items=?, errors=?, result_data=?, completed_at=? WHERE id=?`
  ).bind(
    updates.status ?? 'completed',
    updates.processed_items ?? 0,
    updates.failed_items ?? 0,
    JSON.stringify(updates.errors ?? []),
    updates.result_data ?? null,
    updates.completed_at ?? new Date().toISOString(),
    jobId
  ).run();
}

/** Format rows as CSV — first row is header */
function toCSV(rows: Record<string, unknown>[]): string {
  if (rows.length === 0) return '';
  const headers = Object.keys(rows[0]);
  const lines = [headers.join(',')];
  for (const row of rows) {
    const values = headers.map(h => {
      const v = String(row[h] ?? '').replace(/"/g, '""');
      return v.includes(',') || v.includes('"') || v.includes('\n') ? `"${v}"` : v;
    });
    lines.push(values.join(','));
  }
  return lines.join('\n');
}

/** Export missions for a tenant */
export async function exportMissions(
  db: D1Database, tenantId: string, format: 'json' | 'csv', filters?: Record<string, string>
): Promise<string> {
  let query = 'SELECT id, goal, status, model, priority, created_at, completed_at FROM missions WHERE tenant_id = ?';
  const params: unknown[] = [tenantId];
  if (filters?.status) { query += ' AND status = ?'; params.push(filters.status); }
  if (filters?.model)  { query += ' AND model = ?';  params.push(filters.model); }
  query += ' ORDER BY created_at DESC LIMIT 5000';

  const result = await db.prepare(query).bind(...params).all<Record<string, unknown>>();
  const rows = result.results;
  return format === 'csv' ? toCSV(rows) : JSON.stringify(rows, null, 2);
}

/** Export API keys (masked) for a tenant */
export async function exportApiKeys(db: D1Database, tenantId: string, format: 'json' | 'csv'): Promise<string> {
  const result = await db.prepare(
    'SELECT id, name, scope, created_at FROM api_keys WHERE tenant_id = ? ORDER BY created_at DESC'
  ).bind(tenantId).all<Record<string, unknown>>();
  const rows = result.results;
  return format === 'csv' ? toCSV(rows) : JSON.stringify(rows, null, 2);
}

/** Import missions — validates and inserts each item */
export async function importMissions(db: D1Database, tenantId: string, items: Record<string, unknown>[]): Promise<ImportResult> {
  const result: ImportResult = { imported: 0, failed: 0, errors: [] };
  const now = new Date().toISOString();
  const stmt = db.prepare(
    `INSERT INTO missions (id, tenant_id, goal, model, priority, status, created_at) VALUES (?, ?, ?, ?, ?, 'queued', ?)`
  );

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const goal = typeof item.goal === 'string' ? item.goal.trim() : '';
    if (!goal) {
      result.failed++;
      result.errors.push(`Item ${i}: goal is required`);
      continue;
    }
    try {
      const id = crypto.randomUUID();
      const model = typeof item.model === 'string' ? item.model : 'auto';
      const priority = typeof item.priority === 'number' ? item.priority : 0;
      await stmt.bind(id, tenantId, goal, model, priority, now).run();
      result.imported++;
    } catch (err) {
      result.failed++;
      result.errors.push(`Item ${i}: ${err instanceof Error ? err.message : 'insert failed'}`);
    }
  }
  return result;
}

/** Create and run an export job synchronously */
export async function createBulkExport(
  db: D1Database, tenantId: string,
  resource: BulkJob['resource'],
  options?: { format?: 'json' | 'csv'; filters?: Record<string, string> }
): Promise<BulkJob> {
  const format = options?.format ?? 'json';
  const jobId = crypto.randomUUID();
  const now = new Date().toISOString();

  await saveJob(db, {
    id: jobId, tenant_id: tenantId, type: 'export', resource,
    status: 'processing', total_items: 0, processed_items: 0, failed_items: 0,
    errors: '[]', created_at: now, completed_at: null,
  });

  try {
    let data = '';
    if (resource === 'missions') data = await exportMissions(db, tenantId, format, options?.filters);
    else if (resource === 'api_keys') data = await exportApiKeys(db, tenantId, format);
    else data = format === 'json' ? '[]' : '';

    const rowCount = format === 'csv'
      ? Math.max(0, data.split('\n').length - 1)
      : (JSON.parse(data || '[]') as unknown[]).length;

    await updateJob(db, jobId, {
      status: 'completed', processed_items: rowCount, failed_items: 0,
      errors: [], result_data: data, completed_at: new Date().toISOString(),
    });
  } catch (err) {
    await updateJob(db, jobId, {
      status: 'failed', errors: [err instanceof Error ? err.message : 'export failed'],
      completed_at: new Date().toISOString(),
    });
  }

  return getBulkJob(db, tenantId, jobId) as Promise<BulkJob>;
}

/** Create and run an import job synchronously */
export async function createBulkImport(
  db: D1Database, tenantId: string, resource: BulkJob['resource'], items: Record<string, unknown>[]
): Promise<BulkJob> {
  const jobId = crypto.randomUUID();
  const now = new Date().toISOString();

  if (items.length > 500) throw new Error('Max 500 items per import batch');

  await saveJob(db, {
    id: jobId, tenant_id: tenantId, type: 'import', resource,
    status: 'processing', total_items: items.length, processed_items: 0, failed_items: 0,
    errors: '[]', created_at: now, completed_at: null,
  });

  try {
    let result: ImportResult = { imported: 0, failed: 0, errors: [] };
    if (resource === 'missions') result = await importMissions(db, tenantId, items);
    else result = { imported: 0, failed: items.length, errors: [`Import not supported for resource: ${resource}`] };

    await updateJob(db, jobId, {
      status: result.failed === items.length && items.length > 0 ? 'failed' : 'completed',
      processed_items: result.imported, failed_items: result.failed, errors: result.errors,
      completed_at: new Date().toISOString(),
    });
  } catch (err) {
    await updateJob(db, jobId, {
      status: 'failed', errors: [err instanceof Error ? err.message : 'import failed'],
      completed_at: new Date().toISOString(),
    });
  }

  return getBulkJob(db, tenantId, jobId) as Promise<BulkJob>;
}

/** Get a single bulk job (validates tenant ownership) */
export async function getBulkJob(db: D1Database, tenantId: string, jobId: string): Promise<BulkJob | null> {
  const row = await db.prepare(
    'SELECT id, tenant_id, type, resource, status, total_items, processed_items, failed_items, errors, created_at, completed_at FROM bulk_jobs WHERE id = ? AND tenant_id = ?'
  ).bind(jobId, tenantId).first<BulkJobRow>();
  return row ? parseBulkJob(row) : null;
}

/** List bulk jobs for a tenant with optional filters */
export async function listBulkJobs(
  db: D1Database, tenantId: string,
  options?: { type?: string; resource?: string; limit?: number }
): Promise<BulkJob[]> {
  const limit = Math.min(options?.limit ?? 20, 100);
  let query = 'SELECT id, tenant_id, type, resource, status, total_items, processed_items, failed_items, errors, created_at, completed_at FROM bulk_jobs WHERE tenant_id = ?';
  const params: unknown[] = [tenantId];
  if (options?.type)     { query += ' AND type = ?';     params.push(options.type); }
  if (options?.resource) { query += ' AND resource = ?'; params.push(options.resource); }
  query += ` ORDER BY created_at DESC LIMIT ${limit}`;

  const result = await db.prepare(query).bind(...params).all<BulkJobRow>();
  return result.results.map(parseBulkJob);
}

/** Cancel a pending/processing job */
export async function cancelBulkJob(db: D1Database, tenantId: string, jobId: string): Promise<{ success: boolean; error?: string }> {
  const job = await getBulkJob(db, tenantId, jobId);
  if (!job) return { success: false, error: 'Job not found' };
  if (!['pending', 'processing'].includes(job.status)) {
    return { success: false, error: `Cannot cancel job in status: ${job.status}` };
  }
  await db.prepare(
    `UPDATE bulk_jobs SET status='failed', errors=?, completed_at=? WHERE id=?`
  ).bind(JSON.stringify(['Cancelled by user']), new Date().toISOString(), jobId).run();
  return { success: true };
}

/** Aggregate stats for a tenant's bulk jobs */
export async function getBulkStats(db: D1Database, tenantId: string): Promise<{
  total_jobs: number;
  total_exported: number;
  total_imported: number;
  by_resource: Record<string, { exports: number; imports: number }>;
}> {
  const rows = await db.prepare(
    `SELECT type, resource, SUM(processed_items) as total FROM bulk_jobs WHERE tenant_id = ? AND status = 'completed' GROUP BY type, resource`
  ).bind(tenantId).all<{ type: string; resource: string; total: number }>();

  const by_resource: Record<string, { exports: number; imports: number }> = {};
  let total_exported = 0;
  let total_imported = 0;

  for (const row of rows.results) {
    if (!by_resource[row.resource]) by_resource[row.resource] = { exports: 0, imports: 0 };
    if (row.type === 'export') { by_resource[row.resource].exports += row.total; total_exported += row.total; }
    else { by_resource[row.resource].imports += row.total; total_imported += row.total; }
  }

  const countRow = await db.prepare('SELECT COUNT(*) as c FROM bulk_jobs WHERE tenant_id = ?').bind(tenantId).first<{ c: number }>();
  return { total_jobs: countRow?.c ?? 0, total_exported, total_imported, by_resource };
}
