import type { D1Database } from '@cloudflare/workers-types'

export type LicenseStatus = 'active' | 'suspended' | 'expired' | 'blocked'

export interface DunningSchedule {
  status: LicenseStatus
  daysUntilSuspension: number
  gracePeriodEnds?: string
  suspendedAt?: string
  reason?: string
}

/**
 * Check tenant's current license status
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
 * Suspend tenant access and record suspension reason
 */
export async function suspendTenant(
  db: D1Database,
  tenantId: string,
  reason: string,
): Promise<boolean> {
  const now = new Date().toISOString()
  try {
    await db
      .prepare("UPDATE tenants SET tier = 'blocked', dunning_status = 'suspended', updated_at = ? WHERE id = ?")
      .bind(now, tenantId)
      .run()

    await db
      .prepare("INSERT INTO audit_logs (tenant_id, action, resource, new_value, created_at) VALUES (?, 'suspend', 'tenant', ?, ?)")
      .bind(tenantId, JSON.stringify({ reason, suspended_at: now }), now)
      .run()
      .catch(() => {})

    return true
  } catch {
    return false
  }
}

/**
 * Reactivate tenant after payment/resolution
 */
export async function reactivateTenant(
  db: D1Database,
  tenantId: string,
  newTier: string = 'free',
): Promise<boolean> {
  const now = new Date().toISOString()
  try {
    await db
      .prepare('UPDATE tenants SET tier = ?, dunning_status = NULL, updated_at = ? WHERE id = ?')
      .bind(newTier, now, tenantId)
      .run()

    await db
      .prepare("INSERT INTO audit_logs (tenant_id, action, resource, new_value, created_at) VALUES (?, 'reactivate', 'tenant', ?, ?)")
      .bind(tenantId, JSON.stringify({ reactivated_at: now, tier: newTier }), now)
      .run()
      .catch(() => {})

    return true
  } catch {
    return false
  }
}

/**
 * Get dunning schedule for tenant
 */
export async function getDunningSchedule(
  db: D1Database,
  tenantId: string,
): Promise<DunningSchedule> {
  const result = await db
    .prepare('SELECT tier, dunning_status, updated_at FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first<{ tier: string; dunning_status?: string; updated_at?: string }>()

  if (!result) {
    return { status: 'expired', daysUntilSuspension: 0 }
  }

  if (result.dunning_status === 'suspended' || result.tier === 'blocked') {
    return {
      status: result.dunning_status === 'suspended' ? 'suspended' : 'blocked',
      daysUntilSuspension: 0,
      reason: 'Account suspended',
      suspendedAt: result.updated_at || undefined,
    }
  }

  const gracePeriodDays = 7
  const lastUpdate = result.updated_at ? new Date(result.updated_at) : new Date()
  const gracePeriodEnd = new Date(lastUpdate.getTime() + gracePeriodDays * 24 * 60 * 60 * 1000)
  const daysUntilSuspension = Math.max(
    0,
    Math.ceil((gracePeriodEnd.getTime() - Date.now()) / (24 * 60 * 60 * 1000))
  )

  return {
    status: 'active',
    daysUntilSuspension,
    gracePeriodEnds: gracePeriodEnd.toISOString(),
  }
}

/**
 * Check if tenant has exhausted credits and passed grace period
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
  if (balance > 0) {
    return { shouldSuspend: false, balance, daysOverdue: 0 }
  }

  const schedule = await getDunningSchedule(db, tenantId)
  if (schedule.status === 'active' && schedule.daysUntilSuspension === 0) {
    const graceEnds = schedule.gracePeriodEnds ? new Date(schedule.gracePeriodEnds) : new Date()
    const daysOverdue = Math.ceil((Date.now() - graceEnds.getTime()) / (24 * 60 * 60 * 1000))
    return { shouldSuspend: true, balance, daysOverdue }
  }

  return { shouldSuspend: false, balance, daysOverdue: 0 }
}

export {
  emitLicenseEvent,
  handlePaymentSucceeded,
  handlePaymentFailed,
  handleSubscriptionActive,
  handleSubscriptionExpired,
  handleSubscriptionCanceled,
} from './dunning-webhook-handlers'
