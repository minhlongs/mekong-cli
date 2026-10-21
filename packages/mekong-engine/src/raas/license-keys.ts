import type { D1Database } from '@cloudflare/workers-types'
import {
  type LicenseKeyStatus,
  type LicenseKey,
  hashLicenseKey,
  listLicenseKeys,
  getLicenseKey,
  extendLicenseKey,
} from './license-key-queries'

export type { LicenseKeyStatus, LicenseKey }
export { listLicenseKeys, getLicenseKey, extendLicenseKey }

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
    const randomBytes = crypto.getRandomValues(new Uint8Array(32))
    const key = `lk_${Array.from(randomBytes)
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')}`

    const keyHash = await hashLicenseKey(key)
    const id = crypto.randomUUID()
    const now = new Date().toISOString()

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
    const keyHash = await hashLicenseKey(key)

    const result = await db
      .prepare('SELECT tenant_id, status, expires_at FROM license_keys WHERE key_hash = ?')
      .bind(keyHash)
      .first<{ tenant_id: string; status: LicenseKeyStatus; expires_at?: string }>()

    if (!result) {
      return null
    }

    if (result.expires_at && new Date(result.expires_at) < new Date()) {
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

    await db
      .prepare(`
        INSERT INTO audit_logs (tenant_id, action, resource, resource_id, new_value, created_at)
        VALUES ((SELECT tenant_id FROM license_keys WHERE id = ?), 'revoke', 'license_key', ?, ?, ?)
      `)
      .bind(keyId, keyId, JSON.stringify({ reason: reason || 'Admin revocation', revoked_at: now }), now)
      .run()
      .catch(() => {})

    return true
  } catch {
    return false
  }
}
