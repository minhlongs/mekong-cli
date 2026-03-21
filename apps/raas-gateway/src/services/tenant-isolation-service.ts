/**
 * Tenant Isolation Service — request-scoped data isolation enforcement
 * Prevents cross-tenant data leakage and audits violations
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface IsolationContext {
  tenant_id: string;
  tier: string;
  permissions: string[];
  request_id: string;
  timestamp: string;
}

export interface IsolationViolation {
  id: string;
  tenant_id: string;
  attempted_tenant_id: string;
  endpoint: string;
  action: string;
  created_at: string;
}

interface DataScope {
  table_name: string;
  row_count: number;
}

/**
 * Creates an immutable isolation context for the request lifecycle
 */
export function createIsolationContext(
  tenantId: string,
  tier: string,
  permissions: string[],
  requestId: string
): IsolationContext {
  return Object.freeze({
    tenant_id: tenantId,
    tier,
    permissions: [...permissions],
    request_id: requestId,
    timestamp: new Date().toISOString(),
  });
}

/**
 * Validates that the current tenant can access target tenant's data
 * Enterprise tenants with 'cross_tenant' permission may access others
 */
export function validateDataAccess(
  ctx: IsolationContext,
  targetTenantId: string
): boolean {
  if (ctx.tenant_id === targetTenantId) return true;
  if (ctx.tier === 'enterprise' && ctx.permissions.includes('cross_tenant')) return true;
  return false;
}

/**
 * Records an isolation violation for security audit trail
 */
export async function recordViolation(
  db: D1Database,
  ctx: IsolationContext,
  targetTenantId: string,
  endpoint: string,
  action: string
): Promise<void> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO isolation_violations (id, tenant_id, attempted_tenant_id, endpoint, action, created_at)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(id, ctx.tenant_id, targetTenantId, endpoint, action, new Date().toISOString()).run();
}

/**
 * Retrieves violation history — admin sees all, tenant sees own only
 */
export async function getViolationHistory(
  db: D1Database,
  tenantId?: string,
  limit = 50
): Promise<IsolationViolation[]> {
  const safeLimit = Math.min(limit, 200);

  if (tenantId) {
    const { results } = await db.prepare(
      `SELECT * FROM isolation_violations WHERE tenant_id = ?
       ORDER BY created_at DESC LIMIT ?`
    ).bind(tenantId, safeLimit).all<IsolationViolation>();
    return results;
  }

  const { results } = await db.prepare(
    `SELECT * FROM isolation_violations ORDER BY created_at DESC LIMIT ?`
  ).bind(safeLimit).all<IsolationViolation>();
  return results;
}

/**
 * Calculates isolation health score (100 = clean, -10 per violation)
 */
export async function getIsolationScore(
  db: D1Database,
  tenantId: string
): Promise<number> {
  const { results } = await db.prepare(
    `SELECT COUNT(*) as count FROM isolation_violations WHERE tenant_id = ?`
  ).bind(tenantId).all<{ count: number }>();

  const count = results[0]?.count ?? 0;
  return Math.max(0, 100 - count * 10);
}

/**
 * Returns tables and row counts scoped to this tenant
 */
export async function getTenantDataScope(
  db: D1Database,
  tenantId: string
): Promise<DataScope[]> {
  const tables = ['missions', 'api_keys', 'team_members', 'credit_transactions'];
  const scopes: DataScope[] = [];

  for (const table of tables) {
    try {
      const { results } = await db.prepare(
        `SELECT COUNT(*) as row_count FROM ${table} WHERE tenant_id = ?`
      ).bind(tenantId).all<{ row_count: number }>();
      scopes.push({ table_name: table, row_count: results[0]?.row_count ?? 0 });
    } catch {
      // Table may not exist in all migrations — skip silently
      scopes.push({ table_name: table, row_count: 0 });
    }
  }

  return scopes;
}
