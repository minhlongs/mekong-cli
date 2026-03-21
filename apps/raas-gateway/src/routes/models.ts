/**
 * Model catalog routes
 * GET  /v1/models           — list available AI models (filter by provider, capability)
 * GET  /v1/models/:id       — get model details
 * POST /v1/models/select    — auto-select optimal model for requirements
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth } from '../middleware/auth';
import { OpenClawModelRegistry } from '../services/openclaw-model-registry';

export const models = new Hono<{ Bindings: Env }>();

const registry = new OpenClawModelRegistry();

/** GET / — list all available models, supports ?provider= and ?capability= filters */
models.get('/', auth(), (c) => {
  const provider = c.req.query('provider');
  const capability = c.req.query('capability');
  const result = registry.listModels({ provider, capability });
  return c.json({ success: true, data: { models: result, count: result.length } });
});

/** GET /:id — get details for a specific model */
models.get('/:id', auth(), (c) => {
  const model = registry.getModel(c.req.param('id'));
  if (!model) {
    return c.json({ success: false, error: 'Model not found' }, 404);
  }
  return c.json({ success: true, data: model });
});

/** POST /select — auto-select optimal (cheapest) model matching requirements */
models.post('/select', auth(), async (c) => {
  const body = await c.req.json().catch(() => ({})) as {
    capability?: string;
    max_cost_per_m_token?: number;
    min_context_window?: number;
  };

  const model = registry.selectOptimal({
    capability: body.capability,
    maxCost: body.max_cost_per_m_token,
    minContext: body.min_context_window,
  });

  if (!model) {
    return c.json({ success: false, error: 'No model matches requirements' }, 404);
  }

  return c.json({ success: true, data: { selected: model, reason: 'lowest_cost_matching' } });
});
