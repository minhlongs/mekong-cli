/**
 * Tenant API Versioning Service — manage per-tenant API versions and endpoint mappings
 * Functions: listVersions, createVersion, getMappings, getAdminOverview
 */

function newId(): string {
  return crypto.randomUUID();
}

/** List all API versions for a tenant */
export async function listVersions(db: any, tenantId: string): Promise<any[]> {
  try {
    const { results } = await db
      .prepare('SELECT * FROM api_versions WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return results;
  } catch (err: any) {
    throw new Error(`Failed to list versions: ${err.message}`);
  }
}

/** Create a new API version for a tenant */
export async function createVersion(
  db: any,
  tenantId: string,
  data: {
    version_label: string;
    base_url: string;
    is_default?: number;
    is_deprecated?: number;
    deprecation_date?: string;
  }
): Promise<any> {
  try {
    const id = newId();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO api_versions (id, tenant_id, version_label, base_url, is_default, is_deprecated, deprecation_date, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        data.version_label,
        data.base_url,
        data.is_default ?? 0,
        data.is_deprecated ?? 0,
        data.deprecation_date ?? null,
        now,
        now
      )
      .run();
    return db.prepare('SELECT * FROM api_versions WHERE id = ?').bind(id).first();
  } catch (err: any) {
    throw new Error(`Failed to create version: ${err.message}`);
  }
}

/** List all endpoint mappings for a tenant */
export async function getMappings(db: any, tenantId: string): Promise<any[]> {
  try {
    const { results } = await db
      .prepare('SELECT * FROM api_version_mappings WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return results;
  } catch (err: any) {
    throw new Error(`Failed to get mappings: ${err.message}`);
  }
}

/** Admin overview — counts of versions and mappings across all tenants */
export async function getAdminOverview(db: any): Promise<any> {
  try {
    const totalVersionsRow = await db
      .prepare('SELECT COUNT(*) as total FROM api_versions')
      .first();
    const totalMappingsRow = await db
      .prepare('SELECT COUNT(*) as total FROM api_version_mappings')
      .first();
    const { results: tenantCounts } = await db
      .prepare(
        `SELECT tenant_id, COUNT(*) as version_count
         FROM api_versions GROUP BY tenant_id ORDER BY version_count DESC LIMIT 20`
      )
      .all();
    return {
      totalVersions: totalVersionsRow?.total ?? 0,
      totalMappings: totalMappingsRow?.total ?? 0,
      tenantCounts,
    };
  } catch (err: any) {
    throw new Error(`Failed to get admin overview: ${err.message}`);
  }
}

export const tenantApiVersioningService = {
  listVersions,
  createVersion,
  getMappings,
  getAdminOverview,
};
