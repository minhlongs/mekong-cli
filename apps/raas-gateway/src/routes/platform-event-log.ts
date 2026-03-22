/**
 * Platform Event Log routes — log, query, and manage platform events
 * Admin endpoints require X-Admin-Key header. Mount path: /platform/events
 */

import { Hono } from 'hono';
import {
  logEvent,
  getEvents,
  getEvent,
  listCategories,
  createCategory,
  getRetentionConfigs,
  updateRetentionConfig,
  purgeExpired,
  getEventStats,
  getAdminOverview,
} from '../services/platform-event-log-service';

type Env = { Bindings: { DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any; JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string; TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string; LOG_LEVEL: string; ADMIN_API_KEY: string } };

const app = new Hono<Env>();

// Admin auth middleware — applied to all routes except GET /categories
app.use('*', async (c, next) => {
  // Allow public GET /categories
  if (c.req.method === 'GET' && c.req.path.endsWith('/categories')) {
    return next();
  }
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  return next();
});

// POST /events — log a new event
app.post('/events', async (c) => {
  try {
    const body = await c.req.json<{
      event_type: string;
      category?: string;
      source?: string;
      actor_id?: string;
      tenant_id?: string;
      payload?: Record<string, unknown>;
      severity?: string;
    }>();
    if (!body.event_type) return c.json({ error: 'event_type is required' }, 400);
    const event = await logEvent(c.env.DB, body);
    return c.json({ event }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /events — list events with optional filters
app.get('/events', async (c) => {
  try {
    const limit = parseInt(c.req.query('limit') ?? '50', 10);
    const events = await getEvents(c.env.DB, {
      event_type: c.req.query('event_type'),
      category:   c.req.query('category'),
      tenant_id:  c.req.query('tenant_id'),
      severity:   c.req.query('severity'),
      since:      c.req.query('since'),
      limit,
    });
    return c.json({ events, count: events.length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /events/:id — get a single event
app.get('/events/:id', async (c) => {
  try {
    const event = await getEvent(c.env.DB, c.req.param('id'));
    if (!event) return c.json({ error: 'Not found' }, 404);
    return c.json({ event });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /categories — list categories (public)
app.get('/categories', async (c) => {
  try {
    const categories = await listCategories(c.env.DB);
    return c.json({ categories });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /categories — create a category (admin)
app.post('/categories', async (c) => {
  try {
    const body = await c.req.json<{ name: string; description?: string; color?: string; icon?: string }>();
    if (!body.name) return c.json({ error: 'name is required' }, 400);
    const category = await createCategory(c.env.DB, body);
    return c.json({ category }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /retention — list retention configs (admin)
app.get('/retention', async (c) => {
  try {
    const configs = await getRetentionConfigs(c.env.DB);
    return c.json({ configs });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /retention/:category — update retention config (admin)
app.put('/retention/:category', async (c) => {
  try {
    const body = await c.req.json<{ retention_days?: number; archive_enabled?: number }>();
    const config = await updateRetentionConfig(c.env.DB, c.req.param('category'), body);
    if (!config) return c.json({ error: 'Category not found' }, 404);
    return c.json({ config });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /purge — purge expired events (admin)
app.post('/purge', async (c) => {
  try {
    const result = await purgeExpired(c.env.DB);
    return c.json(result);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /stats — event statistics (admin)
app.get('/stats', async (c) => {
  try {
    const stats = await getEventStats(c.env.DB);
    return c.json({ stats });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — admin overview (admin)
app.get('/dashboard', async (c) => {
  try {
    const overview = await getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as platformEventLog };
