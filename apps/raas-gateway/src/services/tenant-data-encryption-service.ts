/**
 * Tenant Data Encryption Service
 * Manages encryption keys, audit trail, and encrypted field registry
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface EncryptionKey {
  id: string;
  tenant_id: string;
  key_alias: string;
  key_type: string;
  key_status: string;
  created_at: string;
  rotated_at: string | null;
  expires_at: string | null;
  version: number;
}

export interface EncryptionAuditEntry {
  id: string;
  tenant_id: string;
  key_id: string;
  operation: string;
  field_name: string | null;
  performed_by: string | null;
  created_at: string;
}

export interface EncryptedField {
  id: string;
  tenant_id: string;
  table_name: string;
  field_name: string;
  key_id: string;
  encryption_type: string;
  is_active: number;
  created_at: string;
}

export interface KeyStats {
  total: number;
  active: number;
  rotating: number;
  retired: number;
  revoked: number;
}

const VALID_KEY_TYPES = ['aes-256-gcm', 'rsa-2048'] as const;
const VALID_KEY_STATUSES = ['active', 'rotating', 'retired', 'revoked'] as const;
const VALID_ENC_TYPES = ['deterministic', 'randomized'] as const;

/** List encryption keys for tenant */
export async function listKeys(db: D1Database, tenantId: string): Promise<EncryptionKey[]> {
  const result = await db
    .prepare('SELECT * FROM encryption_keys WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all<EncryptionKey>();
  return result.results;
}

/** Create a new encryption key */
export async function createKey(
  db: D1Database,
  tenantId: string,
  params: { key_alias: string; key_type?: string; expires_at?: string }
): Promise<EncryptionKey> {
  const keyType = VALID_KEY_TYPES.includes(params.key_type as any) ? params.key_type : 'aes-256-gcm';
  await db
    .prepare(
      `INSERT INTO encryption_keys (tenant_id, key_alias, key_type, expires_at)
       VALUES (?, ?, ?, ?)`
    )
    .bind(tenantId, params.key_alias, keyType, params.expires_at ?? null)
    .run();
  const row = await db
    .prepare('SELECT * FROM encryption_keys WHERE tenant_id = ? AND key_alias = ?')
    .bind(tenantId, params.key_alias)
    .first<EncryptionKey>();
  return row!;
}

/** Rotate an active key — bumps version and sets rotated_at */
export async function rotateKey(
  db: D1Database,
  tenantId: string,
  keyId: string,
  performedBy?: string
): Promise<EncryptionKey | null> {
  const key = await db
    .prepare('SELECT * FROM encryption_keys WHERE id = ? AND tenant_id = ?')
    .bind(keyId, tenantId)
    .first<EncryptionKey>();
  if (!key) return null;

  await db
    .prepare(
      `UPDATE encryption_keys SET key_status = 'rotating', rotated_at = datetime('now'), version = version + 1
       WHERE id = ? AND tenant_id = ?`
    )
    .bind(keyId, tenantId)
    .run();

  await db
    .prepare(
      `INSERT INTO encryption_audit (tenant_id, key_id, operation, performed_by) VALUES (?, ?, 'rotate', ?)`
    )
    .bind(tenantId, keyId, performedBy ?? null)
    .run();

  return db
    .prepare('SELECT * FROM encryption_keys WHERE id = ?')
    .bind(keyId)
    .first<EncryptionKey>();
}

/** Revoke a key */
export async function revokeKey(
  db: D1Database,
  tenantId: string,
  keyId: string,
  performedBy?: string
): Promise<boolean> {
  const info = await db
    .prepare(
      `UPDATE encryption_keys SET key_status = 'revoked' WHERE id = ? AND tenant_id = ? AND key_status != 'revoked'`
    )
    .bind(keyId, tenantId)
    .run();
  if (!info.meta.changes) return false;

  await db
    .prepare(
      `INSERT INTO encryption_audit (tenant_id, key_id, operation, performed_by) VALUES (?, ?, 'revoke', ?)`
    )
    .bind(tenantId, keyId, performedBy ?? null)
    .run();
  return true;
}

/** Fetch audit trail for tenant */
export async function listAudit(
  db: D1Database,
  tenantId: string,
  limit = 100
): Promise<EncryptionAuditEntry[]> {
  const result = await db
    .prepare('SELECT * FROM encryption_audit WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?')
    .bind(tenantId, Math.min(limit, 1000))
    .all<EncryptionAuditEntry>();
  return result.results;
}

/** Register a field for encryption */
export async function registerField(
  db: D1Database,
  tenantId: string,
  params: { table_name: string; field_name: string; key_id: string; encryption_type?: string }
): Promise<EncryptedField> {
  const encType = VALID_ENC_TYPES.includes(params.encryption_type as any)
    ? params.encryption_type
    : 'deterministic';
  await db
    .prepare(
      `INSERT INTO encrypted_fields (tenant_id, table_name, field_name, key_id, encryption_type)
       VALUES (?, ?, ?, ?, ?)`
    )
    .bind(tenantId, params.table_name, params.field_name, params.key_id, encType)
    .run();
  return db
    .prepare('SELECT * FROM encrypted_fields WHERE tenant_id = ? AND table_name = ? AND field_name = ? ORDER BY created_at DESC LIMIT 1')
    .bind(tenantId, params.table_name, params.field_name)
    .first<EncryptedField>() as Promise<EncryptedField>;
}

/** List encrypted fields for tenant */
export async function listFields(db: D1Database, tenantId: string): Promise<EncryptedField[]> {
  const result = await db
    .prepare('SELECT * FROM encrypted_fields WHERE tenant_id = ? ORDER BY created_at DESC')
    .bind(tenantId)
    .all<EncryptedField>();
  return result.results;
}

/** Aggregate key status counts for tenant */
export async function getKeyStats(db: D1Database, tenantId: string): Promise<KeyStats> {
  const result = await db
    .prepare(
      `SELECT key_status, COUNT(*) as cnt FROM encryption_keys WHERE tenant_id = ? GROUP BY key_status`
    )
    .bind(tenantId)
    .all<{ key_status: string; cnt: number }>();

  const map: Record<string, number> = {};
  for (const row of result.results) map[row.key_status] = row.cnt;
  const total = Object.values(map).reduce((s, n) => s + n, 0);
  return {
    total,
    active: map['active'] ?? 0,
    rotating: map['rotating'] ?? 0,
    retired: map['retired'] ?? 0,
    revoked: map['revoked'] ?? 0,
  };
}

/** Admin overview — all tenants key + audit counts */
export async function getAdminOverview(
  db: D1Database
): Promise<{ tenants: number; total_keys: number; total_audits: number; total_fields: number }> {
  const [keys, audits, fields] = await Promise.all([
    db.prepare('SELECT COUNT(*) as n, COUNT(DISTINCT tenant_id) as t FROM encryption_keys').first<{ n: number; t: number }>(),
    db.prepare('SELECT COUNT(*) as n FROM encryption_audit').first<{ n: number }>(),
    db.prepare('SELECT COUNT(*) as n FROM encrypted_fields').first<{ n: number }>(),
  ]);
  return {
    tenants: keys?.t ?? 0,
    total_keys: keys?.n ?? 0,
    total_audits: audits?.n ?? 0,
    total_fields: fields?.n ?? 0,
  };
}
