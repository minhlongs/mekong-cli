/**
 * Audit Logging Middleware
 * Tamper-proof logging of all sensitive operations
 *
 * Logs: who, what, when, where, result
 *
 * Compatible with migration 0014 + 0015 schema:
 * - id, tenant_id, user_id, action, resource, resource_id
 * - old_value, new_value, ip_address, user_agent
 * - request_method, request_path, status_code, metadata
 * - created_at
 */

import type { Context, Next } from 'hono'
import type { Bindings } from '../index'

export interface AuditLogEntry {
  id: string
  tenant_id?: string
  user_id?: string
  action: string
  resource?: string
  resource_id?: string
  resource_type?: string
  ip_address?: string
  user_agent?: string
  request_method?: string
  request_path?: string
  status_code?: number
  old_value?: string
  new_value?: string
  metadata?: Record<string, unknown>
  created_at: string
}

/**
 * Create audit log entry in D1 database
 * Compatible with migration 0014 + 0015 schema
 */
export async function logAudit(
  db: D1Database,
  entry: Omit<AuditLogEntry, 'id' | 'created_at'>
): Promise<void> {
  try {
    const id = crypto.randomUUID()
    const created_at = new Date().toISOString()
    const metadata = entry.metadata ? JSON.stringify(entry.metadata) : null
    const old_value = entry.old_value ? JSON.stringify(entry.old_value) : null
    const new_value = entry.new_value ? JSON.stringify(entry.new_value) : null

    await db
      .prepare(`
        INSERT INTO audit_logs (
          id, tenant_id, user_id, action, resource, resource_id,
          ip_address, user_agent, request_method, request_path, status_code,
          old_value, new_value, metadata, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `)
      .bind(
        id,
        entry.tenant_id || null,
        entry.user_id || null,
        entry.action,
        entry.resource || entry.resource_type || null,
        entry.resource_id || null,
        entry.ip_address || null,
        entry.user_agent || null,
        entry.request_method || null,
        entry.request_path || null,
        entry.status_code || null,
        old_value,
        new_value,
        metadata,
        created_at
      )
      .run()
  } catch (error) {
    // Don't fail the request if audit logging fails
    // But log to console for debugging
    console.error('Audit log write failed:', error instanceof Error ? error.message : String(error))
  }
}

/**
 * Query audit logs with filters
 */
export async function queryAuditLogs(
  db: D1Database,
  filters: {
    tenant_id?: string
    action?: string
    resource_type?: string
    resource_id?: string
    start_date?: string
    end_date?: string
    limit?: number
    offset?: number
  }
): Promise<AuditLogEntry[]> {
  let sql = `
    SELECT id, tenant_id, user_id, action, resource_type, resource_id,
           ip_address, user_agent, request_method, request_path, status_code,
           metadata, created_at
    FROM audit_logs
    WHERE 1=1
  `
  const params: (string | number)[] = []

  if (filters.tenant_id) {
    sql += ' AND tenant_id = ?'
    params.push(filters.tenant_id)
  }

  if (filters.action) {
    sql += ' AND action = ?'
    params.push(filters.action)
  }

  if (filters.resource_type) {
    sql += ' AND resource_type = ?'
    params.push(filters.resource_type)
  }

  if (filters.resource_id) {
    sql += ' AND resource_id = ?'
    params.push(filters.resource_id)
  }

  if (filters.start_date) {
    sql += ' AND created_at >= ?'
    params.push(filters.start_date)
  }

  if (filters.end_date) {
    sql += ' AND created_at <= ?'
    params.push(filters.end_date)
  }

  sql += ' ORDER BY created_at DESC'
  sql += ` LIMIT ? OFFSET ?`
  params.push(filters.limit || 100, filters.offset || 0)

  const { results } = await db.prepare(sql).bind(...params).all()

  return results.map((row: any) => ({
    ...row,
    metadata: row.metadata ? JSON.parse(row.metadata) : null,
  }))
}

/**
 * Get single audit log by ID
 */
export async function getAuditLogById(
  db: D1Database,
  id: string
): Promise<AuditLogEntry | null> {
  const row = await db
    .prepare(`
      SELECT id, tenant_id, user_id, action, resource_type, resource_id,
             ip_address, user_agent, request_method, request_path, status_code,
             metadata, created_at
      FROM audit_logs
      WHERE id = ?
    `)
    .bind(id)
    .first()

  if (!row) return null

  return {
    ...row,
    metadata: row.metadata ? JSON.parse(row.metadata) : null,
  }
}

