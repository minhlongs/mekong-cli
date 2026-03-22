/**
 * AI Model Registry routes — browse models/providers, usage analytics, admin management
 * Public: GET /models, GET /models/:id, GET /providers
 * Auth:   GET /usage, GET /costs
 * Admin:  POST /admin/providers, POST /admin/models, GET /admin/top-models,
 *         POST /admin/seed, POST /admin/usage
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  registerProvider, listProviders,
  registerModel, listModels, getModel,
  trackUsage, getTenantModelUsage, getModelCostBreakdown,
  getTopModels, seedDefaultModels,
} from '../services/ai-model-registry-service';

export const aiModelRegistry = new Hono<{ Bindings: Env }>();

function requireAdminKey(c: { req: { header: (k: string) => string | undefined }; env: Env }): boolean {
  const key = c.req.header('X-Admin-Key');
  return !!(c.env.ADMIN_API_KEY && key === c.env.ADMIN_API_KEY);
}

// ── Public ─────────────────────────────────────────────────────────────────────

/** GET /models — list active models; query: category, provider */
aiModelRegistry.get('/models', async (c) => {
  try {
    const models = await listModels(c.env.DB, c.req.query('category'), c.req.query('provider'));
    return json({ models, total: models.length });
  } catch (err) {
    return json({ error: 'Failed to list models', details: String(err) }, { status: 500 });
  }
});

/** GET /models/:id — model detail */
aiModelRegistry.get('/models/:id', async (c) => {
  try {
    const model = await getModel(c.env.DB, c.req.param('id'));
    if (!model) return json({ error: 'Model not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ model });
  } catch (err) {
    return json({ error: 'Failed to fetch model', details: String(err) }, { status: 500 });
  }
});

/** GET /providers — list active providers */
aiModelRegistry.get('/providers', async (c) => {
  try {
    const providers = await listProviders(c.env.DB);
    return json({ providers, total: providers.length });
  } catch (err) {
    return json({ error: 'Failed to list providers', details: String(err) }, { status: 500 });
  }
});

// ── Authenticated ──────────────────────────────────────────────────────────────

/** GET /usage — tenant model usage summary; query: days (default 30, max 365) */
aiModelRegistry.get('/usage', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const days = Math.min(Number(c.req.query('days') ?? 30), 365);
  try {
    const usage = await getTenantModelUsage(c.env.DB, tenantId, days);
    return json({ usage, days, total_models: usage.length });
  } catch (err) {
    return json({ error: 'Failed to fetch usage', details: String(err) }, { status: 500 });
  }
});

/** GET /costs — tenant cost breakdown by model (all time) */
aiModelRegistry.get('/costs', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const breakdown = await getModelCostBreakdown(c.env.DB, tenantId);
    const total = Math.round(breakdown.reduce((s, r) => s + r.cost_usd, 0) * 1000000) / 1000000;
    return json({ breakdown, total_cost_usd: total });
  } catch (err) {
    return json({ error: 'Failed to fetch cost breakdown', details: String(err) }, { status: 500 });
  }
});

// ── Admin ──────────────────────────────────────────────────────────────────────

/** POST /admin/providers — register provider; body: { name, base_url, auth_type? } */
aiModelRegistry.post('/admin/providers', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Forbidden' }, { status: 403 });
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const name = String(body.name ?? '').trim();
  const baseUrl = String(body.base_url ?? '').trim();
  if (!name || !baseUrl) return json({ error: 'name and base_url are required', code: 'INVALID_INPUT' }, { status: 400 });
  try {
    const provider = await registerProvider(c.env.DB, name, baseUrl, String(body.auth_type ?? 'bearer'));
    return json({ provider }, { status: 201 });
  } catch (err) {
    const msg = String(err);
    if (msg.includes('UNIQUE')) return json({ error: 'Provider name already exists', code: 'CONFLICT' }, { status: 409 });
    return json({ error: 'Failed to register provider', details: msg }, { status: 500 });
  }
});

/**
 * POST /admin/models — register model under provider
 * body: { provider_id, model_id, display_name, category?, cost_per_1k_input?, cost_per_1k_output?,
 *         context_window?, max_output_tokens?, supports_tools?, supports_vision? }
 */
aiModelRegistry.post('/admin/models', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Forbidden' }, { status: 403 });
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const providerId = String(body.provider_id ?? '').trim();
  const modelId = String(body.model_id ?? '').trim();
  const displayName = String(body.display_name ?? '').trim();
  if (!providerId || !modelId || !displayName) {
    return json({ error: 'provider_id, model_id, and display_name are required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  const provider = await c.env.DB.prepare('SELECT id FROM ai_model_providers WHERE id = ?')
    .bind(providerId).first<{ id: string }>();
  if (!provider) return json({ error: 'Provider not found', code: 'NOT_FOUND' }, { status: 404 });
  try {
    const model = await registerModel(
      c.env.DB, providerId, modelId, displayName,
      String(body.category ?? 'general'),
      { input: Number(body.cost_per_1k_input ?? 0), output: Number(body.cost_per_1k_output ?? 0) },
      { contextWindow: Number(body.context_window ?? 4096), maxOutput: Number(body.max_output_tokens ?? 4096),
        tools: Boolean(body.supports_tools), vision: Boolean(body.supports_vision) },
    );
    return json({ model }, { status: 201 });
  } catch (err) {
    const msg = String(err);
    if (msg.includes('UNIQUE')) return json({ error: 'Model already registered for this provider', code: 'CONFLICT' }, { status: 409 });
    return json({ error: 'Failed to register model', details: msg }, { status: 500 });
  }
});

/** GET /admin/top-models — most used models platform-wide; query: limit (max 50) */
aiModelRegistry.get('/admin/top-models', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Forbidden' }, { status: 403 });
  const limit = Math.min(Number(c.req.query('limit') ?? 10), 50);
  try {
    const models = await getTopModels(c.env.DB, limit);
    return json({ models, total: models.length });
  } catch (err) {
    return json({ error: 'Failed to fetch top models', details: String(err) }, { status: 500 });
  }
});

/** POST /admin/seed — seed default providers and models (idempotent) */
aiModelRegistry.post('/admin/seed', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Forbidden' }, { status: 403 });
  try {
    const result = await seedDefaultModels(c.env.DB);
    return json({ seeded: result, message: 'Default models seeded successfully' });
  } catch (err) {
    return json({ error: 'Failed to seed models', details: String(err) }, { status: 500 });
  }
});

/** POST /admin/usage — record token usage (internal/service); body: { tenant_id, model_id, input_tokens, output_tokens, cost_usd, mission_id? } */
aiModelRegistry.post('/admin/usage', async (c) => {
  if (!requireAdminKey(c)) return json({ error: 'Forbidden' }, { status: 403 });
  const body = await c.req.json().catch(() => ({})) as Record<string, unknown>;
  const tenantId = String(body.tenant_id ?? '').trim();
  const modelId = String(body.model_id ?? '').trim();
  if (!tenantId || !modelId) return json({ error: 'tenant_id and model_id are required', code: 'INVALID_INPUT' }, { status: 400 });
  try {
    const record = await trackUsage(
      c.env.DB, tenantId, modelId,
      Number(body.input_tokens ?? 0), Number(body.output_tokens ?? 0),
      Number(body.cost_usd ?? 0), body.mission_id as string | undefined,
    );
    return json({ record }, { status: 201 });
  } catch (err) {
    return json({ error: 'Failed to track usage', details: String(err) }, { status: 500 });
  }
});
