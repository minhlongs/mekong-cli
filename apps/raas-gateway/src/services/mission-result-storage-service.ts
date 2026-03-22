/**
 * Mission Result Storage Service — store, version, and retrieve mission results + attachments
 */

interface StoreResultData {
  result_type?: string;
  content?: string;
  metadata_json?: string;
}

interface AddAttachmentData {
  filename: string;
  content_type?: string;
  size_bytes?: number;
  storage_url?: string;
  checksum?: string;
}

export interface MissionResult {
  id: string;
  tenant_id: string;
  mission_id: string;
  result_type: string;
  content: string | null;
  metadata_json: string;
  version: number;
  size_bytes: number;
  created_at: string;
}

export interface ResultAttachment {
  id: string;
  result_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  storage_url: string | null;
  checksum: string | null;
  created_at: string;
}

/**
 * Get next version number for a mission's results
 */
async function getNextVersion(db: any, missionId: string): Promise<number> {
  const row = (await db
    .prepare('SELECT MAX(version) as max_ver FROM mission_results WHERE mission_id = ?')
    .bind(missionId)
    .first()) as { max_ver: number | null } | null;
  return (row?.max_ver ?? 0) + 1;
}

/**
 * Store a new versioned result for a mission (tenant-scoped)
 */
async function storeResult(
  db: any,
  tenantId: string,
  missionId: string,
  data: StoreResultData
): Promise<MissionResult> {
  const id = crypto.randomUUID();
  const version = await getNextVersion(db, missionId);
  const content = data.content ?? null;
  const sizeBytes = content ? new TextEncoder().encode(content).length : 0;
  const resultType = data.result_type ?? 'text';
  const metadataJson = data.metadata_json ?? '{}';
  const now = new Date().toISOString();

  await db
    .prepare(
      `INSERT INTO mission_results (id, tenant_id, mission_id, result_type, content, metadata_json, version, size_bytes, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(id, tenantId, missionId, resultType, content, metadataJson, version, sizeBytes, now)
    .run();

  return { id, tenant_id: tenantId, mission_id: missionId, result_type: resultType, content, metadata_json: metadataJson, version, size_bytes: sizeBytes, created_at: now };
}

/**
 * Get latest result for a mission (tenant-scoped)
 */
async function getResult(db: any, tenantId: string, missionId: string): Promise<MissionResult | null> {
  return (await db
    .prepare('SELECT * FROM mission_results WHERE tenant_id = ? AND mission_id = ? ORDER BY version DESC LIMIT 1')
    .bind(tenantId, missionId)
    .first()) as MissionResult | null;
}

/**
 * List all versions for a mission (tenant-scoped)
 */
async function getResultVersions(db: any, tenantId: string, missionId: string): Promise<MissionResult[]> {
  const rows = await db
    .prepare('SELECT * FROM mission_results WHERE tenant_id = ? AND mission_id = ? ORDER BY version ASC')
    .bind(tenantId, missionId)
    .all();
  return (rows.results ?? []) as MissionResult[];
}

/**
 * Get specific version of a mission result (tenant-scoped)
 */
async function getResultByVersion(db: any, tenantId: string, missionId: string, version: number): Promise<MissionResult | null> {
  return (await db
    .prepare('SELECT * FROM mission_results WHERE tenant_id = ? AND mission_id = ? AND version = ?')
    .bind(tenantId, missionId, version)
    .first()) as MissionResult | null;
}

/**
 * Add attachment metadata to a result
 */
async function addAttachment(db: any, resultId: string, data: AddAttachmentData): Promise<ResultAttachment> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const contentType = data.content_type ?? 'application/octet-stream';
  const sizeBytes = data.size_bytes ?? 0;

  await db
    .prepare(
      `INSERT INTO result_attachments (id, result_id, filename, content_type, size_bytes, storage_url, checksum, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(id, resultId, data.filename, contentType, sizeBytes, data.storage_url ?? null, data.checksum ?? null, now)
    .run();

  return { id, result_id: resultId, filename: data.filename, content_type: contentType, size_bytes: sizeBytes, storage_url: data.storage_url ?? null, checksum: data.checksum ?? null, created_at: now };
}

/**
 * List all attachments for a result
 */
async function listAttachments(db: any, resultId: string): Promise<ResultAttachment[]> {
  const rows = await db
    .prepare('SELECT * FROM result_attachments WHERE result_id = ? ORDER BY created_at ASC')
    .bind(resultId)
    .all();
  return (rows.results ?? []) as ResultAttachment[];
}

/**
 * Delete an attachment by id — returns true if a row was removed
 */
async function deleteAttachment(db: any, id: string): Promise<boolean> {
  const result = await db
    .prepare('DELETE FROM result_attachments WHERE id = ?')
    .bind(id)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

/**
 * Storage stats for a tenant
 */
async function getStorageStats(db: any, tenantId: string): Promise<Record<string, unknown>> {
  const [results, attachments] = await Promise.all([
    db.prepare(
      `SELECT COUNT(*) as total_results, COALESCE(SUM(size_bytes),0) as total_bytes,
       COUNT(DISTINCT mission_id) as missions_with_results
       FROM mission_results WHERE tenant_id = ?`
    ).bind(tenantId).first(),
    db.prepare(
      `SELECT COUNT(*) as total_attachments, COALESCE(SUM(ra.size_bytes),0) as attachment_bytes
       FROM result_attachments ra
       JOIN mission_results mr ON ra.result_id = mr.id
       WHERE mr.tenant_id = ?`
    ).bind(tenantId).first(),
  ]) as [any, any];

  return {
    total_results: results?.total_results ?? 0,
    total_bytes: results?.total_bytes ?? 0,
    missions_with_results: results?.missions_with_results ?? 0,
    total_attachments: attachments?.total_attachments ?? 0,
    attachment_bytes: attachments?.attachment_bytes ?? 0,
  };
}

/**
 * Admin overview across all tenants
 */
async function getAdminOverview(db: any): Promise<Record<string, unknown>> {
  const [summary, topTenants] = await Promise.all([
    db.prepare(
      `SELECT COUNT(*) as total_results, COALESCE(SUM(size_bytes),0) as total_bytes,
       COUNT(DISTINCT tenant_id) as tenant_count, COUNT(DISTINCT mission_id) as mission_count
       FROM mission_results`
    ).first(),
    db.prepare(
      `SELECT tenant_id, COUNT(*) as result_count, COALESCE(SUM(size_bytes),0) as bytes_used
       FROM mission_results GROUP BY tenant_id ORDER BY bytes_used DESC LIMIT 10`
    ).all(),
  ]) as [any, any];

  return {
    summary: summary ?? {},
    top_tenants_by_storage: topTenants?.results ?? [],
  };
}

export const missionResultStorageService = {
  storeResult,
  getResult,
  getResultVersions,
  getResultByVersion,
  addAttachment,
  listAttachments,
  deleteAttachment,
  getStorageStats,
  getAdminOverview,
};
