/**
 * Mission Quality Scoring routes
 *
 * Tenant-scoped (requires auth):
 *   GET  /scores           — list quality scores (query: mission_id)
 *   POST /scores           — create a quality score
 *   GET  /criteria         — list scoring criteria for tenant
 *
 * Admin (requires X-Admin-Key):
 *   GET  /admin/overview   — per-tenant scoring overview
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionQualityScoringService } from '../services/mission-quality-scoring';

// Inline Bindings — no import from index to keep file self-contained
const app = new Hono<{
  Bindings: {
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
}>();

// ─── Tenant routes ────────────────────────────────────────────────────────────

/**
 * GET /scores
 * List quality scores for the authenticated tenant.
 * Query param: mission_id (optional filter)
 */
app.get('/scores', auth(), async (c) => {
  const tenant = getTenant(c);
  const missionId = c.req.query('mission_id');
  try {
    const result = await missionQualityScoringService.listScores(
      c.env.DB,
      tenant.tenantId,
      missionId || undefined
    );
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to list quality scores' }, 500);
  }
});

/**
 * POST /scores
 * Create a quality score for a mission.
 * Body: { mission_id, accuracy_score?, completeness_score?, timeliness_score?, overall_score?, scored_by? }
 */
app.post('/scores', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return c.json({ error: 'Invalid JSON body' }, 400);
  }

  const missionId = typeof body.mission_id === 'string' ? body.mission_id.trim() : '';
  if (!missionId) {
    return c.json({ error: 'mission_id is required' }, 400);
  }

  try {
    const result = await missionQualityScoringService.createScore(c.env.DB, tenant.tenantId, {
      mission_id: missionId,
      accuracy_score: typeof body.accuracy_score === 'number' ? body.accuracy_score : undefined,
      completeness_score: typeof body.completeness_score === 'number' ? body.completeness_score : undefined,
      timeliness_score: typeof body.timeliness_score === 'number' ? body.timeliness_score : undefined,
      overall_score: typeof body.overall_score === 'number' ? body.overall_score : undefined,
      scored_by: typeof body.scored_by === 'string' ? body.scored_by : undefined,
    });
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Failed to create quality score' }, 500);
  }
});

/**
 * GET /criteria
 * List quality scoring criteria for the authenticated tenant.
 */
app.get('/criteria', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await missionQualityScoringService.getCriteria(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch quality criteria' }, 500);
  }
});

// ─── Admin route ──────────────────────────────────────────────────────────────

/**
 * GET /admin/overview
 * Platform-wide scoring overview grouped by tenant.
 * Requires X-Admin-Key header matching ADMIN_API_KEY env var.
 */
app.get('/admin/overview', async (c) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Forbidden' }, 403);
  }
  try {
    const result = await missionQualityScoringService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as missionQualityScoring };
