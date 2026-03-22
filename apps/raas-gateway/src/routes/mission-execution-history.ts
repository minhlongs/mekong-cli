/**
 * Mission Execution History routes — list/record executions and metrics
 *
 * Authenticated tenant routes:
 *   GET  /executions        — list execution history for tenant (query: mission_id)
 *   POST /executions        — record a new execution for tenant
 *   GET  /metrics           — get execution metrics for tenant
 *
 * Admin route (X-Admin-Key header required):
 *   GET  /admin/overview    — count executions and metrics across all tenants
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionExecutionHistoryService } from '../services/mission-execution-history';
import { json } from '../utils/response';

type Bindings = {
  DB: any;
  RATE_LIMIT_KV: any;
  SESSION_KV: any;
  AI: any;
  JWT_SECRET=REDACTED: string;
  POLAR_WEBHOOK_SECRET: string;
  TELEGRAM_BOT_TOKEN: string;
  ENVIRONMENT: string;
  LOG_LEVEL: string;
  ADMIN_API_KEY: string;
};

const app = new Hono<{ Bindings: Bindings }>();

// ─── Auth middleware ──────────────────────────────────────────────────────────

app.use('/executions', auth());
app.use('/metrics', auth());

// ─── Tenant routes ────────────────────────────────────────────────────────────

/**
 * GET /executions
 * List execution history for the authenticated tenant.
 * Query param: mission_id (optional filter)
 */
app.get('/executions', async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.query('mission_id');

  try {
    const history = await missionExecutionHistoryService.listHistory(
      c.env.DB,
      tenant.tenantId,
      missionId || undefined
    );
    return json({ success: true, data: history });
  } catch (err) {
    console.error('[execution-history] GET /executions error', err);
    return json({ success: false, error: 'Failed to fetch execution history' }, { status: 500 });
  }
});

/**
 * POST /executions
 * Record a new execution entry for the authenticated tenant.
 * Body: { mission_id?, executor_type?, status?, duration_ms?, input_summary?, output_summary?, error_message? }
 */
app.post('/executions', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  try {
    const result = await missionExecutionHistoryService.recordExecution(
      c.env.DB,
      tenant.tenantId,
      {
        mission_id: typeof body.mission_id === 'string' ? body.mission_id : undefined,
        executor_type: typeof body.executor_type === 'string' ? body.executor_type : undefined,
        status: typeof body.status === 'string' ? body.status : 'completed',
        duration_ms: typeof body.duration_ms === 'number' ? body.duration_ms : undefined,
        input_summary: typeof body.input_summary === 'string' ? body.input_summary : undefined,
        output_summary: typeof body.output_summary === 'string' ? body.output_summary : undefined,
        error_message: typeof body.error_message === 'string' ? body.error_message : undefined,
      }
    );

    if (!result.success) {
      return json({ success: false, error: 'Failed to record execution' }, { status: 500 });
    }

    return json({ success: true, data: { id: result.id } }, { status: 201 });
  } catch (err) {
    console.error('[execution-history] POST /executions error', err);
    return json({ success: false, error: 'Failed to record execution' }, { status: 500 });
  }
});

/**
 * GET /metrics
 * Get execution metrics for the authenticated tenant.
 */
app.get('/metrics', async (c) => {
  const tenant = getTenant(c);

  try {
    const metrics = await missionExecutionHistoryService.getMetrics(c.env.DB, tenant.tenantId);
    return json({ success: true, data: metrics });
  } catch (err) {
    console.error('[execution-history] GET /metrics error', err);
    return json({ success: false, error: 'Failed to fetch metrics' }, { status: 500 });
  }
});

// ─── Admin route ──────────────────────────────────────────────────────────────

/**
 * GET /admin/overview
 * Returns execution and metrics counts across all tenants.
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var.
 */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');

  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ success: false, error: 'Forbidden' }, { status: 403 });
  }

  try {
    const overview = await missionExecutionHistoryService.getAdminOverview(c.env.DB);
    return json({ success: true, data: overview });
  } catch (err) {
    console.error('[execution-history] GET /admin/overview error', err);
    return json({ success: false, error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});

export { app as missionExecutionHistory };
