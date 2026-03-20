import type { D1Database } from '@cloudflare/workers-types'
import { constantTimeCompare } from '../lib/crypto-utils'

/**
 * License key status
 */
export type LicenseKeyStatus = 'active' | 'suspended' | 'revoked' | 'expired'

/**
 * License key record
 */
export interface LicenseKey {
  id: string
  tenant_id: string
  key_hash: string
  status: LicenseKeyStatus
  expires_at?: string
  created_at: string
}

/**
 * Generate a cryptographically secure license key
 * Returns the raw key (one-time display) and saves the hash
 */
export async function generateLicenseKey(
  db: D1Database,
  tenantId: string,
  expiresAt?: string,
): Promise<{ key: string; licenseKey: LicenseKey } | null> {
  try {
    // Generate cryptographically secure key
    const randomBytes = crypto.getRandomValues(new Uint8Array(32))
    const key = `lk_${Array.from(randomBytes)
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')}`

    // Hash the key for storage
    const keyHash = await hashKey(key)
    const id = crypto.randomUUID()
    const now = new Date().toISOString()

    // Insert license key
    await db
      .prepare(`
        INSERT INTO license_keys (id, tenant_id, key_hash, status, expires_at, created_at)
        VALUES (?, ?, ?, 'active', ?, ?)
      `)
      .bind(id, tenantId, keyHash, expiresAt || null, now)
      .run()

    const licenseKey: LicenseKey = {
      id,
      tenant_id: tenantId,
      key_hash: keyHash,
      status: 'active',
      expires_at: expiresAt,
      created_at: now,
    }

    return { key, licenseKey }
  } catch {
    return null
  }
}

/**
 * Validate a license key
 * Returns tenant info and status if valid
 */
export async function validateLicenseKey(
  db: D1Database,
  key: string,
): Promise<{ tenantId: string; status: LicenseKeyStatus; expiresAt?: string } | null> {
  try {
    const keyHash = await hashKey(key)

    const result = await db
      .prepare('SELECT tenant_id, status, expires_at FROM license_keys WHERE key_hash = ?')
      .bind(keyHash)
      .first<{ tenant_id: string; status: LicenseKeyStatus; expires_at?: string }>()

    if (!result) {
      return null
    }

    // Check if expired
    if (result.expires_at && new Date(result.expires_at) < new Date()) {
      // Mark as expired in database
      await db
        .prepare("UPDATE license_keys SET status = 'expired' WHERE key_hash = ?")
        .bind(keyHash)
        .run()
      return { tenantId: result.tenant_id, status: 'expired', expiresAt: result.expires_at }
    }

    return {
      tenantId: result.tenant_id,
      status: result.status,
      expiresAt: result.expires_at,
    }
  } catch {
    return null
  }
}

/**
 * Revoke a license key
 * Returns true if successful
 */
export async function revokeLicenseKey(
  db: D1Database,
  keyId: string,
  reason?: string,
): Promise<boolean> {
  try {
    const now = new Date().toISOString()

    // Update status
    const result = await db
      .prepare(`
        UPDATE license_keys
        SET status = 'revoked'
        WHERE id = ? AND status != 'revoked'
      `)
      .bind(keyId)
      .run()

    if ((result.meta?.changes ?? 0) === 0) {
      return false
    }

    // Record in audit log
    await db
      .prepare(`
        INSERT INTO audit_logs (tenant_id, action, resource, resource_id, new_value, created_at)
        VALUES ((SELECT tenant_id FROM license_keys WHERE id = ?), 'revoke', 'license_key', ?, ?, ?)
      `)
      .bind(keyId, keyId, JSON.stringify({ reason: reason || 'Admin revocation', revoked_at: now }), now)
      .run()
      .catch(() => {}) // Ignore if audit_logs doesn't exist

    return true
  } catch {
    return false
  }
}

/**
 * List all license keys for a tenant
 */
export async function listLicenseKeys(db: D1Database, tenantId: string): Promise<LicenseKey[]> {
  try {
    const { results } = await db
      .prepare('SELECT id, tenant_id, key_hash, status, expires_at, created_at FROM license_keys WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all()

    return results.map((row) => ({
      id: String(row.id),
      tenant_id: String(row.tenant_id),
      key_hash: String(row.key_hash),
      status: row.status as LicenseKeyStatus,
      expires_at: row.expires_at as string | undefined,
      created_at: String(row.created_at),
    }))
  } catch {
    return []
  }
}

/**
 * Get a specific license key by ID
 */
export async function getLicenseKey(db: D1Database, keyId: string): Promise<LicenseKey | null> {
  try {
    const result = await db
      .prepare('SELECT id, tenant_id, key_hash, status, expires_at, created_at FROM license_keys WHERE id = ?')
      .bind(keyId)
      .first()

    if (!result) {
      return null
    }

    return {
      id: String(result.id),
      tenant_id: String(result.tenant_id),
      key_hash: String(result.key_hash),
      status: result.status as LicenseKeyStatus,
      expires_at: result.expires_at as string | undefined,
      created_at: String(result.created_at),
    }
  } catch {
    return null
  }
}

/**
 * Hash a license key for storage
 */
async function hashKey(key: string): Promise<string> {
  const encoded = new TextEncoder().encode(key)
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

/**
 * Extend license key expiration
 */
export async function extendLicenseKey(
  db: D1Database,
  keyId: string,
  newExpiresAt: string,
): Promise<boolean> {
  try {
    const result = await db
      .prepare(`
        UPDATE license_keys
        SET expires_at = ?
        WHERE id = ? AND status = 'active'
      `)
      .bind(newExpiresAt, keyId)
      .run()

    return (result.meta?.changes ?? 0) > 0
  } catch {
    return false
  }
}
