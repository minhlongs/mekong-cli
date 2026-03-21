/**
 * API v1 routes with authentication
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { rateLimit } from '../middleware/rate-limiter';
import { json, notFound } from '../utils/response';
import { missions } from './missions';

export const api = new Hono<{ Bindings: Env }>();

// API root - no auth required to see available endpoints
api.get('/', (c) => {
  return c.json({
    name: 'RaaS Gateway API',
    version: 'v1',
    endpoints: {
      missions: '/v1/missions',
      credits: '/v1/credits',
      tenants: '/v1/tenants',
      me: '/v1/me',
    },
  });
});

// All other /v1/* routes require authentication
api.use('/*', auth());
// Apply rate limiting after auth (requires tenant context)
api.use('/*', rateLimit());

// Get current tenant info
api.get('/me', (c) => {
  const tenant = getTenant(c);
  return json({
    tenantId: tenant.tenantId,
    tier: tenant.tier,
    permissions: tenant.permissions,
  });
});

// Mission routes
api.route('/missions', missions);

// Placeholder — implemented later
api.all('/tenants/*', async (c) => notFound('Tenants endpoint not yet implemented'));
