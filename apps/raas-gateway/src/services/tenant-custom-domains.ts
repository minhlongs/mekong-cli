/**
 * Tenant Custom Domains Service
 * Manages custom domain registration, verification, and admin overview for tenants
 */

// --- helpers ---

function nowIso(): string {
  return new Date().toISOString();
}

function randomId(): string {
  return crypto.randomUUID();
}

// --- list domains for a tenant ---

async function listDomains(db: any, tenantId: string) {
  try {
    const rows = await db
      .prepare(
        `SELECT id, tenant_id, domain, ssl_status, verified, dns_record, created_at, updated_at
         FROM tenant_custom_domains
         WHERE tenant_id = ?
         ORDER BY created_at DESC`
      )
      .bind(tenantId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantCustomDomainsService] listDomains error:', err);
    return { success: false, error: 'Failed to list domains' };
  }
}

// --- create a custom domain record ---

async function createDomain(db: any, tenantId: string, domain: string, dnsRecord?: string) {
  try {
    const id = randomId();
    const now = nowIso();

    await db
      .prepare(
        `INSERT INTO tenant_custom_domains (id, tenant_id, domain, ssl_status, verified, dns_record, created_at, updated_at)
         VALUES (?, ?, ?, 'pending', 0, ?, ?, ?)`
      )
      .bind(id, tenantId, domain, dnsRecord ?? null, now, now)
      .run();

    // Create initial verification record
    const verificationId = randomId();
    const verificationToken = crypto.randomUUID().replace(/-/g, '');

    await db
      .prepare(
        `INSERT INTO tenant_domain_verifications (id, tenant_id, domain_id, verification_type, verification_token, created_at)
         VALUES (?, ?, ?, 'dns', ?, ?)`
      )
      .bind(verificationId, tenantId, id, verificationToken, now)
      .run();

    return {
      success: true,
      data: {
        id,
        tenant_id: tenantId,
        domain,
        ssl_status: 'pending',
        verified: 0,
        dns_record: dnsRecord ?? null,
        verification_token: verificationToken,
        created_at: now,
        updated_at: now,
      },
    };
  } catch (err) {
    console.error('[tenantCustomDomainsService] createDomain error:', err);
    return { success: false, error: 'Failed to create domain' };
  }
}

// --- get verifications for a domain ---

async function getVerifications(db: any, tenantId: string, domainId: string) {
  try {
    // Confirm domain belongs to tenant
    const domain = await db
      .prepare(
        `SELECT id FROM tenant_custom_domains WHERE id = ? AND tenant_id = ?`
      )
      .bind(domainId, tenantId)
      .first();

    if (!domain) {
      return { success: false, error: 'Domain not found' };
    }

    const rows = await db
      .prepare(
        `SELECT id, tenant_id, domain_id, verification_type, verification_token, verified_at, created_at
         FROM tenant_domain_verifications
         WHERE domain_id = ?
         ORDER BY created_at DESC`
      )
      .bind(domainId)
      .all();

    return { success: true, data: rows.results ?? [] };
  } catch (err) {
    console.error('[tenantCustomDomainsService] getVerifications error:', err);
    return { success: false, error: 'Failed to get verifications' };
  }
}

// --- admin: platform-wide domain overview ---

async function getAdminOverview(db: any) {
  try {
    const [totals, pendingRows, recentRows] = await Promise.all([
      db
        .prepare(
          `SELECT
            COUNT(*) as total,
            SUM(verified) as verified_count,
            SUM(CASE WHEN ssl_status = 'active' THEN 1 ELSE 0 END) as ssl_active,
            SUM(CASE WHEN ssl_status = 'pending' THEN 1 ELSE 0 END) as ssl_pending,
            SUM(CASE WHEN ssl_status = 'failed' THEN 1 ELSE 0 END) as ssl_failed
           FROM tenant_custom_domains`
        )
        .first(),

      db
        .prepare(
          `SELECT d.id, d.tenant_id, d.domain, d.ssl_status, d.created_at
           FROM tenant_custom_domains d
           WHERE d.verified = 0
           ORDER BY d.created_at DESC
           LIMIT 20`
        )
        .all(),

      db
        .prepare(
          `SELECT d.id, d.tenant_id, d.domain, d.ssl_status, d.verified, d.created_at
           FROM tenant_custom_domains d
           ORDER BY d.created_at DESC
           LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        summary: totals,
        pending_verification: pendingRows.results ?? [],
        recent_domains: recentRows.results ?? [],
      },
    };
  } catch (err) {
    console.error('[tenantCustomDomainsService] getAdminOverview error:', err);
    return { success: false, error: 'Failed to get admin overview' };
  }
}

export const tenantCustomDomainsService = {
  listDomains,
  createDomain,
  getVerifications,
  getAdminOverview,
};
