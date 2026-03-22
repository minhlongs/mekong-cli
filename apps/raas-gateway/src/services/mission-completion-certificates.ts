/**
 * Mission Completion Certificates Service
 * Handles issuance, listing, and admin overview of mission completion certificates
 */

/**
 * List all certificates for a tenant
 */
async function listCertificates(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, mission_id, certificate_number, issued_to,
                issued_at, expires_at, verification_hash, created_at
         FROM mission_completion_certificates
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();
    return { success: true, data: result.results };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to list certificates';
    return { success: false, error };
  }
}

/**
 * Issue a new completion certificate for a mission
 * Required: mission_id, issued_to
 */
async function createCertificate(
  db: any,
  tenantId: string,
  payload: {
    mission_id: string;
    issued_to: string;
    expires_at?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    // Certificate number: CERT-<timestamp>-<random suffix>
    const certNumber = `CERT-${Date.now()}-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;
    // Simple verification hash: hex digest of id + tenant + mission
    const raw = `${id}:${tenantId}:${payload.mission_id}`;
    const encoder = new TextEncoder();
    const hashBuf = await crypto.subtle.digest('SHA-256', encoder.encode(raw));
    const verificationHash = Array.from(new Uint8Array(hashBuf))
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('');

    await db
      .prepare(
        `INSERT INTO mission_completion_certificates
           (id, tenant_id, mission_id, certificate_number, issued_to, expires_at, verification_hash)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        payload.mission_id,
        certNumber,
        payload.issued_to,
        payload.expires_at ?? null,
        verificationHash
      )
      .run();

    const cert = await db
      .prepare('SELECT * FROM mission_completion_certificates WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: cert };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to create certificate';
    return { success: false, error };
  }
}

/**
 * List certificate templates for a tenant
 */
async function getTemplates(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const result = await db
      .prepare(
        `SELECT id, tenant_id, template_name, logo_url, created_at, updated_at
         FROM mission_certificate_templates
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();
    return { success: true, data: result.results };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to list templates';
    return { success: false, error };
  }
}

/**
 * Admin overview — aggregate counts across all tenants
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [certStats, templateStats, recentCerts] = await Promise.all([
      db
        .prepare(
          `SELECT COUNT(*) as total_certificates,
                  COUNT(DISTINCT tenant_id) as tenants_with_certificates,
                  COUNT(DISTINCT mission_id) as unique_missions_certified
           FROM mission_completion_certificates`
        )
        .first(),
      db
        .prepare(
          `SELECT COUNT(*) as total_templates,
                  COUNT(DISTINCT tenant_id) as tenants_with_templates
           FROM mission_certificate_templates`
        )
        .first(),
      db
        .prepare(
          `SELECT id, tenant_id, mission_id, certificate_number, issued_to, issued_at
           FROM mission_completion_certificates
           ORDER BY created_at DESC LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        certificates: certStats,
        templates: templateStats,
        recent_certificates: recentCerts.results,
      },
    };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to get admin overview';
    return { success: false, error };
  }
}

export const missionCompletionCertificatesService = {
  listCertificates,
  createCertificate,
  getTemplates,
  getAdminOverview,
};
