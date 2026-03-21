/**
 * API Versioning routes — version discovery, changelog, usage stats
 *
 * Public:  GET /api/versions, /:version, /:version/changelog, /migrate/:from/:to
 * Admin:   POST /:version/changelog, GET /usage
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import {
  getVersionInfo, isVersionSupported, getDeprecationWarnings,
  getVersionChangelog, addChangelogEntry, getVersionUsageStats, getMigrationGuide,
} from '../services/api-versioning-service';

export const apiVersioning = new Hono<{ Bindings: Env }>();

const isAdmin = (c: { req: { header: (k: string) => string | undefined }; env: Env }) =>
  Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);

// ---------------------------------------------------------------------------
// Public
// ---------------------------------------------------------------------------

apiVersioning.get('/', (c) => c.json({ success: true, data: getVersionInfo() }));

apiVersioning.get('/migrate/:from/:to', (c) => {
  const from = c.req.param('from');
  const to = c.req.param('to');
  return c.json({ success: true, data: { from, to, steps: getMigrationGuide(from, to) } });
});

apiVersioning.get('/:version', (c) => {
  const version = c.req.param('version');
  const info = getVersionInfo().find((v) => v.version === version);
  if (!info) return json({ error: 'Version not found', code: 'NOT_FOUND' }, { status: 404 });
  return c.json({ success: true, data: info, warnings: getDeprecationWarnings(version) });
});

apiVersioning.get('/:version/changelog', async (c) => {
  const version = c.req.param('version');
  if (!isVersionSupported(version)) return json({ error: 'Version not found', code: 'NOT_FOUND' }, { status: 404 });
  try {
    return c.json({ success: true, data: await getVersionChangelog(c.env.DB, version) });
  } catch {
    return json({ error: 'Failed to fetch changelog' }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------

apiVersioning.get('/usage', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  const days = Math.min(parseInt(c.req.query('days') ?? '30', 10) || 30, 90);
  try {
    return c.json({ success: true, data: await getVersionUsageStats(c.env.DB, days), meta: { days } });
  } catch {
    return json({ error: 'Failed to fetch usage stats' }, { status: 500 });
  }
});

apiVersioning.post('/:version/changelog', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  const version = c.req.param('version');
  if (!isVersionSupported(version)) return json({ error: 'Version not found', code: 'NOT_FOUND' }, { status: 404 });

  const body = await c.req.json<{ title: string; description?: string; type: 'added' | 'changed' | 'deprecated' | 'removed' }>();
  const VALID = ['added', 'changed', 'deprecated', 'removed'];
  if (!body.title || !body.type) return json({ error: 'Missing required: title, type', code: 'VALIDATION_ERROR' }, { status: 400 });
  if (!VALID.includes(body.type)) return json({ error: `type must be: ${VALID.join(', ')}`, code: 'VALIDATION_ERROR' }, { status: 400 });

  try {
    const entry = await addChangelogEntry(c.env.DB, version, body.title, body.description ?? '', body.type);
    return c.json({ success: true, data: entry }, 201);
  } catch {
    return json({ error: 'Failed to add changelog entry' }, { status: 500 });
  }
});
