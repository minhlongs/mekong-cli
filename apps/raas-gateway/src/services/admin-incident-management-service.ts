// Admin Incident Management Service — incident tracking, updates, postmortems
import type { D1Database } from '@cloudflare/workers-types';

// --- Incidents ---

/** List incidents with optional status/severity filters */
export async function listIncidents(
  db: D1Database,
  status?: string,
  severity?: string,
  limit = 50
): Promise<unknown[]> {
  const conditions: string[] = [];
  const binds: unknown[] = [];

  if (status) { conditions.push('status = ?'); binds.push(status); }
  if (severity) { conditions.push('severity = ?'); binds.push(severity); }

  const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
  binds.push(Math.min(limit, 200));

  const rows = await db.prepare(
    `SELECT * FROM incidents ${where} ORDER BY created_at DESC LIMIT ?`
  ).bind(...binds).all();
  return rows.results;
}

/** Create a new incident */
export async function createIncident(
  db: D1Database,
  title: string,
  createdBy: string,
  opts: {
    description?: string;
    severity?: string;
    impact?: string;
    affectedServices?: string[];
    startedAt?: string;
  } = {}
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO incidents (title, description, severity, impact, affected_services, started_at, created_by)
     VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    title,
    opts.description ?? null,
    opts.severity ?? 'medium',
    opts.impact ?? 'partial',
    JSON.stringify(opts.affectedServices ?? []),
    opts.startedAt ?? new Date().toISOString(),
    createdBy
  ).first();
}

/** Get a single incident by ID */
export async function getIncident(db: D1Database, id: string): Promise<unknown | null> {
  return db.prepare(`SELECT * FROM incidents WHERE id = ?`).bind(id).first();
}

/** Update incident fields (status, severity, impact, etc.) */
export async function updateIncident(
  db: D1Database,
  id: string,
  fields: {
    title?: string;
    description?: string;
    severity?: string;
    status?: string;
    impact?: string;
    affectedServices?: string[];
    identifiedAt?: string;
    resolvedAt?: string;
  }
): Promise<unknown | null> {
  const sets: string[] = ['updated_at = datetime(\'now\')'];
  const binds: unknown[] = [];

  if (fields.title !== undefined) { sets.push('title = ?'); binds.push(fields.title); }
  if (fields.description !== undefined) { sets.push('description = ?'); binds.push(fields.description); }
  if (fields.severity !== undefined) { sets.push('severity = ?'); binds.push(fields.severity); }
  if (fields.status !== undefined) { sets.push('status = ?'); binds.push(fields.status); }
  if (fields.impact !== undefined) { sets.push('impact = ?'); binds.push(fields.impact); }
  if (fields.affectedServices !== undefined) { sets.push('affected_services = ?'); binds.push(JSON.stringify(fields.affectedServices)); }
  if (fields.identifiedAt !== undefined) { sets.push('identified_at = ?'); binds.push(fields.identifiedAt); }
  if (fields.resolvedAt !== undefined) { sets.push('resolved_at = ?'); binds.push(fields.resolvedAt); }

  if (sets.length === 1) return getIncident(db, id); // no-op
  binds.push(id);

  return db.prepare(
    `UPDATE incidents SET ${sets.join(', ')} WHERE id = ? RETURNING *`
  ).bind(...binds).first();
}

// --- Incident Updates ---

/** Add an update entry to an incident */
export async function addUpdate(
  db: D1Database,
  incidentId: string,
  message: string,
  createdBy: string,
  updateType = 'note',
  newStatus?: string
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO incident_updates (incident_id, update_type, message, new_status, created_by)
     VALUES (?, ?, ?, ?, ?) RETURNING *`
  ).bind(incidentId, updateType, message, newStatus ?? null, createdBy).first();
}

/** Get all updates for an incident, newest first */
export async function getUpdates(db: D1Database, incidentId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM incident_updates WHERE incident_id = ? ORDER BY created_at DESC`
  ).bind(incidentId).all();
  return rows.results;
}

// --- Postmortems ---

/** Create or replace postmortem for an incident */
export async function createPostmortem(
  db: D1Database,
  incidentId: string,
  summary: string,
  createdBy: string,
  opts: {
    rootCause?: string;
    timeline?: unknown[];
    actionItems?: string[];
    lessonsLearned?: string;
  } = {}
): Promise<unknown> {
  return db.prepare(
    `INSERT INTO incident_postmortems
       (incident_id, summary, root_cause, timeline, action_items, lessons_learned, created_by)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(incident_id) DO UPDATE SET
       summary = excluded.summary,
       root_cause = excluded.root_cause,
       timeline = excluded.timeline,
       action_items = excluded.action_items,
       lessons_learned = excluded.lessons_learned,
       updated_at = datetime('now')
     RETURNING *`
  ).bind(
    incidentId,
    summary,
    opts.rootCause ?? null,
    opts.timeline ? JSON.stringify(opts.timeline) : null,
    JSON.stringify(opts.actionItems ?? []),
    opts.lessonsLearned ?? null,
    createdBy
  ).first();
}

/** Get postmortem for an incident */
export async function getPostmortem(db: D1Database, incidentId: string): Promise<unknown | null> {
  return db.prepare(
    `SELECT * FROM incident_postmortems WHERE incident_id = ?`
  ).bind(incidentId).first();
}

/** List active (non-resolved) incidents */
export async function getActiveIncidents(db: D1Database): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM incidents WHERE status NOT IN ('resolved', 'postmortem')
     ORDER BY severity DESC, created_at DESC`
  ).all();
  return rows.results;
}

/** Dashboard summary: counts by status and severity */
export async function getDashboard(db: D1Database): Promise<unknown> {
  const [total, active, critical, resolved, withPostmortem] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM incidents`).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM incidents WHERE status NOT IN ('resolved','postmortem')`
    ).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM incidents WHERE severity = 'critical' AND status NOT IN ('resolved','postmortem')`
    ).first<{ count: number }>(),
    db.prepare(
      `SELECT COUNT(*) as count FROM incidents WHERE status = 'resolved'`
    ).first<{ count: number }>(),
    db.prepare(`SELECT COUNT(*) as count FROM incident_postmortems`).first<{ count: number }>(),
  ]);

  return {
    incidents: {
      total: total?.count ?? 0,
      active: active?.count ?? 0,
      criticalActive: critical?.count ?? 0,
      resolved: resolved?.count ?? 0,
      withPostmortem: withPostmortem?.count ?? 0,
    },
  };
}
