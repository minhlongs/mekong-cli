/**
 * Admin Platform Backup Service — CRUD for platform_backups and platform_restore_points
 * Used by admin-platform-backup routes. All functions accept db: any (D1 binding).
 */

import { randomUUID } from 'crypto';

/** List all platform backups, optionally filtered by status */
async function listBackups(db: any, status?: string): Promise<unknown[]> {
  try {
    if (status) {
      const rows = await db
        .prepare('SELECT * FROM platform_backups WHERE status = ? ORDER BY started_at DESC')
        .bind(status)
        .all();
      return (rows.results as unknown[]);
    }
    const rows = await db
      .prepare('SELECT * FROM platform_backups ORDER BY started_at DESC')
      .all();
    return (rows.results as unknown[]);
  } catch (e: unknown) {
    throw new Error(`listBackups failed: ${(e as Error).message}`);
  }
}

/** Create a new platform backup record */
async function createBackup(
  db: any,
  data: {
    backup_type?: string;
    storage_location: string;
    size_bytes?: number;
    initiated_by?: string;
  }
): Promise<unknown> {
  try {
    const id = randomUUID();
    const now = new Date().toISOString();
    const backupType = data.backup_type ?? 'full';
    const sizeBytes = data.size_bytes ?? 0;

    await db
      .prepare(
        `INSERT INTO platform_backups
           (id, backup_type, storage_location, size_bytes, status, initiated_by, started_at)
         VALUES (?, ?, ?, ?, 'pending', ?, ?)`
      )
      .bind(id, backupType, data.storage_location, sizeBytes, data.initiated_by ?? null, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM platform_backups WHERE id = ?')
      .bind(id)
      .first();
    return row;
  } catch (e: unknown) {
    throw new Error(`createBackup failed: ${(e as Error).message}`);
  }
}

/** List all restore points, optionally filtered by backup_id */
async function getRestorePoints(db: any, backupId?: string): Promise<unknown[]> {
  try {
    if (backupId) {
      const rows = await db
        .prepare('SELECT * FROM platform_restore_points WHERE backup_id = ? ORDER BY created_at DESC')
        .bind(backupId)
        .all();
      return (rows.results as unknown[]);
    }
    const rows = await db
      .prepare('SELECT * FROM platform_restore_points ORDER BY created_at DESC')
      .all();
    return (rows.results as unknown[]);
  } catch (e: unknown) {
    throw new Error(`getRestorePoints failed: ${(e as Error).message}`);
  }
}

/** Dashboard summary: backup counts by status and recent restore points */
async function getDashboard(db: any): Promise<unknown> {
  try {
    const byStatus = await db
      .prepare('SELECT status, COUNT(*) as count FROM platform_backups GROUP BY status')
      .all();
    const byType = await db
      .prepare('SELECT backup_type, COUNT(*) as count FROM platform_backups GROUP BY backup_type')
      .all();
    const recentRestores = await db
      .prepare('SELECT * FROM platform_restore_points ORDER BY created_at DESC LIMIT 10')
      .all();
    return {
      by_status: (byStatus.results as unknown[]),
      by_type: (byType.results as unknown[]),
      recent_restores: (recentRestores.results as unknown[]),
    };
  } catch (e: unknown) {
    throw new Error(`getDashboard failed: ${(e as Error).message}`);
  }
}

export const adminPlatformBackupService = {
  listBackups,
  createBackup,
  getRestorePoints,
  getDashboard,
};
