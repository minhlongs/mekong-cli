// Admin Incident Management Service — platform incidents, outages, resolution tracking

/** List all platform incidents ordered by newest first */
async function listIncidents(db: any): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
  try {
    const rows = await db.prepare(
      `SELECT * FROM platform_incidents ORDER BY created_at DESC`
    ).all();
    return { success: true, data: rows.results };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Create a new platform incident */
async function createIncident(
  db: any,
  data: {
    id: string;
    title: string;
    description?: string;
    severity?: string;
    status?: string;
    affected_services?: string;
    started_at?: string;
  }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const row = await db.prepare(
      `INSERT INTO platform_incidents (id, title, description, severity, status, affected_services, started_at)
       VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(
      data.id,
      data.title,
      data.description ?? null,
      data.severity ?? 'medium',
      data.status ?? 'investigating',
      data.affected_services ?? null,
      data.started_at ?? new Date().toISOString()
    ).first();
    return { success: true, data: row };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Get all incident updates ordered by newest first */
async function getUpdates(db: any): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
  try {
    const rows = await db.prepare(
      `SELECT * FROM platform_incident_updates ORDER BY created_at DESC`
    ).all();
    return { success: true, data: rows.results };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

/** Dashboard: incident counts by status + 5 most recent incidents */
async function getDashboard(db: any): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const [counts, recent] = await Promise.all([
      db.prepare(
        `SELECT status, COUNT(*) as count FROM platform_incidents GROUP BY status`
      ).all(),
      db.prepare(
        `SELECT * FROM platform_incidents ORDER BY created_at DESC LIMIT 5`
      ).all(),
    ]);
    return {
      success: true,
      data: {
        counts_by_status: counts.results,
        recent_incidents: recent.results,
      },
    };
  } catch (e: unknown) {
    return { success: false, error: (e as Error).message };
  }
}

export const adminIncidentManagementService = {
  listIncidents,
  createIncident,
  getUpdates,
  getDashboard,
};
