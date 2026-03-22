/**
 * Admin Platform Backup Service — CRUD for platform_backups and platform_backup_schedules
 * All functions accept db: any (D1 binding). Returns { success, data } or { success, error }.
 */

function newId(): string {
  return crypto.randomUUID();
}

function now(): string {
  return new Date().toISOString();
}

/** List all platform backups ordered by created_at desc */
async function listBackups(db: any): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM platform_backups ORDER BY created_at DESC')
      .all();
    return { success: true, data: (result.results ?? []) as any[] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Create a new backup record with status 'pending' */
async function createBackup(
  db: any,
  input: { backup_name: string; backup_type?: string; size_bytes?: number; storage_path?: string }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = newId();
    const ts = now();
    const backupType = input.backup_type ?? 'full';
    await db
      .prepare(
        `INSERT INTO platform_backups
         (id, backup_name, backup_type, size_bytes, storage_path, status, started_at, created_at)
         VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)`
      )
      .bind(
        id,
        input.backup_name,
        backupType,
        input.size_bytes ?? null,
        input.storage_path ?? null,
        ts,
        ts
      )
      .run();
    const row = await db
      .prepare('SELECT * FROM platform_backups WHERE id = ?')
      .bind(id)
      .first();
    return { success: true, data: row };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** List all backup schedules, enabled first */
async function getSchedules(db: any): Promise<{ success: boolean; data?: any[]; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM platform_backup_schedules ORDER BY enabled DESC, created_at DESC')
      .all();
    return { success: true, data: (result.results ?? []) as any[] };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

/** Dashboard: backup counts by status and type */
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [byStatus, byType] = await Promise.all([
      db
        .prepare('SELECT status, COUNT(*) as count FROM platform_backups GROUP BY status')
        .all(),
      db
        .prepare('SELECT backup_type, COUNT(*) as count FROM platform_backups GROUP BY backup_type')
        .all(),
    ]);
    return {
      success: true,
      data: {
        by_status: (byStatus.results ?? []) as any[],
        by_type: (byType.results ?? []) as any[],
      },
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : String(err) };
  }
}

export const adminPlatformBackupService = {
  listBackups,
  createBackup,
  getSchedules,
  getDashboard,
};
