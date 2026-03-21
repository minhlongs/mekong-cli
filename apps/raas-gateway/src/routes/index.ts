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
import { onboarding } from './onboarding';
import { telegram } from './telegram';
import { alerts } from './alerts';
import { marketplace } from './marketplace';
import { stripe } from './stripe';
import { checkout } from './checkout';
import { admin } from './admin';
import { adminAnalytics } from './admin-analytics';
import { dunning } from './dunning';
import { licenses } from './licenses';
import { webhooks } from './webhooks';
import { status } from './status';
import { dashboard } from './dashboard';
import { playground } from './playground';
import { usageExport } from './usage-export';
import { referrals } from './referrals';
import { metrics } from './metrics';
import { apiDocs } from './api-docs';
import { projects } from './projects';
import { team } from './team';
import { webhookManagement } from './webhook-management';
import { audit } from './audit';
import { landing } from './landing';
import { notFound } from '../utils/response';

export function createRoutes() {
  const routes = new Hono<{ Bindings: Env }>();

  // Mount routes — public routes BEFORE /v1 api (which has auth middleware)
  routes.route('/admin', admin);
  routes.route('/admin/analytics', adminAnalytics);
  routes.route('/admin/dunning', dunning);
  routes.route('/admin/webhooks', webhooks);
  routes.route('/health', health);
  routes.route('/status', status);
  routes.route('/marketplace', marketplace);
  routes.route('/v1/tenants', tenants);
  routes.route('/v1/onboarding', onboarding);
  // Licenses: verify + activate are PUBLIC; create + list require auth (per-route)
  routes.route('/v1/licenses', licenses);

  routes.route('/v1', api);
  routes.route('/v1', dashboard);
  routes.route('/v1/usage', usageExport);
  routes.route('/v1/invoices', usageExport);
  routes.route('/', landing);
  routes.route('/', playground);
  routes.route('/v1/alerts', alerts);
  routes.route('/credits', credits);
  routes.route('/billing', billing);
  // Stripe: /billing/stripe/webhook is PUBLIC (no global auth), /billing/stripe/checkout has its own auth()
  routes.route('/billing/stripe', stripe);
  routes.route('/billing/checkout', checkout);
  routes.route('/webhook/telegram', telegram);
  routes.route('/metrics', metrics);
  routes.route('/docs', apiDocs);
  routes.route('/v1/referrals', referrals);
  routes.route('/v1/projects', projects);
  routes.route('/v1/team', team);
  routes.route('/v1/webhooks', webhookManagement);
  routes.route('/v1/audit', audit);

  // Waitlist email capture (public)
  routes.post('/waitlist', async (c) => {
    const body = await c.req.json().catch(() => ({}));
    const email = body.email?.trim()?.toLowerCase();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return c.json({ error: 'Valid email required' }, 400);
    }
    try {
      await c.env.DB.prepare(
        "INSERT OR IGNORE INTO waitlist (id, email, source, created_at) VALUES (?, ?, ?, datetime('now'))"
      ).bind(crypto.randomUUID(), email, body.source || 'landing').run();
      return c.json({ success: true, message: 'You\'re on the list!' });
    } catch {
      return c.json({ success: true, message: 'Already on the list!' });
    }
  });

  // Public mission sharing (no auth)
  routes.get('/share/:id', async (c) => {
    const missionId = c.req.param('id');
    const mission = await c.env.DB.prepare(
      `SELECT goal, complexity, status, result, credits_cost, created_at, completed_at
       FROM missions WHERE id = ? AND is_public = 1`
    ).bind(missionId).first<any>();

    if (!mission) {
      return c.json({ error: 'Mission not found or not public' }, 404);
    }

    // Return as HTML for social sharing
    const html = `<!DOCTYPE html><html><head>
      <title>Mekong Mission Result</title>
      <meta property="og:title" content="AI Mission: ${mission.goal.slice(0, 60)}">
      <meta property="og:description" content="${(mission.result || '').slice(0, 150)}">
      <style>body{font-family:system-ui;background:#0a0a0a;color:#e5e5e5;max-width:700px;margin:2rem auto;padding:1rem}
      h1{color:#22d3ee;font-size:1.2rem}pre{background:#111;padding:1rem;border-radius:8px;white-space:pre-wrap;font-size:0.9rem}
      .meta{color:#888;font-size:0.85rem}a{color:#22d3ee}</style></head><body>
      <h1>${mission.goal}</h1>
      <p class="meta">${mission.complexity} | ${mission.credits_cost} MCU | ${mission.status}</p>
      <pre>${mission.result || 'Processing...'}</pre>
      <p class="meta">Powered by <a href="https://mekong-raas.pages.dev">Mekong CLI</a></p>
      </body></html>`;
    return c.html(html);
  });

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
        '/v1/tenants/api-keys/{id}': { delete: { summary: 'Revoke API key', tags: ['Tenants'], security: [{ bearer: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/missions': { post: { summary: 'Submit mission (1-5 MCU)', tags: ['Missions'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { goal: { type: 'string' }, complexity: { type: 'string', enum: ['simple','standard','complex'] }, project: { type: 'string' }, callback_url: { type: 'string' } }, required: ['goal'] } } } } }, get: { summary: 'List missions', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}': { get: { summary: 'Get mission + result', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}/cancel': { post: { summary: 'Cancel + refund', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/analytics': { get: { summary: 'Usage dashboard', tags: ['Analytics'], security: [{ bearer: [] }] } },
        '/credits': { get: { summary: 'Credit balance', tags: ['Credits'], security: [{ bearer: [] }] } },
        '/credits/check': { post: { summary: 'Pre-check cost', tags: ['Credits'], security: [{ bearer: [] }] } },
        '/billing/pricing': { get: { summary: 'Pricing tiers', tags: ['Billing'] } },
        '/billing/webhook': { post: { summary: 'Polar webhook', tags: ['Billing'] } },
        '/marketplace': { get: { summary: 'Browse public missions', tags: ['Marketplace'], parameters: [{ name: 'q', in: 'query', schema: { type: 'string' } }, { name: 'limit', in: 'query', schema: { type: 'integer' } }] } },
        '/marketplace/featured': { get: { summary: 'Featured missions', tags: ['Marketplace'] } },
        '/marketplace/stats': { get: { summary: 'Marketplace statistics', tags: ['Marketplace'] } },
        '/v1/alerts': { get: { summary: 'List unread alerts', tags: ['Alerts'], security: [{ bearer: [] }] } },
        '/v1/alerts/count': { get: { summary: 'Unread alert count', tags: ['Alerts'], security: [{ bearer: [] }] } },
        '/billing/stripe/packs': { get: { summary: 'List credit packs', tags: ['Billing'] } },
        '/billing/stripe/checkout': { post: { summary: 'Create Stripe checkout', tags: ['Billing'], security: [{ bearer: [] }] } },
        '/billing/stripe/webhook': { post: { summary: 'Stripe webhook', tags: ['Billing'] } },
        '/health': { get: { summary: 'Health check', tags: ['System'] } },
        '/health/deep': { get: { summary: 'Deep health check', tags: ['System'] } },
        '/stats': { get: { summary: 'Public stats', tags: ['System'] } },
        '/marketplace/leaderboard': { get: { summary: 'Referral leaderboard', tags: ['Marketplace'] } },
        '/marketplace/{id}/reviews': {
          get: { summary: 'Mission reviews', tags: ['Marketplace'], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }] },
          post: { summary: 'Submit review', tags: ['Marketplace'], security: [{ bearer: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { rating: { type: 'integer' }, comment: { type: 'string' } }, required: ['rating'] } } } } },
        },
        '/v1/missions/templates': { get: { summary: 'Mission templates (DB-backed)', tags: ['Missions'], parameters: [{ name: 'category', in: 'query', schema: { type: 'string' } }] } },
        '/v1/tenants/settings': { put: { summary: 'Update tenant settings', tags: ['Tenants'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { webhook_url: { type: 'string' }, notify_email: { type: 'boolean' }, notify_telegram: { type: 'boolean' } } } } } } } },
        '/v1/tenants/trial-extend': { post: { summary: 'Trial extension', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/usage': { get: { summary: 'Monthly usage', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/v1/tenants/invoices': { get: { summary: 'Invoice history', tags: ['Tenants'], security: [{ bearer: [] }], parameters: [{ name: 'limit', in: 'query', schema: { type: 'integer' } }, { name: 'offset', in: 'query', schema: { type: 'integer' } }, { name: 'type', in: 'query', schema: { type: 'string' } }] } },
        '/v1/credits/redeem': { post: { summary: 'Redeem coupon', tags: ['Credits'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { code: { type: 'string' } }, required: ['code'] } } } } } },
        '/v1/credits/feedback': { post: { summary: 'Submit feedback', tags: ['Credits'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { type: { type: 'string' }, message: { type: 'string' } }, required: ['type', 'message'] } } } } } },
        '/admin/revenue/daily': { get: { summary: 'Daily revenue', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/mrr': { get: { summary: 'MRR calculation', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/churn': { get: { summary: 'Churn stats', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/ltv': { get: { summary: 'LTV analytics', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/revenue/forecast': { get: { summary: 'Revenue forecast', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/coupons': {
          get: { summary: 'List coupons', tags: ['Admin'], security: [{ bearer: [] }] },
          post: { summary: 'Create coupon', tags: ['Admin'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object' } } } } },
        },
        '/admin/rate-limits/{tenantId}': { get: { summary: 'Rate limit status', tags: ['Admin'], security: [{ bearer: [] }], parameters: [{ name: 'tenantId', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/admin/errors': { get: { summary: 'Error log', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/v1/onboarding/checklist': { get: { summary: 'Onboarding checklist', tags: ['Onboarding'], security: [{ bearer: [] }] } },
        '/v1/onboarding/complete': { post: { summary: 'Complete onboarding step', tags: ['Onboarding'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { step: { type: 'string' } }, required: ['step'] } } } } } },
        '/v1/onboarding/tips': { get: { summary: 'Quickstart tips (public)', tags: ['Onboarding'] } },
        '/admin/webhooks/logs': { get: { summary: 'Webhook delivery logs', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/webhooks/dead-letter': { get: { summary: 'Dead letter queue', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/webhooks/retry/{id}': { post: { summary: 'Retry webhook delivery', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/webhooks/stats': { get: { summary: 'Webhook delivery stats', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/status': { get: { summary: 'System status', tags: ['System'] } },
        '/status/incidents': { get: { summary: 'Recent incidents', tags: ['System'] } },
        '/status/history': { get: { summary: 'Uptime history', tags: ['System'] } },
        '/admin/dunning/active': { get: { summary: 'Active dunning cases', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/stats': { get: { summary: 'Dunning statistics', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/resolve/{id}': { post: { summary: 'Resolve dunning case', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/win-back': { get: { summary: 'Win-back campaign stats', tags: ['Admin'], security: [{ bearer: [] }] } },
        '/admin/dunning/win-back/{tenantId}': { post: { summary: 'Trigger win-back email', tags: ['Admin'], security: [{ bearer: [] }], parameters: [{ name: 'tenantId', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/licenses': { post: { summary: 'Generate license key', tags: ['Licenses'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { type: { type: 'string', enum: ['personal','team','enterprise','oem'] }, email: { type: 'string' }, name: { type: 'string' } }, required: ['type'] } } } } }, get: { summary: 'List licenses', tags: ['Licenses'], security: [{ bearer: [] }] } },
        '/v1/licenses/verify/{key}': { get: { summary: 'Verify license key (public)', tags: ['Licenses'], parameters: [{ name: 'key', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/licenses/activate/{key}': { post: { summary: 'Activate license (public)', tags: ['Licenses'], parameters: [{ name: 'key', in: 'path', required: true, schema: { type: 'string' } }] } },
        '/v1/missions/{id}/share': { post: { summary: 'Make mission public', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/{id}/poll': { get: { summary: 'Lightweight status poll', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/missions/batch': { post: { summary: 'Batch submit (pro+)', tags: ['Missions'], security: [{ bearer: [] }] } },
        '/v1/dashboard': { get: { summary: 'Tenant aggregated stats', tags: ['Dashboard'], security: [{ bearer: [] }], responses: { '200': { description: 'Mission counts, credit summary, webhook success rate, recent missions' } } } },
        '/playground': { get: { summary: 'Interactive API explorer', tags: ['System'], responses: { '200': { description: 'HTML page with API playground UI' } } } },
        '/v1/usage/export': { get: { summary: 'Export credit transactions as CSV', tags: ['Usage'], security: [{ bearer: [] }], parameters: [{ name: 'format', in: 'query', schema: { type: 'string', enum: ['csv'] } }, { name: 'from', in: 'query', schema: { type: 'string', format: 'date' } }, { name: 'to', in: 'query', schema: { type: 'string', format: 'date' } }], responses: { '200': { description: 'CSV file download', content: { 'text/csv': { schema: { type: 'string' } } } } } } },
        '/v1/invoices': { get: { summary: 'List invoices (subscriptions + credit purchases)', tags: ['Billing'], security: [{ bearer: [] }], responses: { '200': { description: 'Invoice list with id, date, amount, currency, status, description, items' } } } },
        '/v1/invoices/{id}': { get: { summary: 'Get single invoice detail', tags: ['Billing'], security: [{ bearer: [] }], parameters: [{ name: 'id', in: 'path', required: true, schema: { type: 'string' } }], responses: { '200': { description: 'Invoice detail' }, '404': { description: 'Invoice not found' } } } },
        '/billing/checkout': { post: { summary: 'Create Polar checkout session', tags: ['Billing'], security: [{ bearer: [] }], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { product_id: { type: 'string' }, success_url: { type: 'string' }, cancel_url: { type: 'string' } }, required: ['product_id'] } } } } } },
        '/billing/checkout/products': { get: { summary: 'List purchasable products', tags: ['Billing'] } },
        '/v1/tenants/limits': { get: { summary: 'Rate limits and usage quotas', tags: ['Tenants'], security: [{ bearer: [] }] } },
        '/metrics': { get: { summary: 'Request metrics (24h)', tags: ['System'] } },
        '/metrics/live': { get: { summary: 'Live metrics (current hour)', tags: ['System'] } },
        '/docs': { get: { summary: 'API reference docs', tags: ['System'] } },
        '/v1/referrals/generate': { post: { summary: 'Generate referral code', tags: ['Referrals'], security: [{ bearer: [] }] } },
        '/v1/referrals/stats': { get: { summary: 'Referral stats dashboard', tags: ['Referrals'], security: [{ bearer: [] }] } },
        '/v1/referrals/apply': { post: { summary: 'Apply referral code', tags: ['Referrals'], requestBody: { content: { 'application/json': { schema: { type: 'object', properties: { code: { type: 'string' }, email: { type: 'string' } }, required: ['code', 'email'] } } } } } },
        '/v1/projects': { post: { summary: 'Create project', tags: ['Projects'], security: [{ bearer: [] }] }, get: { summary: 'List projects', tags: ['Projects'], security: [{ bearer: [] }] } },
        '/v1/projects/{id}': { get: { summary: 'Get project', tags: ['Projects'], security: [{ bearer: [] }] }, delete: { summary: 'Archive project', tags: ['Projects'], security: [{ bearer: [] }] } },
        '/v1/projects/{id}/missions': { get: { summary: 'Project missions', tags: ['Projects'], security: [{ bearer: [] }] } },
        '/v1/team/invite': { post: { summary: 'Invite team member (pro+)', tags: ['Team'], security: [{ bearer: [] }] } },
        '/v1/team/members': { get: { summary: 'List team members', tags: ['Team'], security: [{ bearer: [] }] } },
        '/v1/team/members/{id}': { put: { summary: 'Update member role', tags: ['Team'], security: [{ bearer: [] }] }, delete: { summary: 'Remove member', tags: ['Team'], security: [{ bearer: [] }] } },
        '/v1/webhooks/events': { get: { summary: 'List webhook event types', tags: ['Webhooks'], security: [{ bearer: [] }] } },
        '/v1/webhooks/test': { post: { summary: 'Send test webhook', tags: ['Webhooks'], security: [{ bearer: [] }] } },
        '/v1/webhooks/config': { get: { summary: 'Webhook configuration', tags: ['Webhooks'], security: [{ bearer: [] }] } },
        '/v1/audit': { get: { summary: 'Tenant audit log', tags: ['Audit'], security: [{ bearer: [] }], parameters: [{ name: 'limit', in: 'query', schema: { type: 'integer' } }, { name: 'offset', in: 'query', schema: { type: 'integer' } }] } },
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
