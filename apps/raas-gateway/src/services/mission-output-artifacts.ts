/**
 * Mission Output Artifacts Service
 * CRUD for mission_output_artifacts + download tracking + admin overview
 */

// List all artifacts for a tenant, optionally filtered by mission_id
async function listArtifacts(
  db: any,
  tenantId: string,
  missionId?: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = missionId
      ? await db
          .prepare(
            `SELECT * FROM mission_output_artifacts
             WHERE tenant_id = ? AND mission_id = ?
             ORDER BY created_at DESC`
          )
          .bind(tenantId, missionId)
          .all()
      : await db
          .prepare(
            `SELECT * FROM mission_output_artifacts
             WHERE tenant_id = ?
             ORDER BY created_at DESC`
          )
          .bind(tenantId)
          .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Insert a new artifact record for a mission
async function createArtifact(
  db: any,
  payload: {
    id: string;
    tenant_id: string;
    mission_id: string;
    artifact_name: string;
    artifact_type?: string;
    file_url?: string;
    file_size?: number;
    content_type?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const {
      id,
      tenant_id,
      mission_id,
      artifact_name,
      artifact_type = 'file',
      file_url,
      file_size,
      content_type,
    } = payload;

    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO mission_output_artifacts
           (id, tenant_id, mission_id, artifact_name, artifact_type, file_url, file_size, content_type, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenant_id,
        mission_id,
        artifact_name,
        artifact_type,
        file_url ?? null,
        file_size ?? null,
        content_type ?? null,
        now
      )
      .run();

    const created = await db
      .prepare(`SELECT * FROM mission_output_artifacts WHERE id = ?`)
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Record a download event and return full download history for an artifact
async function getDownloads(
  db: any,
  tenantId: string,
  artifactId: string,
  downloadedBy?: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    // Verify artifact belongs to tenant
    const artifact = await db
      .prepare(
        `SELECT id FROM mission_output_artifacts WHERE id = ? AND tenant_id = ?`
      )
      .bind(artifactId, tenantId)
      .first();

    if (!artifact) {
      return { success: false, error: 'Artifact not found' };
    }

    // Record download
    const downloadId = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO mission_artifact_downloads (id, tenant_id, artifact_id, downloaded_by, downloaded_at)
         VALUES (?, ?, ?, ?, ?)`
      )
      .bind(downloadId, tenantId, artifactId, downloadedBy ?? null, now)
      .run();

    // Return all downloads for this artifact
    const result = await db
      .prepare(
        `SELECT * FROM mission_artifact_downloads WHERE artifact_id = ? ORDER BY downloaded_at DESC`
      )
      .bind(artifactId)
      .all();

    return { success: true, data: result.results ?? [] };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Admin overview — aggregate counts across all tenants
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const totals = await db
      .prepare(
        `SELECT
           COUNT(*) AS total_artifacts,
           COUNT(DISTINCT tenant_id) AS total_tenants,
           COUNT(DISTINCT mission_id) AS total_missions,
           SUM(file_size) AS total_bytes
         FROM mission_output_artifacts`
      )
      .first();

    const downloadCount = await db
      .prepare(`SELECT COUNT(*) AS total_downloads FROM mission_artifact_downloads`)
      .first();

    const byType = await db
      .prepare(
        `SELECT artifact_type, COUNT(*) AS cnt
         FROM mission_output_artifacts
         GROUP BY artifact_type
         ORDER BY cnt DESC`
      )
      .all();

    return {
      success: true,
      data: {
        total_artifacts: totals?.total_artifacts ?? 0,
        total_tenants: totals?.total_tenants ?? 0,
        total_missions: totals?.total_missions ?? 0,
        total_bytes: totals?.total_bytes ?? 0,
        total_downloads: downloadCount?.total_downloads ?? 0,
        by_type: byType?.results ?? [],
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const missionOutputArtifactsService = {
  listArtifacts,
  createArtifact,
  getDownloads,
  getAdminOverview,
};
