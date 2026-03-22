/**
 * Agent Marketplace Service — publish, browse, install, review AI agents
 * Stats functions live in agent-marketplace-stats-service.ts
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface MarketplaceAgent {
  id: string; publisher_id: string; name: string; slug: string;
  description: string | null; category: string; pricing_type: string;
  price_credits: number; version: string; config_schema: string | null;
  system_prompt: string | null; model_preference: string | null;
  install_count: number; rating_avg: number; rating_count: number;
  status: string; created_at: string; updated_at: string | null;
}

export interface AgentInstallation {
  id: string; tenant_id: string; agent_id: string; config: string | null;
  installed_at: string; last_used_at: string | null; usage_count: number;
}

export interface AgentReview {
  id: string; agent_id: string; tenant_id: string;
  rating: number; review: string | null; created_at: string;
}

// ── Publish ────────────────────────────────────────────────────────────────────

/** Create a new agent listing (status: draft) */
export async function publishAgent(
  db: D1Database,
  publisherId: string,
  data: {
    name: string; slug: string; description?: string; category?: string;
    pricing_type?: string; price_credits?: number; version?: string;
    config_schema?: string; system_prompt?: string; model_preference?: string;
  }
): Promise<MarketplaceAgent> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO marketplace_agents
      (id, publisher_id, name, slug, description, category, pricing_type,
       price_credits, version, config_schema, system_prompt, model_preference)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id, publisherId, data.name, data.slug,
    data.description ?? null, data.category ?? 'general',
    data.pricing_type ?? 'free', data.price_credits ?? 0,
    data.version ?? '1.0.0', data.config_schema ?? null,
    data.system_prompt ?? null, data.model_preference ?? null,
  ).run();
  return db.prepare('SELECT * FROM marketplace_agents WHERE id = ?')
    .bind(id).first<MarketplaceAgent>() as Promise<MarketplaceAgent>;
}

// ── Browse ─────────────────────────────────────────────────────────────────────

/** List published agents with optional category/search filters */
export async function listPublishedAgents(
  db: D1Database, category?: string, search?: string, limit = 20, offset = 0
): Promise<MarketplaceAgent[]> {
  let sql = `SELECT * FROM marketplace_agents WHERE status = 'published'`;
  const binds: unknown[] = [];
  if (category) { sql += ` AND category = ?`; binds.push(category); }
  if (search) { sql += ` AND (name LIKE ? OR description LIKE ?)`; binds.push(`%${search}%`, `%${search}%`); }
  sql += ` ORDER BY install_count DESC, rating_avg DESC LIMIT ? OFFSET ?`;
  binds.push(Math.min(limit, 100), offset);
  const result = await db.prepare(sql).bind(...binds).all<MarketplaceAgent>();
  return result.results ?? [];
}

/** Top rated + most installed agents for featured section */
export async function getFeaturedAgents(db: D1Database): Promise<MarketplaceAgent[]> {
  const result = await db.prepare(
    `SELECT * FROM marketplace_agents WHERE status = 'published'
     ORDER BY rating_avg DESC, install_count DESC LIMIT 10`
  ).all<MarketplaceAgent>();
  return result.results ?? [];
}

/** Get single agent by slug */
export async function getAgentBySlug(db: D1Database, slug: string): Promise<MarketplaceAgent | null> {
  return db.prepare('SELECT * FROM marketplace_agents WHERE slug = ?').bind(slug).first<MarketplaceAgent>();
}

// ── Install / Uninstall ────────────────────────────────────────────────────────

