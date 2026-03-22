/**
 * Platform Resource Pools routes — admin-only capacity management at /admin/resource-pools
 * All routes require X-Admin-Key header authentication (403 on failure)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { json } from '../utils/response';
import { platformResourcePoolsService } from '../services/platform-resource-pools';

const app = new Hono<{ Bindings: Env }>();

// Admin auth guard — all routes require X-Admin-Key
app.use('/*', async (c, next) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /admin/resource-pools/pools?status=active — list all pools, optional status filter
app.get('/pools', async (c) => {
  try {
    const status = c.req.query('status');
    const pools = await platformResourcePoolsService.listPools(c.env.DB, status);
    return json({ pools });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// POST /admin/resource-pools/pools — create a new resource pool
// Body: { pool_name, resource_type, total_capacity, status? }
app.post('/pools', async (c) => {
  try {
    const body = await c.req.json();
    const { pool_name, resource_type, total_capacity, status } = body;

    if (!pool_name || !resource_type || total_capacity == null) {
      return json({ error: 'pool_name, resource_type, and total_capacity are required' }, { status: 400 });
    }
    if (typeof total_capacity !== 'number' || total_capacity < 1) {
      return json({ error: 'total_capacity must be a positive integer' }, { status: 400 });
    }

    const pool = await platformResourcePoolsService.createPool(c.env.DB, {
      pool_name,
      resource_type,
      total_capacity: Math.floor(total_capacity),
      status,
    });

    if (!pool) return json({ error: 'Failed to create pool' }, { status: 500 });
    return json({ pool }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/resource-pools/allocations?pool_id=&active=true — list allocations
app.get('/allocations', async (c) => {
  try {
    const poolId = c.req.query('pool_id');
    const activeOnly = c.req.query('active') === 'true';
    const allocations = await platformResourcePoolsService.getAllocations(c.env.DB, poolId, activeOnly);
    return json({ allocations });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// GET /admin/resource-pools/dashboard — utilization summary by pool and resource_type
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await platformResourcePoolsService.getDashboard(c.env.DB);
    return json(dashboard);
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

export { app as platformResourcePools };
