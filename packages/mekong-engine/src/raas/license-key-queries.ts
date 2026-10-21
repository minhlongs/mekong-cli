import type { D1Database } from '@cloudflare/workers-types'

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
 * Hash a license key for storage
 */
export async function hashLicenseKey(key: string): Promise<string> {
  const encoded = new TextEncoder().encode(key)
  const hashBuffer = await crypto.subtle.digest('SHA-256', encoded)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
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
