/**
 * Admin Incident Response Service — CRUD for incidents and incident updates
 * Used by admin-incident-response routes. All functions accept db: any (D1 binding).
 */

import { randomUUID } from 'crypto';

/** List all incidents, optionally filtered by status */
export async function listIncidents(db: any, status?: string): Promise<unknown[]> {
  try {
    if (status) {
      const rows = await db
        .prepare('SELECT * FROM incidents WHERE status = ? ORDER BY created_at DESC')
        .bind(status)
        .all();
      return rows.results;
    }
    const rows = await db
      .prepare('SELECT * FROM incidents ORDER BY created_at DESC')
      .all();
    return rows.results;
  } catch (e: unknown) {
    throw new Error(`listIncidents failed: ${(e as Error).message}`);
  }
}

/** Create a new incident record */
export async function createIncident(
  db: any,
  data: {
    title: string;
    severity?: string;
    description?: string;
    assigned_to?: string;
  }
): Promise<unknown> {
  try {
    const id = randomUUID();
    const now = new Date().toISOString();
    const severity = data.severity ?? 'medium';

    await db
      .prepare(
        `INSERT INTO incidents (id, title, severity, status, description, assigned_to, created_at, updated_at)
         VALUES (?, ?, ?, 'open', ?, ?, ?, ?)`
      )
      .bind(id, data.title, severity, data.description ?? null, data.assigned_to ?? null, now, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM incidents WHERE id = ?')
      .bind(id)
      .first();
    return row;
  } catch (e: unknown) {
    throw new Error(`createIncident failed: ${(e as Error).message}`);
  }
}

/** Get all updates for a given incident */
export async function getUpdates(db: any, incidentId: string): Promise<unknown[]> {
  try {
    const rows = await db
      .prepare('SELECT * FROM incident_updates WHERE incident_id = ? ORDER BY created_at ASC')
      .bind(incidentId)
      .all();
    return rows.results;
  } catch (e: unknown) {
    throw new Error(`getUpdates failed: ${(e as Error).message}`);
  }
}

/** Dashboard summary: counts by status and severity */
export async function getDashboard(db: any): Promise<unknown> {
  try {
    const byStatus = await db
      .prepare('SELECT status, COUNT(*) as count FROM incidents GROUP BY status')
      .all();
    const bySeverity = await db
      .prepare('SELECT severity, COUNT(*) as count FROM incidents GROUP BY severity')
      .all();
    const recentUpdates = await db
      .prepare('SELECT * FROM incident_updates ORDER BY created_at DESC LIMIT 10')
      .all();
    return {
      by_status: byStatus.results,
      by_severity: bySeverity.results,
      recent_updates: recentUpdates.results,
    };
  } catch (e: unknown) {
    throw new Error(`getDashboard failed: ${(e as Error).message}`);
  }
}

export const adminIncidentResponseService = {
  listIncidents,
  createIncident,
  getUpdates,
  getDashboard,
};
