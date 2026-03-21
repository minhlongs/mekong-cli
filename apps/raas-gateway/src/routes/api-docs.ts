/**
 * API Docs route — serves HTML API reference page at GET /docs
 */

import { Hono } from 'hono';
import type { Env } from '../index';

export const apiDocs = new Hono<{ Bindings: Env }>();

// [method, path, description, requiresAuth?]
const ENDPOINTS: [string, string, string, boolean?][] = [
  // Tenants
  ['POST', '/v1/tenants/signup',    'Create account → JWT + 10 credits'],
  ['GET',  '/v1/tenants/profile',   'Get tenant profile', true],
  ['PUT',  '/v1/tenants/settings',  'Update webhook URL, notifications', true],
  ['POST', '/v1/tenants/api-keys',  'Create API key', true],
  ['GET',  '/v1/tenants/api-keys',  'List API keys', true],
  ['GET',  '/v1/tenants/usage',     'Monthly usage stats', true],
  // Missions
  ['POST', '/v1/missions',           'Submit mission (1–5 MCU)', true],
  ['GET',  '/v1/missions',           'List missions (paginated)', true],
  ['GET',  '/v1/missions/:id',       'Get mission + full result', true],
  ['GET',  '/v1/missions/:id/poll',  'Lightweight status poll', true],
  ['POST', '/v1/missions/:id/cancel','Cancel + refund credits', true],
  ['POST', '/v1/missions/:id/share', 'Make mission public', true],
  ['POST', '/v1/missions/batch',     'Batch submit (pro+)', true],
  ['GET',  '/v1/missions/templates', 'Browse mission templates'],
  // Credits
  ['GET',  '/credits',              'Balance + total spent', true],
  ['POST', '/credits/check',        'Pre-check cost before submitting', true],
  ['GET',  '/credits/history',      'Transaction history', true],
  ['POST', '/v1/credits/redeem',    'Redeem coupon code', true],
  // Billing
  ['GET',  '/billing/pricing',            'Subscription tiers + pricing'],
  ['GET',  '/billing/stripe/packs',       'One-time credit packs'],
  ['POST', '/billing/stripe/checkout',    'Create Stripe checkout session', true],
  ['GET',  '/v1/invoices',               'Invoice history', true],
  // Marketplace
  ['GET',  '/marketplace',               'Search public missions'],
  ['GET',  '/marketplace/featured',      'Featured / trending missions'],
  ['GET',  '/marketplace/stats',         'Platform-wide stats'],
  ['GET',  '/marketplace/leaderboard',   'Top referrers'],
  ['GET',  '/marketplace/:id/reviews',   'Reviews for a mission'],
  ['POST', '/marketplace/:id/reviews',   'Submit a review', true],
  // Admin
  ['GET',  '/admin/revenue/daily',       'Daily revenue', true],
  ['GET',  '/admin/revenue/mrr',         'MRR calculation', true],
  ['GET',  '/admin/coupons',             'List / create coupons', true],
  ['GET',  '/admin/webhooks/logs',       'Webhook delivery logs', true],
  ['GET',  '/admin/errors',              'Error log', true],
  // System
  ['GET',  '/health',        'Basic health check'],
  ['GET',  '/health/deep',   'Deep health + component checks'],
  ['GET',  '/status',        'System status page'],
  ['GET',  '/stats',         'Public platform stats'],
  ['GET',  '/openapi.json',  'Full OpenAPI 3.0 spec'],
  ['GET',  '/playground',    'Interactive API explorer'],
];

const MC: Record<string, string> = {
  GET: '#22d3ee', POST: '#a78bfa', PUT: '#fbbf24', DELETE: '#f87171',
};

const rows = ENDPOINTS.map(([m, p, d, auth]) =>
  `<div class="ep"><span class="b" style="background:${MC[m]??'#888'}">${m}</span><code>${p}</code><span class="d">${d}</span>${auth ? '<span title="Auth required">&#128274;</span>' : ''}</div>`
).join('');

/** GET /docs — HTML API reference page */
apiDocs.get('/', (c) => c.html(`<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Mekong RaaS API Reference</title>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{font-family:system-ui,sans-serif;background:#0a0a0a;color:#e5e5e5;min-height:100vh}
    .wrap{max-width:900px;margin:0 auto;padding:32px 20px}
    h1{color:#22d3ee;font-size:1.5rem;margin-bottom:6px}
    .sub{color:#71717a;font-size:.85rem;margin-bottom:14px}
    .links{display:flex;gap:10px;margin-bottom:28px}
    .links a{color:#22d3ee;font-size:.82rem;text-decoration:none;border:1px solid #22d3ee33;padding:4px 12px;border-radius:6px}
    .links a:hover{background:#22d3ee18}
    .ep{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;background:#111;margin-bottom:5px;border:1px solid #1f1f1f}
    .b{font-size:.68rem;font-weight:700;padding:2px 7px;border-radius:4px;color:#0a0a0a;min-width:46px;text-align:center;flex-shrink:0}
    code{font-family:monospace;font-size:.8rem;color:#d4d4d8;flex:1}
    .d{color:#71717a;font-size:.8rem}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Mekong RaaS API Reference</h1>
    <p class="sub">Robot-as-a-Service Gateway &mdash; AI-operated business platform</p>
    <div class="links">
      <a href="/openapi.json">OpenAPI JSON</a>
      <a href="/playground">Interactive Playground</a>
    </div>
    ${rows}
  </div>
</body>
</html>`));
