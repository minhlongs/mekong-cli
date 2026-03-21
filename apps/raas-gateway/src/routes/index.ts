/**
 * Route registry — combines all route handlers
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { health } from './health';
import { api } from './api';
import { credits } from './credits';
import { billing } from './billing';
import { tenants } from './tenants';
import { telegram } from './telegram';
import { notFound } from '../utils/response';

export function createRoutes() {
  const routes = new Hono<{ Bindings: Env }>();

  // Mount routes (tenants before api — signup is public, must bypass api auth)
  routes.route('/health', health);
  routes.route('/v1/tenants', tenants);
  routes.route('/v1', api);
  routes.route('/credits', credits);
  routes.route('/billing', billing);
  routes.route('/webhook/telegram', telegram);

  // Public stats — cached in KV for 5 min
  routes.get('/stats', async (c) => {
    const cached = await c.env.RATE_LIMIT_KV.get('public:stats', 'json') as any;
    if (cached) return c.json(cached);

    const [tenants, missions, credits] = await Promise.all([
      c.env.DB.prepare('SELECT COUNT(*) as c FROM tenants WHERE active=1').first<{c:number}>(),
      c.env.DB.prepare("SELECT COUNT(*) as c FROM missions WHERE status='completed'").first<{c:number}>(),
      c.env.DB.prepare('SELECT COALESCE(SUM(total_spent),0) as c FROM tenants').first<{c:number}>(),
    ]);

    const stats = {
      tenants: tenants?.c ?? 0,
      missionsCompleted: missions?.c ?? 0,
      creditsProcessed: credits?.c ?? 0,
      updatedAt: new Date().toISOString(),
    };

    await c.env.RATE_LIMIT_KV.put('public:stats', JSON.stringify(stats), { expirationTtl: 300 });
    return c.json(stats);
  });

  // OpenAPI spec
  routes.get('/openapi.json', (c) => {
    return c.json({
      openapi: '3.0.3',
      info: { title: 'Mekong RaaS Gateway', version: '1.0.0', description: 'AI-Operated Business Platform API' },
      servers: [{ url: 'https://raas-gateway.agencyos-openclaw.workers.dev' }],
      paths: {
        '/v1/tenants/signup': { post: { summary: 'Create account', tags: ['Tenants'], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { name: { type: 'string' }, email: { type: 'string' } }, required: ['name','email'] } } } }, responses: { '201': { description: 'Account created with JWT + 10 credits' } } } },
        '/v1/tenants/profile': { get: { summary: 'Get profile', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/api-keys': { post: { summary: 'Generate API key', tags: ['Tenants'], security: [{ bearer: [] }] }, get: { summary: 'List API keys', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/missions': { post: { summary: 'Submit mission (1-5 MCU)', tags: ['Missions'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { goal: { type: 'string' }, complexity: { type: 'string', enum: ['simple','standard','complex'] }, project: { type: 'string' }, callback_url: { type: 'string' } }, required: ['goal'] } } } } }, get: { summary: 'List missions', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}': { get: { summary: 'Get mission + result', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}/cancel': { post: { summary: 'Cancel + refund', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/analytics': { get: { summary: 'Usage dashboard', tags: ['Analytics'], security: [{ bearer: [] }] } },
        '/credits': { get: { summary: 'Credit balance', tags: ['Credits'], security: [{ bearer: [] }] } },
        '/credits/check': { post: { summary: 'Pre-check cost', tags: ['Credits'], security: [{ bearer: [] }] } },
        '/billing/pricing': { get: { summary: 'Pricing tiers', tags: ['Billing'] } },
        '/billing/webhook': { post: { summary: 'Polar webhook', tags: ['Billing'] } },
        '/health': { get: { summary: 'Health check', tags: ['System'] } },
        '/stats': { get: { summary: 'Public stats', tags: ['System'] } },
      },
      components: { securitySchemes: { bearer: { type: 'http', scheme: 'bearer' }, apiKey: { type: 'apiKey', in: 'header', name: 'X-API-Key' } } },
    });
  });

  // Catch-all 404
  routes.notFound((c) => {
    return notFound(`Route ${c.req.path} not found`);
  });

  return routes;
}
