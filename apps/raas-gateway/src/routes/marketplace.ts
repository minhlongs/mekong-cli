/**
 * Marketplace route — public gallery of shared, completed missions (social proof)
 * Reviews + leaderboard endpoints require auth; gallery endpoints are public.
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { auth } from '../middleware/auth';

export const marketplace = new Hono<{ Bindings: Env }>();

// GET /marketplace — Public gallery with optional filters
marketplace.get('/', async (c) => {
  const limit = Math.min(parseInt(c.req.query('limit') || '20'), 50);
  const offset = parseInt(c.req.query('offset') || '0');
  const complexity = c.req.query('complexity');
  const search = c.req.query('q');

  let query = `SELECT m.id, m.goal, m.complexity, m.model,
    SUBSTR(m.result, 1, 500) as result,
    m.completed_at, t.name as author
    FROM missions m
    JOIN tenants t ON m.tenant_id = t.id
    WHERE m.is_public = 1 AND m.status = 'completed'`;
  const bindings: (string | number)[] = [];

  if (complexity) {
    query += ' AND m.complexity = ?';
    bindings.push(complexity);
  }
  if (search) {
    query += ' AND m.goal LIKE ?';
    bindings.push(`%${search}%`);
  }

  query += ' ORDER BY m.completed_at DESC LIMIT ? OFFSET ?';
  bindings.push(limit, offset);

  try {
    const [missions, countRow] = await Promise.all([
      c.env.DB.prepare(query).bind(...bindings).all(),
      c.env.DB.prepare(
        "SELECT COUNT(*) as total FROM missions WHERE is_public = 1 AND status = 'completed'"
      ).first<{ total: number }>(),
    ]);

    return json({
      missions: missions.results,
      total: countRow?.total || 0,
      pagination: { limit, offset },
    });
  } catch {
    return json({ error: 'Failed to fetch marketplace' }, { status: 500 });
  }
});

// GET /marketplace/featured — Top 5 most recent shared missions
marketplace.get('/featured', async (c) => {
  try {
    const missions = await c.env.DB.prepare(
      `SELECT m.id, m.goal, m.complexity,
        SUBSTR(m.result, 1, 500) as result,
        m.completed_at, t.name as author
       FROM missions m
       JOIN tenants t ON m.tenant_id = t.id
       WHERE m.is_public = 1 AND m.status = 'completed'
       ORDER BY m.completed_at DESC LIMIT 5`
    ).all();

    return json({ featured: missions.results });
  } catch {
    return json({ error: 'Failed to fetch featured missions' }, { status: 500 });
  }
});

// GET /marketplace/stats — Aggregate statistics for the marketplace
marketplace.get('/stats', async (c) => {
  try {
    const stats = await c.env.DB.prepare(
      `SELECT COUNT(*) as totalShared,
        COUNT(DISTINCT tenant_id) as uniqueAuthors,
        SUM(CASE WHEN complexity = 'simple' THEN 1 ELSE 0 END) as simple,
        SUM(CASE WHEN complexity = 'standard' THEN 1 ELSE 0 END) as standard,
        SUM(CASE WHEN complexity = 'complex' THEN 1 ELSE 0 END) as complex
       FROM missions WHERE is_public = 1 AND status = 'completed'`
    ).first();

    return json(stats || {});
  } catch {
    return json({ error: 'Failed to fetch marketplace stats' }, { status: 500 });
  }
});

// GET /marketplace/leaderboard — top referrers by referral count
marketplace.get('/leaderboard', async (c) => {
  try {
    const leaders = await c.env.DB.prepare(
      `SELECT t.name, t.referral_code, COUNT(r.id) as referral_count, COUNT(r.id) * 5 as credits_earned
       FROM tenants t
       LEFT JOIN tenants r ON r.referred_by = t.referral_code
       WHERE t.referral_code IS NOT NULL
       GROUP BY t.id
       HAVING referral_count > 0
       ORDER BY referral_count DESC
       LIMIT 10`
    ).all();
    return json({ leaderboard: leaders.results });
  } catch {
    return json({ error: 'Failed to fetch leaderboard' }, { status: 500 });
  }
});

// GET /marketplace/:id/reviews — ratings and comments for a mission
marketplace.get('/:id/reviews', async (c) => {
  const missionId = c.req.param('id');
  try {
    const [reviews, avg] = await Promise.all([
      c.env.DB.prepare(
        `SELECT r.rating, r.comment, r.created_at, t.name as author
         FROM reviews r
         JOIN tenants t ON r.tenant_id = t.id
         WHERE r.mission_id = ?
         ORDER BY r.created_at DESC
         LIMIT 20`
      ).bind(missionId).all(),
      c.env.DB.prepare(
        `SELECT AVG(rating) as avg_rating, COUNT(*) as total
         FROM reviews WHERE mission_id = ?`
      ).bind(missionId).first<{ avg_rating: number; total: number }>(),
    ]);
    return json({
      reviews: reviews.results,
      avgRating: avg?.avg_rating || 0,
      totalReviews: avg?.total || 0,
    });
  } catch {
    return json({ error: 'Failed to fetch reviews' }, { status: 500 });
  }
});

// POST /marketplace/:id/reviews — submit a review (requires auth)
marketplace.post('/:id/reviews', auth(), async (c) => {
  const missionId = c.req.param('id');
  const tenant = c.get('tenant');

  let body: { rating?: unknown; comment?: unknown };
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const rating = Number(body.rating);
  if (!Number.isInteger(rating) || rating < 1 || rating > 5) {
    return json({ error: 'rating must be an integer between 1 and 5' }, { status: 400 });
  }

  const comment = typeof body.comment === 'string' ? body.comment.slice(0, 1000) : null;

  try {
    // Verify the mission exists and is public
    const mission = await c.env.DB.prepare(
      `SELECT id FROM missions WHERE id = ? AND is_public = 1 AND status = 'completed'`
    ).bind(missionId).first();
    if (!mission) {
      return json({ error: 'Mission not found or not reviewable' }, { status: 404 });
    }

    const id = crypto.randomUUID();
    await c.env.DB.prepare(
      `INSERT INTO reviews (id, mission_id, tenant_id, rating, comment) VALUES (?, ?, ?, ?, ?)`
    ).bind(id, missionId, tenant.tenantId, rating, comment).run();

    return json({ id, missionId, rating, comment }, { status: 201 });
  } catch {
    return json({ error: 'Failed to submit review' }, { status: 500 });
  }
});
