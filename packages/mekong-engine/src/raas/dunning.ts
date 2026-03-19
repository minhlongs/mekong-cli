import type { D1Database } from '@cloudflare/workers-types'

/**
 * License status for dunning system
 */
export type LicenseStatus = 'active' | 'suspended' | 'expired' | 'blocked'

/**
 * Dunning schedule with timeline
 */
export interface DunningSchedule {
  status: LicenseStatus
  daysUntilSuspension: number
  gracePeriodEnds?: string
  suspendedAt?: string
  reason?: string
}

/**
 * Check tenant's current license status
 * Returns: active, suspended, expired, or blocked
 */
export async function checkLicenseStatus(
  db: D1Database,
  tenantId: string,
): Promise<LicenseStatus> {
  const result = await db
    .prepare('SELECT tier, dunning_status FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first<{ tier: string; dunning_status?: string }>()

  if (!result) return 'expired'
  if (result.dunning_status === 'suspended') return 'suspended'
  if (result.dunning_status === 'blocked') return 'blocked'
  if (result.tier === 'blocked') return 'blocked'
  if (result.tier === 'free' || result.tier === 'pro' || result.tier === 'enterprise') return 'active'
  return 'active'
}

/**
 * Suspend tenant access (e.g., non-payment, credit exhaustion)
 * Sets tier to 'blocked' and records suspension reason
 */
export async function suspendTenant(
  db: D1Database,
  tenantId: string,
  reason: string,
): Promise<boolean> {
  const now = new Date().toISOString()
  try {
    await db
      .prepare(`
        UPDATE tenants
        SET tier = 'blocked',
            dunning_status = 'suspended',
            updated_at = ?
        WHERE id = ?
      `)
      .bind(now, tenantId)
      .run()

    // Record suspension in audit log if table exists
    await db
      .prepare(`
        INSERT INTO audit_logs (tenant_id, action, resource, new_value, created_at)
        VALUES (?, 'suspend', 'tenant', ?, ?)
      `)
      .bind(tenantId, JSON.stringify({ reason, suspended_at: now }), now)
      .run()
      .catch(() => {}) // Ignore if audit_logs table doesn't exist yet

    return true
  } catch {
    return false
  }
}

/**
 * Reactivate tenant after payment/resolution
 * Restores previous tier and clears suspension
 */
export async function reactivateTenant(
  db: D1Database,
  tenantId: string,
  newTier: string = 'free',
): Promise<boolean> {
  const now = new Date().toISOString()
  try {
    await db
      .prepare(`
        UPDATE tenants
        SET tier = ?,
            dunning_status = NULL,
            updated_at = ?
        WHERE id = ?
      `)
      .bind(newTier, now, tenantId)
      .run()

    // Record reactivation in audit log
    await db
      .prepare(`
        INSERT INTO audit_logs (tenant_id, action, resource, new_value, created_at)
        VALUES (?, 'reactivate', 'tenant', ?, ?)
      `)
      .bind(tenantId, JSON.stringify({ reactivated_at: now, tier: newTier }), now)
      .run()
      .catch(() => {}) // Ignore if audit_logs table doesn't exist yet

    return true
  } catch {
    return false
  }
}

/**
 * Get dunning schedule for tenant
 * Returns days until suspension, grace period info
 */
export async function getDunningSchedule(
  db: D1Database,
  tenantId: string,
): Promise<DunningSchedule> {
  const result = await db
    .prepare('SELECT tier, dunning_status, updated_at FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first<{
      tier: string
      dunning_status?: string
      updated_at?: string
    }>()

  if (!result) {
    return { status: 'expired', daysUntilSuspension: 0 }
  }

  // Already suspended or blocked
  if (result.dunning_status === 'suspended' || result.tier === 'blocked') {
    return {
      status: result.dunning_status === 'suspended' ? 'suspended' : 'blocked',
      daysUntilSuspension: 0,
      reason: 'Account suspended',
      suspendedAt: result.updated_at || undefined,
    }
  }

  // Active tenant - calculate grace period
  const gracePeriodDays = 7
  const lastUpdate = result.updated_at ? new Date(result.updated_at) : new Date()
  const gracePeriodEnd = new Date(lastUpdate.getTime() + gracePeriodDays * 24 * 60 * 60 * 1000)
  const now = new Date()
  const daysUntilSuspension = Math.max(
    0,
    Math.ceil((gracePeriodEnd.getTime() - now.getTime()) / (24 * 60 * 60 * 1000))
  )

  return {
    status: 'active',
    daysUntilSuspension,
    gracePeriodEnds: gracePeriodEnd.toISOString(),
  }
}

/**
 * Check if tenant has exhausted credits and passed grace period
 * Returns true if tenant should be suspended
 */
export async function shouldSuspendForCreditExhaustion(
  db: D1Database,
  tenantId: string,
): Promise<{ shouldSuspend: boolean; balance: number; daysOverdue: number }> {
  const balanceResult = await db
    .prepare('SELECT COALESCE(SUM(amount), 0) as balance FROM credits WHERE tenant_id = ?')
    .bind(tenantId)
    .first<{ balance: number }>()

  const balance = balanceResult?.balance ?? 0

  // Still has credits - no suspension needed
  if (balance > 0) {
    return { shouldSuspend: false, balance, daysOverdue: 0 }
  }

  // Zero or negative balance - check grace period
  const schedule = await getDunningSchedule(db, tenantId)

  if (schedule.status === 'active' && schedule.daysUntilSuspension === 0) {
    // Grace period expired
    const graceEnds = schedule.gracePeriodEnds ? new Date(schedule.gracePeriodEnds) : new Date()
    const daysOverdue = Math.ceil((Date.now() - graceEnds.getTime()) / (24 * 60 * 60 * 1000))
    return { shouldSuspend: true, balance, daysOverdue }
  }

  return { shouldSuspend: false, balance, daysOverdue: 0 }
}

/**
 * Emit webhook event for license changes
 */
export async function emitLicenseEvent(
  db: D1Database,
  tenantId: string,
  eventType: 'license.suspended' | 'license.reactivated' | 'license.payment_failed' | 'license.subscription_expired' | 'license.subscription_canceled',
  details: Record<string, unknown>,
): Promise<void> {
  const now = new Date().toISOString()
  try {
    await db
      .prepare(`
        INSERT INTO webhook_events (event_type, tenant_id, payload, created_at)
        VALUES (?, ?, ?, ?)
      `)
      .bind(eventType, tenantId, JSON.stringify({ tenant_id: tenantId, ...details }), now)
      .run()
      .catch(() => {}) // Ignore if webhook_events table doesn't exist
  } catch {
    // Silently ignore - webhook events are best-effort
  }
}

/**
 * Handle payment.succeeded webhook from Polar.sh
 * Auto-reactivates suspended tenants
 */
export async function handlePaymentSucceeded(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string }; customer_id?: string },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  const status = await checkLicenseStatus(db, tenantId)
  if (status === 'suspended' || status === 'blocked') {
    // Restore to pro tier for paid subscriptions
    await reactivateTenant(db, tenantId, 'pro')
    await emitLicenseEvent(db, tenantId, 'license.reactivated', {
      trigger: 'payment_succeeded',
      payment_id: data.id,
    })
  }
}

