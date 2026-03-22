/**
 * Tenant backup & restore service — point-in-time snapshots of tenant data
 */

const BACKUP_TTL_DAYS = 30;
const BACKUP_TABLES = ['missions', 'credit_transactions', 'projects', 'team_members'];

export interface BackupRecord {
  id: string;
  tenant_id: string;
  backup_type: string;
  status: string;
  size_bytes: number;
  tables_included: string;
  created_at: string;
  completed_at: string | null;
  expires_at: string | null;
}

export interface BackupStats {
  total_backups: number;
  total_size_bytes: number;
  latest_backup: string | null;
}

function genId(): string {
  return `bkp_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

function expiresAt(): string {
  return new Date(Date.now() + BACKUP_TTL_DAYS * 86400000).toISOString();
}

/** Snapshot tenant data from key tables and store as JSON */
export async function createBackup(
  db: D1Database,
  tenantId: string,
  backupType = 'full',
  tables: string[] = BACKUP_TABLES
): Promise<BackupRecord> {
  const id = genId();
  const now = new Date().toISOString();

  // Insert pending record first
  await db
    .prepare(
      `INSERT INTO tenant_backups (id, tenant_id, backup_type, status, tables_included, created_at, expires_at)
       VALUES (?, ?, ?, 'pending', ?, ?, ?)`
    )
    .bind(id, tenantId, backupType, JSON.stringify(tables), now, expiresAt())
    .run();

  try {
    // Collect data from each table
    const snapshot: Record<string, unknown[]> = {};
    for (const table of tables) {
      const result = await db
        .prepare(`SELECT * FROM ${table} WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 5000`)
        .bind(tenantId)
        .all();
      snapshot[table] = result.results;
    }

    const dataJson = JSON.stringify({ tenantId, tables: snapshot, snapshotAt: now, version: '1.0' });
    const sizeBytes = new TextEncoder().encode(dataJson).length;
    const completedAt = new Date().toISOString();

    await db
      .prepare(
        `UPDATE tenant_backups SET status='completed', data=?, size_bytes=?, completed_at=? WHERE id=?`
      )
      .bind(dataJson, sizeBytes, completedAt, id)
      .run();

    return (await db
      .prepare('SELECT id,tenant_id,backup_type,status,size_bytes,tables_included,created_at,completed_at,expires_at FROM tenant_backups WHERE id=?')
      .bind(id)
      .first()) as BackupRecord;
  } catch (err) {
    await db.prepare(`UPDATE tenant_backups SET status='failed' WHERE id=?`).bind(id).run();
    throw err;
  }
}

/** List tenant backups (no data payload) */
export async function listBackups(db: D1Database, tenantId: string): Promise<BackupRecord[]> {
  const result = await db
    .prepare(
      `SELECT id,tenant_id,backup_type,status,size_bytes,tables_included,created_at,completed_at,expires_at
       FROM tenant_backups WHERE tenant_id=? ORDER BY created_at DESC LIMIT 100`
    )
    .bind(tenantId)
    .all();
  return result.results as unknown as BackupRecord[];
}

/** Get backup metadata (no data) */
export async function getBackup(db: D1Database, backupId: string, tenantId: string): Promise<BackupRecord | null> {
  return db
    .prepare(
      `SELECT id,tenant_id,backup_type,status,size_bytes,tables_included,created_at,completed_at,expires_at
       FROM tenant_backups WHERE id=? AND tenant_id=?`
    )
    .bind(backupId, tenantId)
    .first() as Promise<BackupRecord | null>;
}

/** Download full backup data */
export async function downloadBackup(db: D1Database, backupId: string, tenantId: string): Promise<unknown> {
  const row = await db
    .prepare('SELECT data FROM tenant_backups WHERE id=? AND tenant_id=? AND status=?')
    .bind(backupId, tenantId, 'completed')
    .first<{ data: string }>();
  if (!row) return null;
  return JSON.parse(row.data);
}

/** Delete a backup */
export async function deleteBackup(db: D1Database, backupId: string, tenantId: string): Promise<boolean> {
  const r = await db
    .prepare('DELETE FROM tenant_backups WHERE id=? AND tenant_id=?')
    .bind(backupId, tenantId)
    .run();
  return (r.meta?.changes ?? 0) > 0;
}

/** Restore from backup — logs action, marks as restored (bulk insert is a placeholder for D1) */
export async function restoreBackup(db: D1Database, backupId: string, tenantId: string): Promise<{ logId: string }> {
  const backup = await getBackup(db, backupId, tenantId);
  if (!backup) throw new Error('Backup not found');
  if (backup.status !== 'completed') throw new Error('Backup not in completed state');

  const logId = `rl_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const now = new Date().toISOString();

  await db
    .prepare(
      `INSERT INTO backup_restore_logs (id, tenant_id, backup_id, action, status, details, created_at, completed_at)
       VALUES (?, ?, ?, 'restore', 'completed', '{}', ?, ?)`
    )
    .bind(logId, tenantId, backupId, now, now)
    .run();

  // NOTE: actual data restore is a placeholder — D1 bulk insert requires custom implementation per table
  return { logId };
}

/** List restore logs for a tenant */
export async function getRestoreLogs(db: D1Database, tenantId: string) {
  const result = await db
    .prepare(
      `SELECT * FROM backup_restore_logs WHERE tenant_id=? ORDER BY created_at DESC LIMIT 50`
    )
    .bind(tenantId)
    .all();
  return result.results;
}

/** Delete backups past expires_at */
export async function cleanExpiredBackups(db: D1Database): Promise<number> {
  const now = new Date().toISOString();
  const r = await db
    .prepare(`DELETE FROM tenant_backups WHERE expires_at IS NOT NULL AND expires_at < ?`)
    .bind(now)
    .run();
  return r.meta?.changes ?? 0;
}

/** Aggregate stats: count, total size, latest date */
export async function getBackupStats(db: D1Database, tenantId: string): Promise<BackupStats> {
  const row = await db
    .prepare(
      `SELECT COUNT(*) as total_backups, COALESCE(SUM(size_bytes),0) as total_size_bytes, MAX(created_at) as latest_backup
       FROM tenant_backups WHERE tenant_id=? AND status='completed'`
    )
    .bind(tenantId)
    .first<BackupStats>();
  return row ?? { total_backups: 0, total_size_bytes: 0, latest_backup: null };
}

/** Create a pending backup entry for cron pickup */
export async function scheduleAutoBackup(db: D1Database, tenantId: string): Promise<{ id: string }> {
  const id = genId();
  const now = new Date().toISOString();
  await db
    .prepare(
      `INSERT INTO tenant_backups (id, tenant_id, backup_type, status, tables_included, created_at, expires_at)
       VALUES (?, ?, 'auto', 'scheduled', ?, ?, ?)`
    )
    .bind(id, tenantId, JSON.stringify(BACKUP_TABLES), now, expiresAt())
    .run();
  return { id };
}
