/**
 * Data Retention routes — tenant CRUD + purge execution + admin cron endpoints
 * Tenant (JWT/API key): GET/POST /policies, PUT/DELETE /policies/:id, GET /stats, POST /purge/:id, GET /logs, POST /seed
 * Admin (X-Admin-Key): GET /admin/due, POST /admin/run-all
 *
 * IMPORTANT: /stats, /logs, /seed, /admin/* mounted BEFORE /:id to avoid shadowing
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  createPolicy,
  getPolicies,
  getPolicyById,
  updatePolicy,
  deletePolicy,
  executePurge,
  getDuePolicies,
  getPurgeLogs,
  VALID_DATA_TYPES,
} from '../services/data-retention-service';
import { getRetentionStats, seedDefaultPolicies } from '../services/data-retention-helpers';

const app = new Hono<{ Bindings: Env }>();

function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// ── All tenant routes require auth ───────────────────────────────────────────
app.use('/*', auth());

// ── GET /stats — count records that would be purged per data type ─────────────
app.get('/stats', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const stats = await getRetentionStats(c.env.DB, tenantId);
    return c.json({ success: true, data: stats });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── GET /logs — purge execution history ───────────────────────────────────────
app.get('/logs', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const logs = await getPurgeLogs(c.env.DB, tenantId);
    return c.json({ success: true, data: logs });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── POST /seed — seed default 90-day policies for all data types ──────────────
app.post('/seed', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const policies = await seedDefaultPolicies(c.env.DB, tenantId);
    return c.json({ success: true, data: policies }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── POST /purge/:id — manually trigger purge for a specific policy ────────────
app.post('/purge/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const policyId = c.req.param('id');
  try {
    const log = await executePurge(c.env.DB, tenantId, policyId);
    return c.json({ success: true, data: log });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : 'Purge failed';
    if (msg === 'Policy not found') return c.json({ success: false, error: msg }, 404);
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── Admin: GET /admin/due — list all auto-purge policies due for cron ─────────
app.get('/admin/due', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const policies = await getDuePolicies(c.env.DB);
    return c.json({ success: true, data: policies });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── Admin: POST /admin/run-all — execute all due auto-purge policies ──────────
app.post('/admin/run-all', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const policies = await getDuePolicies(c.env.DB);
    const results = await Promise.allSettled(
      policies.map(p => executePurge(c.env.DB, p.tenant_id, p.id))
    );
    const logs = results
      .filter((r): r is PromiseFulfilledResult<Awaited<ReturnType<typeof executePurge>>> => r.status === 'fulfilled')
      .map(r => r.value);
    const errors = results.filter(r => r.status === 'rejected').length;
    return c.json({ success: true, data: { executed: logs.length, errors, logs } });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── GET /policies — list all policies for tenant ──────────────────────────────
app.get('/policies', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const policies = await getPolicies(c.env.DB, tenantId);
    return c.json({ success: true, data: policies });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── POST /policies — create or upsert a policy ────────────────────────────────
app.post('/policies', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{
      data_type: string;
      retention_days: number;
      auto_purge?: boolean;
      archive_before_purge?: boolean;
    }>();

    if (!body.data_type || !VALID_DATA_TYPES.includes(body.data_type)) {
      return c.json({ success: false, error: `data_type must be one of: ${VALID_DATA_TYPES.join(', ')}` }, 400);
    }
    if (!body.retention_days || body.retention_days < 1) {
      return c.json({ success: false, error: 'retention_days must be >= 1' }, 400);
    }

    const policy = await createPolicy(
      c.env.DB, tenantId, body.data_type, body.retention_days,
      body.auto_purge ?? false, body.archive_before_purge ?? true,
    );
    return c.json({ success: true, data: policy }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── PUT /policies/:id — update policy fields ──────────────────────────────────
app.put('/policies/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const policyId = c.req.param('id');
  try {
    const body = await c.req.json();
    const existing = await getPolicyById(c.env.DB, tenantId, policyId);
    if (!existing) return c.json({ success: false, error: 'Policy not found' }, 404);

    const updated = await updatePolicy(c.env.DB, tenantId, policyId, body);
    return c.json({ success: true, data: updated });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

// ── DELETE /policies/:id — remove a policy ────────────────────────────────────
app.delete('/policies/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const policyId = c.req.param('id');
  try {
    const deleted = await deletePolicy(c.env.DB, tenantId, policyId);
    if (!deleted) return c.json({ success: false, error: 'Policy not found' }, 404);
    return c.json({ success: true, data: { deleted: true } });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export const dataRetention = app;
