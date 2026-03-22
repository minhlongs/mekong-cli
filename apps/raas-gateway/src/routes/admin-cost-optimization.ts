/**
 * Admin Cost Optimization routes — recommendations and actions management
 * All endpoints require X-Admin-Key header
 * Mounted at /v1/admin/cost-optimization in parent router
 */

import { Hono } from 'hono';
import { adminCostOptimizationService } from '../services/admin-cost-optimization';

interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
}

const app = new Hono<{ Bindings: Bindings }>();

/** Returns true when request carries a valid admin key */
function isAdmin(c: { req: { header: (k: string) => string | undefined }; env: Bindings }): boolean {
  return !!c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY;
}

// GET /recommendations — list all recommendations (filterable by category, status, priority)
app.get('/recommendations', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const category = c.req.query('category');
    const status   = c.req.query('status');
    const priority = c.req.query('priority');
    const result = await adminCostOptimizationService.listRecommendations(c.env.DB, { category, status, priority });
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /recommendations — create a new recommendation
app.post('/recommendations', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const body = await c.req.json<{
      category: string;
      title: string;
      description?: string;
      estimated_savings?: number;
      priority?: string;
      status?: string;
    }>();

    if (!body.category?.trim()) return c.json({ success: false, error: 'category is required' }, 400);
    if (!body.title?.trim())    return c.json({ success: false, error: 'title is required' }, 400);

    const result = await adminCostOptimizationService.createRecommendation(c.env.DB, body);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /actions — list actions (filterable by recommendation_id, action_type)
app.get('/actions', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const recommendation_id = c.req.query('recommendation_id');
    const action_type       = c.req.query('action_type');
    const result = await adminCostOptimizationService.getActions(c.env.DB, { recommendation_id, action_type });
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /dashboard — aggregated cost optimization dashboard
app.get('/dashboard', async (c) => {
  if (!isAdmin(c)) return c.json({ success: false, error: 'Admin key required' }, 403);
  try {
    const result = await adminCostOptimizationService.getDashboard(c.env.DB);
    if (!result.success) return c.json({ success: false, error: result.error }, 500);
    return c.json(result);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as adminCostOptimization };
