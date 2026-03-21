/**
 * IP Allowlist Service — tenant-level IP restriction management
 * Logic: no rules = allow all; rules exist = must match one (allowlist mode)
 * Supports exact IP and CIDR notation (/8, /16, /24, /32)
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface IpRule {
  id: string;
  tenant_id: string;
  ip_address: string;
  label: string | null;
  is_active: number;
  created_at: string;
  expires_at: string | null;
}

export interface IpAccessLog {
  id: string;
  tenant_id: string;
  ip_address: string;
  action: 'allowed' | 'blocked';
  endpoint: string | null;
  created_at: string;
}

export interface UpdateIpRuleInput {
  label?: string;
  is_active?: boolean;
  expires_at?: string | null;
}

/** Convert dotted IPv4 to unsigned 32-bit integer */
function ipToNumber(ip: string): number {
  return ip.split('.').reduce((acc, octet) => (acc << 8) + parseInt(octet, 10), 0) >>> 0;
}

/** Check if a single IP matches a CIDR range or exact IP */
export function matchesCidr(ip: string, cidr: string): boolean {
  if (!cidr.includes('/')) return ip === cidr;
  const [network, bitsStr] = cidr.split('/');
  const bits = parseInt(bitsStr, 10);
  const mask = bits === 0 ? 0 : (~(2 ** (32 - bits) - 1)) >>> 0;
  return (ipToNumber(ip) & mask) === (ipToNumber(network) & mask);
}

/** Add a new IP rule for a tenant */
export async function addIpRule(
  db: D1Database,
  tenantId: string,
  ipAddress: string,
  label?: string,
  expiresAt?: string,
): Promise<IpRule> {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO ip_allowlists (id, tenant_id, ip_address, label, is_active, created_at, expires_at)
       VALUES (?, ?, ?, ?, 1, ?, ?)`,
    )
    .bind(id, tenantId, ipAddress, label ?? null, now, expiresAt ?? null)
    .run();
  return { id, tenant_id: tenantId, ip_address: ipAddress, label: label ?? null,
    is_active: 1, created_at: now, expires_at: expiresAt ?? null };
}

/** Remove an IP rule by id (tenant-scoped) */
export async function removeIpRule(db: D1Database, tenantId: string, ruleId: string): Promise<boolean> {
  const result = await db
    .prepare('DELETE FROM ip_allowlists WHERE id = ? AND tenant_id = ?')
    .bind(ruleId, tenantId)
    .run();
  return (result.meta?.changes ?? 0) > 0;
}

/** List all IP rules for a tenant */
export async function listIpRules(db: D1Database, tenantId: string): Promise<IpRule[]> {
  const rows = await db
    .prepare('SELECT * FROM ip_allowlists WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all<IpRule>();
  return rows.results;
}

/** Update label, active status, or expiry for a rule (tenant-scoped) */
export async function updateIpRule(
  db: D1Database,
  tenantId: string,
  ruleId: string,
  updates: UpdateIpRuleInput,
): Promise<IpRule | null> {
  const sets: string[] = [];
  const values: unknown[] = [];
  if (updates.label !== undefined) { sets.push('label = ?'); values.push(updates.label); }
  if (updates.is_active !== undefined) { sets.push('is_active = ?'); values.push(updates.is_active ? 1 : 0); }
  if (updates.expires_at !== undefined) { sets.push('expires_at = ?'); values.push(updates.expires_at); }
  if (sets.length === 0) return null;
  values.push(ruleId, tenantId);
  await db
    .prepare(`UPDATE ip_allowlists SET ${sets.join(', ')} WHERE id = ? AND tenant_id = ?`)
    .bind(...values)
    .run();
  const row = await db
    .prepare('SELECT * FROM ip_allowlists WHERE id = ? AND tenant_id = ?')
    .bind(ruleId, tenantId)
    .first<IpRule>();
  return row ?? null;
}

/** Check if an IP is allowed for a tenant (no active rules = allow all) */
export async function isIpAllowed(db: D1Database, tenantId: string, ipAddress: string): Promise<boolean> {
  const now = new Date().toISOString();
  const rows = await db
    .prepare(
      `SELECT ip_address FROM ip_allowlists
       WHERE tenant_id = ? AND is_active = 1
         AND (expires_at IS NULL OR expires_at > ?)`,
    )
    .bind(tenantId, now)
    .all<{ ip_address: string }>();
  if (rows.results.length === 0) return true; // no rules = allow all
  return rows.results.some(r => matchesCidr(ipAddress, r.ip_address));
}

/** Log an access attempt */
export async function logAccess(
  db: D1Database,
  tenantId: string,
  ipAddress: string,
  action: 'allowed' | 'blocked',
  endpoint?: string,
): Promise<void> {
  const id = crypto.randomUUID();
  await db
    .prepare(
      `INSERT INTO ip_access_logs (id, tenant_id, ip_address, action, endpoint, created_at)
       VALUES (?, ?, ?, ?, ?, datetime('now'))`,
    )
    .bind(id, tenantId, ipAddress, action, endpoint ?? null)
    .run();
}

/** Get paginated access logs for a tenant */
export async function getAccessLogs(
  db: D1Database,
  tenantId: string,
  limit = 50,
  offset = 0,
): Promise<{ logs: IpAccessLog[]; total: number }> {
  const [rows, countRow] = await Promise.all([
    db.prepare(
      'SELECT * FROM ip_access_logs WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?',
    ).bind(tenantId, limit, offset).all<IpAccessLog>(),
    db.prepare('SELECT COUNT(*) as count FROM ip_access_logs WHERE tenant_id = ?')
      .bind(tenantId).first<{ count: number }>(),
  ]);
  return { logs: rows.results, total: countRow?.count ?? 0 };
}

/** Remove all expired rules (admin maintenance) */
export async function cleanExpiredRules(db: D1Database): Promise<number> {
  const now = new Date().toISOString();
  const result = await db
    .prepare('DELETE FROM ip_allowlists WHERE expires_at IS NOT NULL AND expires_at <= ?')
    .bind(now)
    .run();
  return result.meta?.changes ?? 0;
}

/** Count blocked access attempts for a tenant */
export async function getBlockedCount(db: D1Database, tenantId: string): Promise<number> {
  const row = await db
    .prepare("SELECT COUNT(*) as count FROM ip_access_logs WHERE tenant_id = ? AND action = 'blocked'")
    .bind(tenantId)
    .first<{ count: number }>();
  return row?.count ?? 0;
}
