/**
 * Audit Logging Middleware
 * Tamper-proof logging of all sensitive operations
 *
 * Logs: who, what, when, where, result
 */

import type { Context, Next } from 'hono'
import type { Bindings } from '../index'
import {
  type AuditLogEntry,
  type AuditLogFilters,
  logAudit,
  queryAuditLogs,
  getAuditLogById,
} from './audit-log-queries'

export type { AuditLogEntry, AuditLogFilters }
export { logAudit, queryAuditLogs, getAuditLogById }

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
  return async (c: Context<{ Bindings: Bindings; Variables: { tenant: { id: string } } }>, next: Next) => {
    const startTime = Date.now()

    if (options?.skipPaths?.some(path => c.req.path.includes(path))) {
      await next()
      return
    }

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

    let requestBody: unknown
    if (options?.includeBody) {
      try {
        const clonedRequest = c.req.raw.clone()
        requestBody = await clonedRequest.json().catch(() => undefined)
      } catch {
        // Ignore body parse errors
      }
    }

    await next()

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
        metadata.response_status = c.res.status
      } catch {
        // Ignore
      }
    }

    const action = `${c.req.method} ${c.req.path}`

    if (c.env.DB) {
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
}

/**
 * Manual audit logging for specific operations
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
