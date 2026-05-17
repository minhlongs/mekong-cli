import type { D1Database } from '@cloudflare/workers-types'
import { generateLicenseKey, revokeLicenseKey } from './license-keys'
import { createTenant } from './tenant'

/**
 * Verify Polar webhook signature using HMAC-SHA256.
 * Polar sends `webhook-signature` header in `<algo>=<hex>` form (Standard Webhooks).
 */
export async function verifyPolarSignature(
  body: string,
  signature: string | undefined,
  secret: string | undefined,
): Promise<boolean> {
  if (!signature || !secret) return false

  // Standard Webhooks: signature is `v1,<base64-hmac>` joined by spaces.
  // We accept either raw hex or `v1=<hex>` for compatibility.
  const candidate = signature.includes('=') ? signature.split('=').pop() ?? '' : signature
  const expected = await hmacHex(secret, body)
  return constantTimeEqual(candidate.trim(), expected)
}

async function hmacHex(secret: string, message: string): Promise<string> {
  const enc = new TextEncoder()
  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const buf = await crypto.subtle.sign('HMAC', key, enc.encode(message))
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

function constantTimeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false
  let mismatch = 0
  for (let i = 0; i < a.length; i++) mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i)
  return mismatch === 0
}

export type PolarTier = 'starter' | 'growth' | 'pro'

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
): Promise<{ licenseKey: string; tenantId: string; tier: PolarTier; email: string } | null> {
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
  return { licenseKey: result.key, tenantId, tier, email }
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