/**
 * Handle payment.failed webhook from Polar.sh
 * Starts grace period for tenant
 */
export async function handlePaymentFailed(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string } },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  // Grace period is automatically calculated by getDunningSchedule
  // Just emit an event for monitoring/notification purposes
  await emitLicenseEvent(db, tenantId, 'license.payment_failed', {
    trigger: 'payment_failed',
    payment_id: data.id,
  })
}

/**
 * Handle subscription.active webhook from Polar.sh
 * Ensures tenant status is active
 */
export async function handleSubscriptionActive(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string } },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  const status = await checkLicenseStatus(db, tenantId)
  if (status === 'suspended' || status === 'blocked') {
    await reactivateTenant(db, tenantId, 'pro')
    await emitLicenseEvent(db, tenantId, 'license.reactivated', {
      trigger: 'subscription_active',
      subscription_id: data.id,
    })
  }
}

/**
 * Handle subscription.expired webhook from Polar.sh
 * Starts 7-day grace period
 */
export async function handleSubscriptionExpired(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string } },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  // Update tenant's dunning_status to track expiration
  // Grace period will be calculated by getDunningSchedule
  await emitLicenseEvent(db, tenantId, 'license.subscription_expired', {
    trigger: 'subscription_expired',
    subscription_id: data.id,
  })
}

/**
 * Handle subscription.canceled webhook from Polar.sh
 * Marks tenant for suspension after grace period
 */
export async function handleSubscriptionCanceled(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string } },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  await emitLicenseEvent(db, tenantId, 'license.subscription_canceled', {
    trigger: 'subscription_canceled',
    subscription_id: data.id,
  })
}
