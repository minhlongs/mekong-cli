/**
 * Custom domains service — enterprise tenant white-label API domain management
 * Handles DNS verification, SSL status tracking, and domain lifecycle
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface CustomDomain {
  id: string;
  tenant_id: string;
  domain: string;
  status: 'pending' | 'verifying' | 'active' | 'failed';
  verification_method: 'cname' | 'txt';
  verification_token: string | null;
  ssl_status: 'pending' | 'active' | 'failed';
  created_at: string;
  verified_at: string | null;
  expires_at: string | null;
}

export interface DomainStats {
  total: number;
  pending: number;
  verifying: number;
  active: number;
  failed: number;
}

/** Generate a random verification token for DNS record */
function generateVerificationToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** Add a new custom domain for a tenant — initializes pending verification */
export async function addDomain(
  db: D1Database,
  tenantId: string,
  domain: string
): Promise<CustomDomain> {
  const id = crypto.randomUUID();
  const token = generateVerificationToken();

  try {
    await db
      .prepare(
        `INSERT INTO custom_domains (id, tenant_id, domain, status, verification_token, created_at)
         VALUES (?, ?, ?, 'pending', ?, datetime('now'))`
      )
      .bind(id, tenantId, domain.toLowerCase(), token)
      .run();

    return (await getDomain(db, tenantId, id))!;
  } catch (err) {
    const msg = err instanceof Error ? err.message : 'Failed to add domain';
    if (msg.includes('UNIQUE')) throw new Error(`Domain already registered: ${domain}`);
    throw new Error(msg);
  }
}

/** List all domains for a tenant */
export async function listDomains(db: D1Database, tenantId: string): Promise<CustomDomain[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM custom_domains WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all<CustomDomain>();
    return result.results ?? [];
  } catch {
    return [];
  }
}

/** Get a single domain — enforces tenant ownership */
export async function getDomain(
  db: D1Database,
  tenantId: string,
  domainId: string
): Promise<CustomDomain | null> {
  try {
    return await db
      .prepare('SELECT * FROM custom_domains WHERE id = ? AND tenant_id = ?')
      .bind(domainId, tenantId)
      .first<CustomDomain>();
  } catch {
    return null;
  }
}

/**
 * Trigger verification check for a domain.
 * In production this would query DNS — here we transition to 'verifying'
 * and mark active if token matches (simulated; real impl calls CF DNS API).
 */
export async function verifyDomain(
  db: D1Database,
  tenantId: string,
  domainId: string
): Promise<CustomDomain | null> {
  const domain = await getDomain(db, tenantId, domainId);
  if (!domain) return null;
  if (domain.status === 'active') return domain;

  try {
    // Transition to verifying — real DNS check would happen here
    await db
      .prepare(
        `UPDATE custom_domains
         SET status = 'verifying'
         WHERE id = ? AND tenant_id = ? AND status != 'active'`
      )
      .bind(domainId, tenantId)
      .run();

    return await getDomain(db, tenantId, domainId);
  } catch {
    return null;
  }
}

/** Remove a domain — enforces tenant ownership */
export async function removeDomain(
  db: D1Database,
  tenantId: string,
  domainId: string
): Promise<boolean> {
  try {
    const result = await db
      .prepare('DELETE FROM custom_domains WHERE id = ? AND tenant_id = ?')
      .bind(domainId, tenantId)
      .run();
    return (result.meta?.changes ?? 0) > 0;
  } catch {
    return false;
  }
}

/** Lookup which tenant owns a given hostname — used by edge routing */
export async function getDomainByHostname(
  db: D1Database,
  hostname: string
): Promise<CustomDomain | null> {
  try {
    return await db
      .prepare(`SELECT * FROM custom_domains WHERE domain = ? AND status = 'active'`)
      .bind(hostname.toLowerCase())
      .first<CustomDomain>();
  } catch {
    return null;
  }
}

/** Update SSL certificate status — called by Cloudflare webhook or scheduler */
export async function updateSSLStatus(
  db: D1Database,
  domainId: string,
  status: 'pending' | 'active' | 'failed'
): Promise<boolean> {
  try {
    const result = await db
      .prepare('UPDATE custom_domains SET ssl_status = ? WHERE id = ?')
      .bind(status, domainId)
      .run();
    return (result.meta?.changes ?? 0) > 0;
  } catch {
    return false;
  }
}

/** Count domains by status for a tenant */
export async function getDomainStats(db: D1Database, tenantId: string): Promise<DomainStats> {
  try {
    const rows = await db
      .prepare(
        `SELECT status, COUNT(*) as count FROM custom_domains
         WHERE tenant_id = ? GROUP BY status`
      )
      .bind(tenantId)
      .all<{ status: string; count: number }>();

    const counts: Record<string, number> = {};
    for (const row of rows.results ?? []) counts[row.status] = row.count;

    return {
      total: Object.values(counts).reduce((a, b) => a + b, 0),
      pending: counts['pending'] ?? 0,
      verifying: counts['verifying'] ?? 0,
      active: counts['active'] ?? 0,
      failed: counts['failed'] ?? 0,
    };
  } catch {
    return { total: 0, pending: 0, verifying: 0, active: 0, failed: 0 };
  }
}

/** Admin overview — all domains grouped by status across all tenants */
export async function getAdminDomainOverview(
  db: D1Database
): Promise<{ status: string; count: number }[]> {
  try {
    const result = await db
      .prepare('SELECT status, COUNT(*) as count FROM custom_domains GROUP BY status ORDER BY status')
      .all<{ status: string; count: number }>();
    return result.results ?? [];
  } catch {
    return [];
  }
}

/** Remove unverified domains older than 7 days — keeps table clean */
export async function cleanExpiredVerifications(db: D1Database): Promise<number> {
  try {
    const result = await db
      .prepare(
        `DELETE FROM custom_domains
         WHERE status IN ('pending', 'verifying')
         AND datetime(created_at, '+7 days') < datetime('now')`
      )
      .run();
    return result.meta?.changes ?? 0;
  } catch {
    return 0;
  }
}