/** Install agent for tenant — idempotent on (tenant_id, agent_id) */
export async function installAgent(
  db: D1Database, tenantId: string, agentId: string, config?: string
): Promise<AgentInstallation> {
  const existing = await db.prepare(
    'SELECT * FROM agent_installations WHERE tenant_id = ? AND agent_id = ?'
  ).bind(tenantId, agentId).first<AgentInstallation>();
  if (existing) return existing;

  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO agent_installations (id, tenant_id, agent_id, config) VALUES (?, ?, ?, ?)`
  ).bind(id, tenantId, agentId, config ?? null).run();
  await db.prepare(
    `UPDATE marketplace_agents SET install_count = install_count + 1, updated_at = datetime('now') WHERE id = ?`
  ).bind(agentId).run();
  return db.prepare('SELECT * FROM agent_installations WHERE id = ?')
    .bind(id).first<AgentInstallation>() as Promise<AgentInstallation>;
}

/** Remove agent installation for tenant */
export async function uninstallAgent(
  db: D1Database, tenantId: string, agentId: string
): Promise<{ removed: boolean }> {
  const result = await db.prepare(
    'DELETE FROM agent_installations WHERE tenant_id = ? AND agent_id = ?'
  ).bind(tenantId, agentId).run();
  if (result.meta?.changes) {
    await db.prepare(
      `UPDATE marketplace_agents SET install_count = MAX(0, install_count - 1), updated_at = datetime('now') WHERE id = ?`
    ).bind(agentId).run();
  }
  return { removed: !!(result.meta?.changes) };
}

/** List installed agents for tenant — joined with agent details */
export async function listInstalledAgents(
  db: D1Database, tenantId: string
): Promise<(AgentInstallation & { agent: MarketplaceAgent | null })[]> {
  const result = await db.prepare(
    `SELECT i.*, a.name, a.slug, a.description, a.category, a.pricing_type,
            a.price_credits, a.version, a.model_preference, a.rating_avg, a.rating_count, a.status
     FROM agent_installations i
     LEFT JOIN marketplace_agents a ON a.id = i.agent_id
     WHERE i.tenant_id = ? ORDER BY i.installed_at DESC`
  ).bind(tenantId).all<AgentInstallation & MarketplaceAgent>();

  return (result.results ?? []).map(row => {
    const { id, tenant_id, agent_id, config, installed_at, last_used_at, usage_count, ...agentFields } = row;
    return { id, tenant_id, agent_id, config, installed_at, last_used_at, usage_count, agent: agentFields as unknown as MarketplaceAgent };
  });
}

// ── Reviews ────────────────────────────────────────────────────────────────────

/** Submit or update a review — one review per (agent, tenant) */
export async function reviewAgent(
  db: D1Database, tenantId: string, agentId: string, rating: number, review?: string
): Promise<AgentReview> {
  const existing = await db.prepare(
    'SELECT id FROM agent_reviews WHERE agent_id = ? AND tenant_id = ?'
  ).bind(agentId, tenantId).first<{ id: string }>();

  if (existing) {
    await db.prepare(`UPDATE agent_reviews SET rating = ?, review = ? WHERE id = ?`)
      .bind(rating, review ?? null, existing.id).run();
  } else {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO agent_reviews (id, agent_id, tenant_id, rating, review) VALUES (?, ?, ?, ?, ?)`
    ).bind(id, agentId, tenantId, rating, review ?? null).run();
  }

  // Recalculate rating_avg + rating_count on the agent row
  await db.prepare(
    `UPDATE marketplace_agents SET
       rating_avg = (SELECT AVG(CAST(rating AS REAL)) FROM agent_reviews WHERE agent_id = ?),
       rating_count = (SELECT COUNT(*) FROM agent_reviews WHERE agent_id = ?),
       updated_at = datetime('now')
     WHERE id = ?`
  ).bind(agentId, agentId, agentId).run();

  return db.prepare('SELECT * FROM agent_reviews WHERE agent_id = ? AND tenant_id = ?')
    .bind(agentId, tenantId).first<AgentReview>() as Promise<AgentReview>;
}

/** List all reviews for an agent, newest first */
export async function getAgentReviews(db: D1Database, agentId: string): Promise<AgentReview[]> {
  const result = await db.prepare(
    'SELECT * FROM agent_reviews WHERE agent_id = ? ORDER BY created_at DESC'
  ).bind(agentId).all<AgentReview>();
  return result.results ?? [];
}
