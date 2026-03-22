/**
 * Mission Artifact Storage Service — list, create, and audit artifact downloads per tenant
 */

export interface MissionArtifact {
  id: string;
  tenant_id: string;
  mission_id: string;
  artifact_type: string;
  file_name: string;
  file_size: number;
  storage_path: string;
  content_type: string;
  created_at: string;
}

export interface ArtifactDownload {
  id: string;
  tenant_id: string;
  artifact_id: string;
  downloaded_by: string;
  ip_address: string;
  downloaded_at: string;
}

interface CreateArtifactData {
  mission_id: string;
  artifact_type?: string;
  file_name: string;
  file_size?: number;
  storage_path: string;
  content_type: string;
}

/**
 * List all artifacts for a tenant, optionally filtered by mission
 */
async function listArtifacts(
  db: any,
  tenantId: string,
  missionId?: string
): Promise<MissionArtifact[]> {
  const rows = missionId
    ? await db
        .prepare('SELECT * FROM mission_artifacts WHERE tenant_id = ? AND mission_id = ? ORDER BY created_at DESC')
        .bind(tenantId, missionId)
        .all()
    : await db
        .prepare('SELECT * FROM mission_artifacts WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
  return (rows.results ?? []) as MissionArtifact[];
}

/**
 * Create a new artifact record for a mission (tenant-scoped)
 */
async function createArtifact(
  db: any,
  tenantId: string,
  data: CreateArtifactData
): Promise<MissionArtifact> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const artifactType = data.artifact_type ?? 'output';
  const fileSize = data.file_size ?? 0;

  await db
    .prepare(
      `INSERT INTO mission_artifacts (id, tenant_id, mission_id, artifact_type, file_name, file_size, storage_path, content_type, created_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
    )
    .bind(id, tenantId, data.mission_id, artifactType, data.file_name, fileSize, data.storage_path, data.content_type, now)
    .run();

  return {
    id, tenant_id: tenantId, mission_id: data.mission_id,
    artifact_type: artifactType, file_name: data.file_name,
    file_size: fileSize, storage_path: data.storage_path,
    content_type: data.content_type, created_at: now,
  };
}

/**
 * List download events for an artifact (tenant-scoped)
 */
async function getDownloads(db: any, tenantId: string, artifactId: string): Promise<ArtifactDownload[]> {
  const rows = await db
    .prepare('SELECT * FROM artifact_downloads WHERE tenant_id = ? AND artifact_id = ? ORDER BY downloaded_at DESC')
    .bind(tenantId, artifactId)
    .all();
  return (rows.results ?? []) as ArtifactDownload[];
}

/**
 * Admin overview: artifact counts and total storage across all tenants
 */
async function getAdminOverview(db: any): Promise<Record<string, unknown>> {
  const [summary, topTenants] = await Promise.all([
    db.prepare(
      `SELECT COUNT(*) as total_artifacts, COALESCE(SUM(file_size),0) as total_bytes,
       COUNT(DISTINCT tenant_id) as tenant_count, COUNT(DISTINCT mission_id) as mission_count
       FROM mission_artifacts`
    ).first(),
    db.prepare(
      `SELECT tenant_id, COUNT(*) as artifact_count, COALESCE(SUM(file_size),0) as bytes_used
       FROM mission_artifacts GROUP BY tenant_id ORDER BY bytes_used DESC LIMIT 10`
    ).all(),
  ]) as [any, any];

  return {
    summary: summary ?? {},
    top_tenants_by_storage: topTenants?.results ?? [],
  };
}

export const missionArtifactStorageService = {
  listArtifacts,
  createArtifact,
  getDownloads,
  getAdminOverview,
};