/**
 * Middleware to automatically log all requests
 * Attach to sensitive routes
 */
export function auditMiddleware(options?: {
  /** Actions to log (default: all) */
  actions?: string[]
  /** Skip logging for these paths */
  skipPaths?: string[]
  /** Include request body in metadata (default: false) */
  includeBody?: boolean
  /** Include response body in metadata (default: false) */
  includeResponse?: boolean
}) {
  return async (c: Context<{ Bindings: Bindings }>, next: Next) => {
    const startTime = Date.now()

    // Skip if path is excluded
    if (options?.skipPaths?.some(path => c.req.path.includes(path))) {
      await next()
      return
    }

    // Get tenant from context if available
    let tenantId: string | undefined
    let userId: string | undefined

    try {
      const tenant = c.get('tenant')
      if (tenant) {
        tenantId = tenant.id
      }
    } catch {
      // Tenant not set, continue without it
    }

    // Clone request for body reading (if enabled)
    let requestBody: unknown
    if (options?.includeBody) {
      try {
        const clonedRequest = c.req.raw.clone()
        requestBody = await clonedRequest.json().catch(() => undefined)
      } catch {
        // Ignore body parse errors
      }
    }

    // Process request
    await next()

    // Log after response
    const duration = Date.now() - startTime
    const metadata: Record<string, unknown> = {
      duration_ms: duration,
      timestamp: new Date().toISOString(),
    }

    if (options?.includeBody && requestBody) {
      metadata.request_body = requestBody
    }

    if (options?.includeResponse) {
      try {
        // Note: This may not work for all response types
        metadata.response_status = c.res.status
      } catch {
        // Ignore
      }
    }

    // Determine action from path and method
    const action = `${c.req.method} ${c.req.path}`

    await logAudit(c.env.DB, {
      tenant_id: tenantId,
      user_id: userId,
      action,
      request_method: c.req.method,
      request_path: c.req.path,
      ip_address: c.req.header('X-Forwarded-For') || c.req.header('CF-Connecting-IP'),
      user_agent: c.req.header('User-Agent'),
      status_code: c.res.status,
      metadata,
    })
  }
}

/**
 * Manual audit logging for specific operations
 * Use this for programmatic logging outside middleware
 */
export async function manualAudit(
  db: D1Database,
  data: {
    tenant_id?: string
    user_id?: string
    action: string
    resource_type?: string
    resource_id?: string
    ip_address?: string
    metadata?: Record<string, unknown>
  }
): Promise<void> {
  await logAudit(db, {
    tenant_id: data.tenant_id,
    user_id: data.user_id,
    action: data.action,
    resource_type: data.resource_type,
    resource_id: data.resource_id,
    ip_address: data.ip_address,
    metadata: data.metadata,
  })
}

/**
 * Sensitive action helpers
 */
export const AuditActions = {
  // Authentication
  LOGIN: 'auth.login',
  LOGOUT: 'auth.logout',
  API_KEY_REGENERATE: 'auth.api_key.regenerate',
  PASSWORD_CHANGE: 'auth.password.change',
  MFA_ENABLE: 'auth.mfa.enable',
  MFA_DISABLE: 'auth.mfa.disable',

  // Tenant Management
  TENANT_CREATE: 'tenant.create',
  TENANT_UPDATE: 'tenant.update',
  TENANT_SUSPEND: 'tenant.suspend',
  TENANT_REACTIVATE: 'tenant.reactivate',
  TENANT_DELETE: 'tenant.delete',

  // Billing
  BILLING_UPDATE: 'billing.update',
  PAYMENT_PROCESS: 'billing.payment.process',
  SUBSCRIPTION_CHANGE: 'billing.subscription.change',
  CREDIT_ADJUST: 'billing.credit.adjust',

  // Data Access
  DATA_EXPORT: 'data.export',
  DATA_IMPORT: 'data.import',
  DATA_DELETE: 'data.delete',

  // Configuration
  SETTINGS_UPDATE: 'settings.update',
  CONSTITUTION_UPDATE: 'constitution.update',
  RBAC_CHANGE: 'rbac.change',

  // Security
  WEBHOOK_CREATE: 'security.webhook.create',
  SECRET_ROTATE: 'security.secret.rotate',
  ACCESS_GRANT: 'security.access.grant',
  ACCESS_REVOKE: 'security.access.revoke',
} as const
