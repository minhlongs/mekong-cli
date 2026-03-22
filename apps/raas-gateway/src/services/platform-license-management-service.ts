/**
 * Platform License Management Service — CRUD for platform_licenses + license_activations tables
 */

/** List all licenses, optionally filtered by tenant_id or status query params */
async function listLicenses(db: any, tenantId?: string, status?: string) {
  try {
    let query = 'SELECT * FROM platform_licenses WHERE 1=1';
    const params: string[] = [];
    if (tenantId) { query += ' AND tenant_id = ?'; params.push(tenantId); }
    if (status) { query += ' AND status = ?'; params.push(status); }
    query += ' ORDER BY issued_at DESC LIMIT 100';
    const result = await db.prepare(query).bind(...params).all();
    return (result.results as any[]);
  } catch (e: any) {
    throw new Error(`listLicenses failed: ${e.message}`);
  }
}

/** Create a new license record */
async function createLicense(db: any, data: {
  id: string;
  license_key: string;
  tenant_id?: string;
  license_type?: string;
  features_json?: string;
  max_users?: number;
  expires_at?: string;
}) {
  try {
    await db.prepare(
      `INSERT INTO platform_licenses (id, license_key, tenant_id, license_type, features_json, max_users, expires_at)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(
      data.id,
      data.license_key,
      data.tenant_id ?? null,
      data.license_type ?? 'standard',
      data.features_json ?? '{}',
      data.max_users ?? 10,
      data.expires_at ?? null
    ).run();
    const created = await db.prepare('SELECT * FROM platform_licenses WHERE id = ?').bind(data.id).first();
    return created as any;
  } catch (e: any) {
    throw new Error(`createLicense failed: ${e.message}`);
  }
}

/** Get activations for a license */
async function getActivations(db: any, licenseId: string) {
  try {
    const result = await db.prepare(
      'SELECT * FROM license_activations WHERE license_id = ? ORDER BY activated_at DESC'
    ).bind(licenseId).all();
    return (result.results as any[]);
  } catch (e: any) {
    throw new Error(`getActivations failed: ${e.message}`);
  }
}

/** Dashboard summary: total, active, expired license counts + activation count */
async function getDashboard(db: any) {
  try {
    const [counts, activationCount] = await Promise.all([
      db.prepare(
        `SELECT
          COUNT(*) as total,
          SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
          SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired_count,
          SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) as revoked_count
         FROM platform_licenses`
      ).first(),
      db.prepare('SELECT COUNT(*) as total FROM license_activations').first(),
    ]);
    return {
      licenses: counts as any,
      activations: activationCount as any,
    };
  } catch (e: any) {
    throw new Error(`getDashboard failed: ${e.message}`);
  }
}

export const platformLicenseManagementService = {
  listLicenses,
  createLicense,
  getActivations,
  getDashboard,
};
