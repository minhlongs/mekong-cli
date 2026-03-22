/**
 * Tenant Event Replay routes — configure and inspect event replay jobs
 *
 * Tenant (auth required):
 *   GET  /event-replay/configs       — list replay configs for tenant
 *   POST /event-replay/configs       — create replay config
 *   GET  /event-replay/runs          — list replay runs (optional ?config_id=)
 *
 * Admin (X-Admin-Key required):
 *   GET  /event-replay/admin/overview — aggregate stats across all tenants
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantEventReplayService } from '../services/tenant-event-replay-service';

export const tenantEventReplay = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Tenant routes
// ---------------------------------------------------------------------------

tenantEventReplay.get('/configs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const configs = await tenantEventReplayService.listConfigs(c.env.DB, tenantId);
    return json({ configs });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

tenantEventReplay.post('/configs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{
      source_event_type: string;
      target_endpoint: string;
      filter_json?: string;
      replay_speed?: number;
    }>();
    if (!body.source_event_type || !body.target_endpoint) {
      return json({ error: 'source_event_type and target_endpoint are required' }, { status: 400 });
    }
    const config = await tenantEventReplayService.createConfig(c.env.DB, tenantId, body);
    return json({ config }, { status: 201 });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

tenantEventReplay.get('/runs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const configId = c.req.query('config_id');
  try {
    const runs = await tenantEventReplayService.getRuns(c.env.DB, tenantId, configId);
    return json({ runs });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin route
// ---------------------------------------------------------------------------

tenantEventReplay.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  try {
    const overview = await tenantEventReplayService.getAdminOverview(c.env.DB);
    return json({ overview });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});
