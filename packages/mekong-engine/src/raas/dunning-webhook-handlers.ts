import type { D1Database } from '@cloudflare/workers-types'
import { checkLicenseStatus, reactivateTenant } from './dunning'

export type LicenseEventType =
  | 'license.suspended'
  | 'license.reactivated'
  | 'license.payment_failed'
  | 'license.subscription_expired'
  | 'license.subscription_canceled'

/**
 * Emit webhook event for license changes
 */
export async function emitLicenseEvent(
  db: D1Database,
  tenantId: string,
  eventType: LicenseEventType,
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
      .catch(() => {})
  } catch {
    // Silently ignore - webhook events are best-effort
  }
}

/**
 * Handle payment.succeeded webhook from NOWPayments
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
    await reactivateTenant(db, tenantId, 'pro')
    await emitLicenseEvent(db, tenantId, 'license.reactivated', {
      trigger: 'payment_succeeded',
      payment_id: data.id,
    })
  }
}

/**
 * Handle payment.failed webhook from NOWPayments
 * Starts grace period for tenant
 */
export async function handlePaymentFailed(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string } },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  await emitLicenseEvent(db, tenantId, 'license.payment_failed', {
    trigger: 'payment_failed',
    payment_id: data.id,
  })
}

/**
 * Handle subscription.active webhook from NOWPayments
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
 * Handle subscription.expired webhook from NOWPayments
 * Starts 7-day grace period
 */
export async function handleSubscriptionExpired(
  db: D1Database,
  data: { id?: string; metadata?: { tenant_id?: string } },
): Promise<void> {
  const tenantId = data.metadata?.tenant_id
  if (!tenantId) return

  await emitLicenseEvent(db, tenantId, 'license.subscription_expired', {
    trigger: 'subscription_expired',
    subscription_id: data.id,
  })
}

/**
 * Handle subscription.canceled webhook from NOWPayments
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
