/**
 * Agent Marketplace Stats Service — publisher dashboard + admin overview
 * Kept separate from core CRUD to stay under 200-line file limit
 */

import type { D1Database } from '@cloudflare/workers-types';
import type { MarketplaceAgent } from './agent-marketplace-service';

// ── Publisher Stats ────────────────────────────────────────────────────────────

/** Publisher dashboard — own agents with aggregate install + rating stats */
export async function getPublisherStats(
  db: D1Database,
  publisherId: string
): Promise<{ agents: MarketplaceAgent[]; total_installs: number; avg_rating: number }> {
  const result = await db.prepare(
    'SELECT * FROM marketplace_agents WHERE publisher_id = ? ORDER BY created_at DESC'
  ).bind(publisherId).all<MarketplaceAgent>();

  const agents = result.results ?? [];
  const total_installs = agents.reduce((s, a) => s + (a.install_count ?? 0), 0);
  const rated = agents.filter(a => a.rating_count > 0);
  const avg_rating = rated.length
    ? rated.reduce((s, a) => s + a.rating_avg, 0) / rated.length
    : 0;

  return { agents, total_installs, avg_rating: Math.round(avg_rating * 100) / 100 };
}

// ── Admin Stats ────────────────────────────────────────────────────────────────

/** Admin overview — marketplace-wide statistics */
export async function getMarketplaceStats(db: D1Database): Promise<{
  total_agents: number;
  published_agents: number;
  total_installations: number;
  total_reviews: number;
  categories: Record<string, number>;
}> {
  const [agentRow, installRow, reviewRow, catRows] = await Promise.all([
    db.prepare(
      `SELECT COUNT(*) as total, SUM(CASE WHEN status='published' THEN 1 ELSE 0 END) as published FROM marketplace_agents`
    ).first<{ total: number; published: number }>(),
    db.prepare(`SELECT COUNT(*) as total FROM agent_installations`).first<{ total: number }>(),
    db.prepare(`SELECT COUNT(*) as total FROM agent_reviews`).first<{ total: number }>(),
    db.prepare(
      `SELECT category, COUNT(*) as cnt FROM marketplace_agents WHERE status='published' GROUP BY category`
    ).all<{ category: string; cnt: number }>(),
  ]);

  const categories: Record<string, number> = {};
  for (const row of catRows.results ?? []) categories[row.category] = row.cnt;

  return {
    total_agents: agentRow?.total ?? 0,
    published_agents: agentRow?.published ?? 0,
    total_installations: installRow?.total ?? 0,
    total_reviews: reviewRow?.total ?? 0,
    categories,
  };
}
