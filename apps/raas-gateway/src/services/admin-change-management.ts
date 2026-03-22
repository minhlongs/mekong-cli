/**
 * Admin Change Management Service — CRUD for change_requests and change_logs
 * Used by admin-change-management routes. All functions accept db: any (D1 binding).
 */

import { randomUUID } from 'crypto';

/** List all change requests, optionally filtered by status */
export async function listChanges(db: any, status?: string): Promise<unknown[]> {
  try {
    if (status) {
      const rows = await db
        .prepare('SELECT * FROM change_requests WHERE status = ? ORDER BY created_at DESC')
        .bind(status)
        .all();
      return rows.results;
    }
    const rows = await db
      .prepare('SELECT * FROM change_requests ORDER BY created_at DESC')
      .all();
    return rows.results;
  } catch (e: unknown) {
    throw new Error(`listChanges failed: ${(e as Error).message}`);
  }
}

/** Create a new change request */
export async function createChange(
  db: any,
  data: {
    title: string;
    change_type: string;
    description?: string;
    priority?: string;
    requested_by?: string;
    scheduled_at?: string;
  }
): Promise<unknown> {
  try {
    const id = randomUUID();
    const now = new Date().toISOString();
    const priority = data.priority ?? 'medium';

    await db
      .prepare(
        `INSERT INTO change_requests
           (id, title, description, change_type, priority, status, requested_by, approved_by, scheduled_at, created_at)
         VALUES (?, ?, ?, ?, ?, 'pending', ?, NULL, ?, ?)`
      )
      .bind(
        id,
        data.title,
        data.description ?? null,
        data.change_type,
        priority,
        data.requested_by ?? null,
        data.scheduled_at ?? null,
        now
      )
      .run();

    const row = await db
      .prepare('SELECT * FROM change_requests WHERE id = ?')
      .bind(id)
      .first();
    return row;
  } catch (e: unknown) {
    throw new Error(`createChange failed: ${(e as Error).message}`);
  }
}

/** Get all logs for a given change request */
export async function getLogs(db: any, changeId: string): Promise<unknown[]> {
  try {
    const rows = await db
      .prepare('SELECT * FROM change_logs WHERE change_id = ? ORDER BY created_at ASC')
      .bind(changeId)
      .all();
    return rows.results;
  } catch (e: unknown) {
    throw new Error(`getLogs failed: ${(e as Error).message}`);
  }
}

/** Dashboard summary: counts by status, priority, and recent logs */
export async function getDashboard(db: any): Promise<unknown> {
  try {
    const byStatus = await db
      .prepare('SELECT status, COUNT(*) as count FROM change_requests GROUP BY status')
      .all();
    const byPriority = await db
      .prepare('SELECT priority, COUNT(*) as count FROM change_requests GROUP BY priority')
      .all();
    const recentLogs = await db
      .prepare('SELECT * FROM change_logs ORDER BY created_at DESC LIMIT 10')
      .all();
    return {
      by_status: byStatus.results,
      by_priority: byPriority.results,
      recent_logs: recentLogs.results,
    };
  } catch (e: unknown) {
    throw new Error(`getDashboard failed: ${(e as Error).message}`);
  }
}

export const adminChangeManagementService = {
  listChanges,
  createChange,
  getLogs,
  getDashboard,
};
