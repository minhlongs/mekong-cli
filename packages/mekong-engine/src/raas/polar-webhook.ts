import type { D1Database } from '@cloudflare/workers-types'
import { addCredits } from './credits'
import { generateLicenseKey, revokeLicenseKey } from './license-keys'
import { createTenant } from './tenant'

/**
 * Verify Polar webhook signature using Standard Webhooks format.
 *
 * Polar sends:
 *   webhook-id: <event_id>
 *   webhook-timestamp: <unix_epoch_seconds>
 *   webhook-signature: v1,<base64>
 *
 * Expected HMAC: base64(HMAC-SHA256(secret, "{id}.{timestamp}.{body}"))
 * Replay window: 5 minutes.
 */
export async function verifyPolarSignature(
  body: string,
  webhookId: string | undefined,
  webhookTimestamp: string | undefined,
  signature: string | undefined,
  secret: string | undefined,
): Promise<boolean> {
  if (!signature || !secret || !webhookId || !webhookTimestamp) return false

  // Replay window check (5 min)
  const ts = parseInt(webhookTimestamp, 10)
  if (isNaN(ts)) return false
  if (Math.abs(Date.now() / 1000 - ts) > 300) return false

  // Standard Webhooks: signature is "v1,<base64>"
  const sigParts = signature.split(',')
  if (sigParts.length !== 2 || sigParts[0] !== 'v1') return false
  const receivedSig = sigParts[1]!.trim()

  // Compute expected: base64(HMAC-SHA256(secret, "{id}.{ts}.{body}"))
  const signingInput = `${webhookId}.${webhookTimestamp}.${body}`
  const expected = await hmacBase64(secret, signingInput)
  return constantTimeEqual(receivedSig, expected)
}

async function hmacBase64(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const buf = await crypto.subtle.sign('HMAC', key, enc.encode(message))
  const bytes = new Uint8Array(buf)
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return btoa(binary)
}

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let mismatch = 0
  for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return mismatch === 0
}

export type PolarTier = 'starter' | 'growth' | 'pro'

export const SUBSCRIPTION_CREDITS: Record<PolarTier, number> = {
  starter: 200,
  growth: 1000,
  pro: 5000,
}

export function tierFromProductName(name: string | undefined): PolarTier {
  const n = (name || '').toLowerCase()
  if (n.includes('pro')) return 'pro'
  if (n.includes('growth')) return 'growth'
  return 'starter'
}

/**
 * Process a `subscription.created` event:
 *   1. Create or reuse a tenant keyed by the Polar customer id.
 *   2. Generate a license key bound to that tenant.
 *
 * The raw license key is returned only once (caller emails it to the user).
 */
export async function handleSubscriptionCreated(
  db: D1Database,
  event: any,
): Promise<{ licenseKey: string; tenantId: string; tier: PolarTier; email: string; creditsGranted: number } | null> {
  const subscription = event?.subscription ?? event?.data?.subscription ?? event?.data ?? {}
  const customer = subscription.customer ?? {}
  const product = subscription.product ?? {}
  const customerId: string | undefined = customer.id
  const email: string = customer.email ?? 'unknown@example.com'
  const tier = tierFromProductName(product.name)
  if (!customerId) return null

  // Reuse a deterministic tenant id derived from the Polar customer id so
  // repeated webhook deliveries are idempotent.
  const tenantId = `polar_${customerId}`
  const existing = await db
    .prepare('SELECT id FROM tenants WHERE id = ?')
    .bind(tenantId)
    .first<{ id: string }>()

  if (!existing) {
    await db
      .prepare(
        'INSERT INTO tenants (id, name, api_key_hash, tier, created_at) VALUES (?, ?, ?, ?, ?)',
      )
      .bind(tenantId, email, '', tier, new Date().toISOString())
      .run()
  }

  const result = await generateLicenseKey(db, tenantId)
  if (!result) return null

  const credits = SUBSCRIPTION_CREDITS[tier]
  await addCredits(db, tenantId, credits, `Polar subscription: ${tier}`)

  return { licenseKey: result.key, tenantId, tier, email, creditsGranted: credits }
}

/**
 * Process a `subscription.cancelled` event by revoking the matching license.
 */
export async function handleSubscriptionCancelled(
  db: D1Database,
  event: any,
): Promise<boolean> {
  const subscription = event?.subscription ?? event?.data?.subscription ?? event?.data ?? {}
  const customerId: string | undefined = subscription.customer?.id
  if (!customerId) return false

  const tenantId = `polar_${customerId}`
  const rows = await db
    .prepare("SELECT id FROM license_keys WHERE tenant_id = ? AND status = 'active'")
    .bind(tenantId)
    .all<{ id: string }>()

  let any = false
  for (const row of rows.results ?? []) {
    if (await revokeLicenseKey(db, row.id)) any = true
  }
  return any
}
