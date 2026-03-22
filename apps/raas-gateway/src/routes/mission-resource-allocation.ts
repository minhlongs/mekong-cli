/**
 * Mission Resource Allocation routes
 * GET  /allocations        — list tenant allocations
 * POST /allocations        — create allocation
 * GET  /pools              — list tenant resource pools
 * GET  /admin/overview     — admin aggregate stats (X-Admin-Key protected)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionResourceAllocationService as svc } from '../services/mission-resource-allocation';

// Inline Bindings — no import from index.ts
interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

/**
 * GET /allocations — list resource allocations for the authenticated tenant
 * Query: ?mission_id=&resource_type=
 */
app.get('/allocations', auth(), async (c) => {
  const tenant = getTenant(c);
  const mission_id = c.req.query('mission_id');
  const resource_type = c.req.query('resource_type');

  try {
    const result = await svc.listAllocations(c.env.DB, tenant.tenantId, {
      mission_id,
      resource_type,
    });

    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }

    return c.json({ success: true, data: result.data, total: result.data?.length ?? 0 });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * POST /allocations — create a resource allocation for a mission
 * Body: { mission_id, resource_type, allocated_amount }
 */
app.post('/allocations', auth(), async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));

  const mission_id = body.mission_id?.trim();
  const resource_type = body.resource_type?.trim();
  const allocated_amount = Number(body.allocated_amount);

  if (!mission_id) {
    return c.json({ error: 'mission_id is required' }, 400);
  }
  if (!resource_type) {
    return c.json({ error: 'resource_type is required' }, 400);
  }
  if (!allocated_amount || allocated_amount <= 0) {
    return c.json({ error: 'allocated_amount must be a positive number' }, 400);
  }

  try {
    const result = await svc.createAllocation(c.env.DB, tenant.tenantId, {
      mission_id,
      resource_type,
      allocated_amount,
    });

    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }

    return c.json({ success: true, data: result.data }, 201);
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /pools — list resource pools for the authenticated tenant
 * Query: ?resource_type=
 */
app.get('/pools', auth(), async (c) => {
  const tenant = getTenant(c);
  const resource_type = c.req.query('resource_type');

  try {
    const result = await svc.getPools(c.env.DB, tenant.tenantId, resource_type);

    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }

    return c.json({ success: true, data: result.data, total: result.data?.length ?? 0 });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

/**
 * GET /admin/overview — aggregate stats across all tenants
 * Protected by X-Admin-Key header — returns 403 if missing or invalid
 */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  const expected = c.env.ADMIN_API_KEY;

  if (!expected || key !== expected) {
    return c.json({ error: 'Forbidden' }, 403);
  }

  try {
    const result = await svc.getAdminOverview(c.env.DB);

    if (!result.success) {
      return c.json({ error: result.error }, 500);
    }

    return c.json({ success: true, data: result.data });
  } catch {
    return c.json({ error: 'Internal server error' }, 500);
  }
});

export { app as missionResourceAllocation };
