/**
 * Public status page + admin incident management endpoints
 * Public: GET /status, GET /status/incidents, GET /status/history
 * Admin (X-Admin-Key): POST /status/incidents, PUT /status/incidents/:id, POST /status/incidents/:id/resolve
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';

export const status = new Hono<{ Bindings: Env }>();

const COMPONENTS = ['API', 'Database', 'AI Engine', 'Docs', 'Dashboard'];

// Determine overall status from active incidents
function overallStatus(activeIncidents: any[]): 'operational' | 'degraded' | 'outage' {
  if (!activeIncidents.length) return 'operational';
  const hasCritical = activeIncidents.some((i) => i.severity === 'critical');
  const hasMajor = activeIncidents.some((i) => i.severity === 'major');
  return hasCritical || hasMajor ? 'outage' : 'degraded';
}

// Build component statuses based on affected_components in active incidents
function buildComponents(activeIncidents: any[]) {
  const affected = new Set<string>();
  for (const inc of activeIncidents) {
    try {
      const comps: string[] = JSON.parse(inc.affected_components || '[]');
      comps.forEach((c) => affected.add(c));
    } catch { /* ignore parse errors */ }
  }
  return COMPONENTS.map((name) => ({
    name,
    status: affected.has(name) ? 'degraded' : 'operational',
  }));
}

// Admin auth middleware — same pattern as admin.ts
const adminAuth = () => async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  await next();
};

// GET /status — overall system status summary
status.get('/', async (c) => {
  try {
    const active = await c.env.DB.prepare(
      `SELECT id, title, severity, status, affected_components, started_at
       FROM incidents WHERE status != 'resolved' ORDER BY started_at DESC`
    ).all();

    // Simple uptime: count resolved incidents vs total in last 30 days
    const stats = await c.env.DB.prepare(
      `SELECT COUNT(*) as total,
        SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) as resolved
       FROM incidents WHERE started_at >= datetime('now', '-30 days')`
    ).first<{ total: number; resolved: number }>();

    const total = stats?.total ?? 0;
    const uptime = total === 0 ? 100 : Math.round(((stats?.resolved ?? 0) / total) * 1000) / 10;

    return json({
      status: overallStatus(active.results),
      uptime,
      components: buildComponents(active.results),
      activeIncidents: active.results,
      updatedAt: new Date().toISOString(),
    });
  } catch {
    return json({ error: 'Failed to fetch status' }, { status: 500 });
  }
});

// GET /status/incidents — recent incidents (last 90 days) with updates, paginated
status.get('/incidents', async (c) => {
  const limit = Math.min(Number(c.req.query('limit') || 20), 100);
  const offset = Number(c.req.query('offset') || 0);

  try {
    const incidents = await c.env.DB.prepare(
      `SELECT id, title, description, severity, status, affected_components, started_at, resolved_at, created_at
       FROM incidents WHERE started_at >= datetime('now', '-90 days')
       ORDER BY started_at DESC LIMIT ? OFFSET ?`
    ).bind(limit, offset).all();

    // Fetch updates for returned incidents
    const ids = incidents.results.map((i: any) => i.id);
    const updates = ids.length
      ? await c.env.DB.prepare(
          `SELECT id, incident_id, status, message, created_at FROM incident_updates
           WHERE incident_id IN (${ids.map(() => '?').join(',')})
           ORDER BY created_at ASC`
        ).bind(...ids).all()
      : { results: [] };

    // Group updates by incident_id
    const updateMap: Record<string, any[]> = {};
    for (const u of updates.results as any[]) {
      if (!updateMap[u.incident_id]) updateMap[u.incident_id] = [];
      updateMap[u.incident_id].push(u);
    }

    return json({
      incidents: (incidents.results as any[]).map((i) => ({
        ...i,
        updates: updateMap[i.id] || [],
      })),
      limit,
      offset,
    });
  } catch {
    return json({ error: 'Failed to fetch incidents' }, { status: 500 });
  }
});

// GET /status/history — daily uptime % for last 30 days
status.get('/history', async (c) => {
  try {
    const rows = await c.env.DB.prepare(
      `SELECT date(started_at) as day,
        COUNT(*) as total,
        SUM(CASE WHEN status='resolved' THEN 1 ELSE 0 END) as resolved
       FROM incidents WHERE started_at >= datetime('now', '-30 days')
       GROUP BY date(started_at) ORDER BY day ASC`
    ).all();

    const history = (rows.results as any[]).map((r) => ({
      date: r.day,
      uptime: r.total === 0 ? 100 : Math.round((r.resolved / r.total) * 1000) / 10,
      incidents: r.total,
    }));

    return json({ history });
  } catch {
    return json({ error: 'Failed to fetch history' }, { status: 500 });
  }
});

// POST /status/incidents — create new incident (admin)
status.post('/incidents', adminAuth(), async (c) => {
  try {
    const body = await c.req.json();
    const { title, description, severity = 'minor', affected_components = [] } = body;
    if (!title) return json({ error: 'title required' }, { status: 400 });

    const id = crypto.randomUUID();
    await c.env.DB.prepare(
      `INSERT INTO incidents (id, title, description, severity, status, affected_components)
       VALUES (?, ?, ?, ?, 'investigating', ?)`
    ).bind(id, title, description || null, severity, JSON.stringify(affected_components)).run();

    return json({ id, status: 'investigating' }, { status: 201 });
  } catch {
    return json({ error: 'Failed to create incident' }, { status: 500 });
  }
});

// PUT /status/incidents/:id — add update to incident (admin)
status.put('/incidents/:id', adminAuth(), async (c) => {
  const incidentId = c.req.param('id');
  try {
    const { status: newStatus, message } = await c.req.json();
    if (!newStatus || !message) return json({ error: 'status and message required' }, { status: 400 });

    const updateId = crypto.randomUUID();
    await c.env.DB.batch([
      c.env.DB.prepare(
        `INSERT INTO incident_updates (id, incident_id, status, message) VALUES (?, ?, ?, ?)`
      ).bind(updateId, incidentId, newStatus, message),
      c.env.DB.prepare(
        `UPDATE incidents SET status=?, updated_at=datetime('now') WHERE id=?`
      ).bind(newStatus, incidentId),
    ]);

    return json({ updateId, incidentId, status: newStatus });
  } catch {
    return json({ error: 'Failed to update incident' }, { status: 500 });
  }
});

// POST /status/incidents/:id/resolve — resolve incident (admin)
status.post('/incidents/:id/resolve', adminAuth(), async (c) => {
  const incidentId = c.req.param('id');
  try {
    const updateId = crypto.randomUUID();
    await c.env.DB.batch([
      c.env.DB.prepare(
        `INSERT INTO incident_updates (id, incident_id, status, message) VALUES (?, ?, 'resolved', 'Incident resolved.')`
      ).bind(updateId, incidentId),
      c.env.DB.prepare(
        `UPDATE incidents SET status='resolved', resolved_at=datetime('now'), updated_at=datetime('now') WHERE id=?`
      ).bind(incidentId),
    ]);

    return json({ incidentId, status: 'resolved' });
  } catch {
    return json({ error: 'Failed to resolve incident' }, { status: 500 });
  }
});
