/**
 * Tenant API Changelog Routes
 * Per-tenant changelog entries and email subscriptions.
 *
 * GET  /entries        — list changelog entries (auth)
 * POST /entries        — create changelog entry (auth)
 * GET  /subscriptions  — list email subscriptions (auth)
 * GET  /admin/overview — cross-tenant stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiChangelogService } from '../services/tenant-api-changelog-service';

const app = new Hono<{ Bindings: Env }>();

// GET /entries — list changelog entries for authenticated tenant
app.get('/entries', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const entries = await tenantApiChangelogService.listEntries(c.env.DB, tenantId);
    return c.json({ entries, total: entries.length });
  } catch (err) {
    return c.json({ error: 'Failed to list changelog entries' }, 500);
  }
});

// POST /entries — create a new changelog entry for authenticated tenant
app.post('/entries', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      change_type?: string;
      endpoint?: string;
      description?: string;
      breaking?: number;
      version?: string;
    };

    const endpoint = body.endpoint?.trim();
    const description = body.description?.trim();
    const version = body.version?.trim();

    if (!endpoint)    return c.json({ error: 'endpoint is required', code: 'VALIDATION_ERROR' }, 400);
    if (!description) return c.json({ error: 'description is required', code: 'VALIDATION_ERROR' }, 400);
    if (!version)     return c.json({ error: 'version is required', code: 'VALIDATION_ERROR' }, 400);

    const entry = await tenantApiChangelogService.createEntry(c.env.DB, tenantId, {
      change_type: body.change_type,
      endpoint,
      description,
      breaking: body.breaking,
      version,
    });

    return c.json(entry, 201);
  } catch (err) {
    return c.json({ error: 'Failed to create changelog entry' }, 500);
  }
});

// GET /subscriptions — list email subscriptions for authenticated tenant
app.get('/subscriptions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const subscriptions = await tenantApiChangelogService.getSubscriptions(c.env.DB, tenantId);
    return c.json({ subscriptions, total: subscriptions.length });
  } catch (err) {
    return c.json({ error: 'Failed to list subscriptions' }, 500);
  }
});

// GET /admin/overview — cross-tenant stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden', code: 'FORBIDDEN' }, 403);
  }
  try {
    const overview = await tenantApiChangelogService.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (err) {
    return c.json({ error: 'Failed to get admin overview' }, 500);
  }
});

export { app as tenantApiChangelog };
