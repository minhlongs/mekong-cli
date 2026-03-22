/**
 * AI Model Registry Service — providers, model definitions, usage tracking, cost analytics
 */

import type { D1Database } from '@cloudflare/workers-types';

export interface ModelProvider {
  id: string; name: string; base_url: string;
  auth_type: string; is_active: number; created_at: string;
}

export interface ModelDefinition {
  id: string; provider_id: string; model_id: string; display_name: string;
  category: string; context_window: number; cost_per_1k_input: number;
  cost_per_1k_output: number; max_output_tokens: number;
  supports_tools: number; supports_vision: number; is_active: number; created_at: string;
}

export interface UsageRecord {
  id: string; tenant_id: string; model_id: string;
  input_tokens: number; output_tokens: number;
  cost_usd: number; mission_id: string | null; created_at: string;
}

// ── Providers ──────────────────────────────────────────────────────────────────

export async function registerProvider(
  db: D1Database, name: string, baseUrl: string, authType = 'bearer'
): Promise<ModelProvider> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO ai_model_providers (id, name, base_url, auth_type) VALUES (?, ?, ?, ?)`
  ).bind(id, name, baseUrl, authType).run();
  return db.prepare('SELECT * FROM ai_model_providers WHERE id = ?')
    .bind(id).first<ModelProvider>() as Promise<ModelProvider>;
}

export async function listProviders(db: D1Database): Promise<ModelProvider[]> {
  const r = await db.prepare(
    `SELECT * FROM ai_model_providers WHERE is_active = 1 ORDER BY name ASC`
  ).all<ModelProvider>();
  return r.results ?? [];
}

// ── Models ─────────────────────────────────────────────────────────────────────

export async function registerModel(
  db: D1Database, providerId: string, modelId: string, displayName: string,
  category = 'general',
  costs: { input?: number; output?: number } = {},
  caps: { contextWindow?: number; maxOutput?: number; tools?: boolean; vision?: boolean } = {}
): Promise<ModelDefinition> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO ai_model_definitions
      (id, provider_id, model_id, display_name, category, context_window,
       cost_per_1k_input, cost_per_1k_output, max_output_tokens, supports_tools, supports_vision)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
  ).bind(
    id, providerId, modelId, displayName, category,
    caps.contextWindow ?? 4096, costs.input ?? 0, costs.output ?? 0,
    caps.maxOutput ?? 4096, caps.tools ? 1 : 0, caps.vision ? 1 : 0,
  ).run();
  return db.prepare('SELECT * FROM ai_model_definitions WHERE id = ?')
    .bind(id).first<ModelDefinition>() as Promise<ModelDefinition>;
}

export async function listModels(
  db: D1Database, category?: string, providerId?: string
): Promise<ModelDefinition[]> {
  let sql = `SELECT * FROM ai_model_definitions WHERE is_active = 1`;
  const binds: unknown[] = [];
  if (category) { sql += ` AND category = ?`; binds.push(category); }
  if (providerId) { sql += ` AND provider_id = ?`; binds.push(providerId); }
  sql += ` ORDER BY display_name ASC`;
  const r = await db.prepare(sql).bind(...binds).all<ModelDefinition>();
  return r.results ?? [];
}

export async function getModel(db: D1Database, id: string): Promise<ModelDefinition | null> {
  return db.prepare('SELECT * FROM ai_model_definitions WHERE id = ?').bind(id).first<ModelDefinition>();
}

// ── Usage Tracking ─────────────────────────────────────────────────────────────

export async function trackUsage(
  db: D1Database, tenantId: string, modelId: string,
  inputTokens: number, outputTokens: number, costUsd: number, missionId?: string
): Promise<UsageRecord> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO model_usage_tracking
      (id, tenant_id, model_id, input_tokens, output_tokens, cost_usd, mission_id)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, tenantId, modelId, inputTokens, outputTokens, costUsd, missionId ?? null).run();
  return db.prepare('SELECT * FROM model_usage_tracking WHERE id = ?')
    .bind(id).first<UsageRecord>() as Promise<UsageRecord>;
}

export async function getTenantModelUsage(
  db: D1Database, tenantId: string, days = 30
): Promise<{ model_id: string; total_input: number; total_output: number; total_cost: number; calls: number }[]> {
  const r = await db.prepare(
    `SELECT model_id, SUM(input_tokens) AS total_input, SUM(output_tokens) AS total_output,
            ROUND(SUM(cost_usd), 6) AS total_cost, COUNT(*) AS calls
     FROM model_usage_tracking
     WHERE tenant_id = ? AND created_at >= datetime('now', ? || ' days')
     GROUP BY model_id ORDER BY total_cost DESC`
  ).bind(tenantId, `-${days}`).all<{ model_id: string; total_input: number; total_output: number; total_cost: number; calls: number }>();
  return r.results ?? [];
}

export async function getModelCostBreakdown(
  db: D1Database, tenantId: string
): Promise<{ model_id: string; cost_usd: number; pct: number }[]> {
  const r = await db.prepare(
    `SELECT model_id, ROUND(SUM(cost_usd), 6) AS cost_usd
     FROM model_usage_tracking WHERE tenant_id = ?
     GROUP BY model_id ORDER BY cost_usd DESC`
  ).bind(tenantId).all<{ model_id: string; cost_usd: number }>();
  const rows = r.results ?? [];
  const total = rows.reduce((s, x) => s + x.cost_usd, 0);
  return rows.map(x => ({ ...x, pct: total > 0 ? Math.round((x.cost_usd / total) * 10000) / 100 : 0 }));
}

export async function getTopModels(
  db: D1Database, limit = 10
): Promise<{ model_id: string; calls: number; total_cost: number }[]> {
  const r = await db.prepare(
    `SELECT model_id, COUNT(*) AS calls, ROUND(SUM(cost_usd), 6) AS total_cost
     FROM model_usage_tracking GROUP BY model_id ORDER BY calls DESC LIMIT ?`
  ).bind(limit).all<{ model_id: string; calls: number; total_cost: number }>();
  return r.results ?? [];
}

// ── Seed Defaults ──────────────────────────────────────────────────────────────

type SeedModel = { modelId: string; display: string; cat: string; in: number; out: number; ctx: number; maxOut: number; tools: boolean; vision: boolean };
type SeedEntry = { name: string; url: string; auth: string; models: SeedModel[] };

const SEED_DATA: SeedEntry[] = [
  { name: 'Anthropic', url: 'https://api.anthropic.com/v1', auth: 'bearer', models: [
    { modelId: 'claude-opus-4-6', display: 'Claude Opus 4.6', cat: 'analysis', in: 15, out: 75, ctx: 200000, maxOut: 8096, tools: true, vision: true },
    { modelId: 'claude-sonnet-4-6', display: 'Claude Sonnet 4.6', cat: 'general', in: 3, out: 15, ctx: 200000, maxOut: 8096, tools: true, vision: true },
    { modelId: 'claude-haiku-3-5', display: 'Claude Haiku 3.5', cat: 'fast', in: 0.8, out: 4, ctx: 200000, maxOut: 8096, tools: true, vision: true },
  ]},
  { name: 'OpenAI', url: 'https://api.openai.com/v1', auth: 'bearer', models: [
    { modelId: 'gpt-4o', display: 'GPT-4o', cat: 'general', in: 2.5, out: 10, ctx: 128000, maxOut: 16384, tools: true, vision: true },
    { modelId: 'gpt-4o-mini', display: 'GPT-4o Mini', cat: 'fast', in: 0.15, out: 0.6, ctx: 128000, maxOut: 16384, tools: true, vision: true },
  ]},
  { name: 'DashScope (Qwen)', url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', auth: 'bearer', models: [
    { modelId: 'qwen3.5-plus', display: 'Qwen 3.5 Plus', cat: 'coding', in: 0.5, out: 1.5, ctx: 131072, maxOut: 8192, tools: true, vision: false },
    { modelId: 'qwen-long', display: 'Qwen Long', cat: 'analysis', in: 0.05, out: 0.2, ctx: 10000000, maxOut: 6000, tools: false, vision: false },
  ]},
  { name: 'Google', url: 'https://generativelanguage.googleapis.com/v1beta', auth: 'api_key', models: [
    { modelId: 'gemini-2.0-flash', display: 'Gemini 2.0 Flash', cat: 'fast', in: 0.1, out: 0.4, ctx: 1048576, maxOut: 8192, tools: true, vision: true },
    { modelId: 'gemini-2.5-pro', display: 'Gemini 2.5 Pro', cat: 'analysis', in: 1.25, out: 10, ctx: 1048576, maxOut: 65536, tools: true, vision: true },
  ]},
];

/** Seed common providers and models — idempotent, skips existing entries */
export async function seedDefaultModels(db: D1Database): Promise<{ providers: number; models: number }> {
  let providerCount = 0; let modelCount = 0;
  for (const seed of SEED_DATA) {
    let row = await db.prepare('SELECT id FROM ai_model_providers WHERE name = ?')
      .bind(seed.name).first<{ id: string }>();
    if (!row) { const p = await registerProvider(db, seed.name, seed.url, seed.auth); row = { id: p.id }; providerCount++; }
    for (const m of seed.models) {
      const exists = await db.prepare('SELECT id FROM ai_model_definitions WHERE provider_id = ? AND model_id = ?')
        .bind(row.id, m.modelId).first<{ id: string }>();
      if (exists) continue;
      await registerModel(db, row.id, m.modelId, m.display, m.cat, { input: m.in, output: m.out }, { contextWindow: m.ctx, maxOutput: m.maxOut, tools: m.tools, vision: m.vision });
      modelCount++;
    }
  }
  return { providers: providerCount, models: modelCount };
}
