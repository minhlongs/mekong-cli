/**
 * Agent Marketplace routes — browse, install, review, publish AI agents
 * Public: browse/featured/detail/reviews
 * Auth: install/uninstall/installed-list/publish/review/publisher-stats
 * Admin: marketplace stats (X-Admin-Key)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  publishAgent,
  listPublishedAgents,
  getFeaturedAgents,
  getAgentBySlug,
  installAgent,
  uninstallAgent,
  listInstalledAgents,
  reviewAgent,
  getAgentReviews,
} from '../services/agent-marketplace-service';
import {
  getPublisherStats,
  getMarketplaceStats,
} from '../services/agent-marketplace-stats-service';

export const agentMarketplace = new Hono<{ Bindings: Env }>();

// ── Admin auth helper ──────────────────────────────────────────────────────────

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Public routes ──────────────────────────────────────────────────────────────

/**
 * GET /browse — list published agents
 * Query: category, search, limit (max 100), offset
 */
agentMarketplace.get('/browse', async (c) => {
  const category = c.req.query('category');
  const search = c.req.query('search');
  const limit = Math.min(Number(c.req.query('limit') ?? 20), 100);
  const offset = Number(c.req.query('offset') ?? 0);

  try {
    const agents = await listPublishedAgents(c.env.DB, category, search, limit, offset);
    return json({ agents, total: agents.length, limit, offset });
  } catch (err) {
    return json({ error: 'Failed to list agents', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /featured — top rated + most installed agents
 */
agentMarketplace.get('/featured', async (c) => {
  try {
    const agents = await getFeaturedAgents(c.env.DB);
    return json({ agents });
  } catch (err) {
    return json({ error: 'Failed to fetch featured agents', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /agent/:slug — full agent detail
 */
agentMarketplace.get('/agent/:slug', async (c) => {
  const slug = c.req.param('slug');
  try {
    const agent = await getAgentBySlug(c.env.DB, slug);
    if (!agent) return json({ error: 'Agent not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ agent });
  } catch (err) {
    return json({ error: 'Failed to fetch agent', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /agent/:slug/reviews — list reviews for an agent
 */
agentMarketplace.get('/agent/:slug/reviews', async (c) => {
  const slug = c.req.param('slug');
  try {
    const agent = await getAgentBySlug(c.env.DB, slug);
    if (!agent) return json({ error: 'Agent not found', code: 'NOT_FOUND' }, { status: 404 });

    const reviews = await getAgentReviews(c.env.DB, agent.id);
    return json({ reviews, total: reviews.length });
  } catch (err) {
    return json({ error: 'Failed to fetch reviews', details: String(err) }, { status: 500 });
  }
});

// ── Authenticated routes ───────────────────────────────────────────────────────

/**
 * POST /install/:agentId — install agent for authenticated tenant
 * Body: { config?: string }
 */
agentMarketplace.post('/install/:agentId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const agentId = c.req.param('agentId');
  const body = await c.req.json().catch(() => ({})) as { config?: string };

  try {
    const agent = await c.env.DB.prepare('SELECT id, status FROM marketplace_agents WHERE id = ?')
      .bind(agentId).first<{ id: string; status: string }>();
    if (!agent) return json({ error: 'Agent not found', code: 'NOT_FOUND' }, { status: 404 });
    if (agent.status !== 'published') return json({ error: 'Agent is not published', code: 'UNAVAILABLE' }, { status: 422 });

    const installation = await installAgent(c.env.DB, tenantId, agentId, body.config);
    return json({ installation }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to install agent', details: String(err) }, { status: 500 });
  }
});

/**
 * DELETE /install/:agentId — uninstall agent for authenticated tenant
 */
agentMarketplace.delete('/install/:agentId', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const agentId = c.req.param('agentId');

  try {
    const result = await uninstallAgent(c.env.DB, tenantId, agentId);
    if (!result.removed) return json({ error: 'Installation not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch (err) {
    return json({ error: 'Failed to uninstall agent', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /installed — list agents installed by authenticated tenant
 */
agentMarketplace.get('/installed', auth(), async (c) => {
  const { tenantId } = getTenant(c);

  try {
    const installations = await listInstalledAgents(c.env.DB, tenantId);
    return json({ installations, total: installations.length });
  } catch (err) {
    return json({ error: 'Failed to list installations', details: String(err) }, { status: 500 });
  }
});

/**
 * POST /publish — create a new agent listing (status: draft)
 * Body: { name, slug, description?, category?, pricing_type?, price_credits?, version?, config_schema?, system_prompt?, model_preference? }
 */
agentMarketplace.post('/publish', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;

  const name = String(body.name ?? '').trim();
  const slug = String(body.slug ?? '').trim();
  if (!name || !slug) {
    return json({ error: 'name and slug are required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  if (!/^[a-z0-9-]+$/.test(slug)) {
    return json({ error: 'slug must be lowercase alphanumeric with hyphens', code: 'INVALID_INPUT' }, { status: 400 });
  }

  try {
    const agent = await publishAgent(c.env.DB, tenantId, {
      name,
      slug,
      description: body.description as string | undefined,
      category: body.category as string | undefined,
      pricing_type: body.pricing_type as string | undefined,
      price_credits: body.price_credits as number | undefined,
      version: body.version as string | undefined,
      config_schema: body.config_schema as string | undefined,
      system_prompt: body.system_prompt as string | undefined,
      model_preference: body.model_preference as string | undefined,
    });
    return json({ agent }, { status: 201 });
  } catch (err) {
    const msg = String(err);
    if (msg.includes('UNIQUE')) return json({ error: 'Slug already taken', code: 'CONFLICT' }, { status: 409 });
    return json({ error: 'Failed to publish agent', details: msg }, { status: 500 });
  }
});

/**
 * POST /agent/:agentId/review — submit or update review for an agent
 * Body: { rating: 1-5, review?: string }
 */
agentMarketplace.post('/agent/:agentId/review', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const agentId = c.req.param('agentId');
  const body = await c.req.json().catch(() => ({})) as { rating?: number; review?: string };

  const rating = Number(body.rating);
  if (!rating || rating < 1 || rating > 5 || !Number.isInteger(rating)) {
    return json({ error: 'rating must be an integer between 1 and 5', code: 'INVALID_INPUT' }, { status: 400 });
  }

  try {
    const agent = await c.env.DB.prepare('SELECT id FROM marketplace_agents WHERE id = ?')
      .bind(agentId).first<{ id: string }>();
    if (!agent) return json({ error: 'Agent not found', code: 'NOT_FOUND' }, { status: 404 });

    const result = await reviewAgent(c.env.DB, tenantId, agentId, rating, body.review);
    return json({ review: result });
  } catch (err) {
    return json({ error: 'Failed to submit review', details: String(err) }, { status: 500 });
  }
});

/**
 * GET /publisher/stats — stats for all agents published by authenticated tenant
 */
agentMarketplace.get('/publisher/stats', auth(), async (c) => {
  const { tenantId } = getTenant(c);

  try {
    const stats = await getPublisherStats(c.env.DB, tenantId);
    return json(stats);
  } catch (err) {
    return json({ error: 'Failed to fetch publisher stats', details: String(err) }, { status: 500 });
  }
});

// ── Admin route ────────────────────────────────────────────────────────────────

/**
 * GET /admin/stats — marketplace-wide overview (X-Admin-Key required)
 */
agentMarketplace.get('/admin/stats', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Forbidden' }, { status: 403 });

  try {
    const stats = await getMarketplaceStats(c.env.DB);
    return json(stats);
  } catch (err) {
    return json({ error: 'Failed to fetch marketplace stats', details: String(err) }, { status: 500 });
  }
});
