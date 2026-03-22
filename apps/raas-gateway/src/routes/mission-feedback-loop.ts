/**
 * Mission Feedback Loop routes — tenant feedback on missions + admin overview
 * Auth endpoints require JWT/API-key. Admin endpoint requires X-Admin-Key.
 * Mount path: /v1/mission-feedback
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionFeedbackLoopService as svc } from '../services/mission-feedback-loop-service';

const app = new Hono<{ Bindings: Env }>();

// GET /feedback — list feedback for tenant, optional ?mission_id= filter
app.get('/feedback', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const missionId = c.req.query('mission_id');
    const data = await svc.listFeedback(c.env.DB, tenantId, missionId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /feedback — submit feedback for a mission
app.post('/feedback', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      mission_id: string;
      rating: number;
      feedback_text?: string;
      feedback_type?: string;
    }>();
    if (!body.mission_id) return c.json({ error: 'mission_id is required' }, 400);
    if (body.rating == null) return c.json({ error: 'rating is required' }, 400);
    const data = await svc.createFeedback(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /actions — list resolution actions for tenant, optional ?feedback_id= filter
app.get('/actions', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const feedbackId = c.req.query('feedback_id');
    const data = await svc.getActions(c.env.DB, tenantId, feedbackId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — platform-wide feedback stats (X-Admin-Key required)
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as missionFeedbackLoop };
