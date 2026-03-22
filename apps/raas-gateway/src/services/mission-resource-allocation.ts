/**
 * Mission Resource Allocation Service
 * Manages resource allocations per mission and resource pools per tenant
 */

export interface ResourceAllocation {
  id: string;
  tenant_id: string;
  mission_id: string;
  resource_type: string;
  allocated_amount: number;
  used_amount: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ResourcePool {
  id: string;
  tenant_id: string;
  pool_name: string;
  resource_type: string;
  total_capacity: number;
  available_capacity: number;
  created_at: string;
}

export interface CreateAllocationInput {
  mission_id: string;
  resource_type: string;
  allocated_amount: number;
}

/**
 * List all resource allocations for a tenant
 * Optional filter by mission_id or resource_type query params
 */
async function listAllocations(
  db: any,
  tenantId: string,
  filters: { mission_id?: string; resource_type?: string } = {}
): Promise<{ success: boolean; data?: ResourceAllocation[]; error?: string }> {
  try {
    let query = 'SELECT * FROM mission_resource_allocations WHERE tenant_id = ?';
    const bindings: string[] = [tenantId];

    if (filters.mission_id) {
      query += ' AND mission_id = ?';
      bindings.push(filters.mission_id);
    }

    if (filters.resource_type) {
      query += ' AND resource_type = ?';
      bindings.push(filters.resource_type);
    }

    query += ' ORDER BY created_at DESC';

    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: result.results as ResourceAllocation[] };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to list allocations';
    return { success: false, error };
  }
}

/**
 * Create a new resource allocation for a mission
 * Generates a UUID-style id using crypto
 */
async function createAllocation(
  db: any,
  tenantId: string,
  input: CreateAllocationInput
): Promise<{ success: boolean; data?: ResourceAllocation; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO mission_resource_allocations
          (id, tenant_id, mission_id, resource_type, allocated_amount, used_amount, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, 0, 'allocated', ?, ?)`
      )
      .bind(id, tenantId, input.mission_id, input.resource_type, input.allocated_amount, now, now)
      .run();

    const row = await db
      .prepare('SELECT * FROM mission_resource_allocations WHERE id = ?')
      .bind(id)
      .first() as ResourceAllocation | null;

    return { success: true, data: row ?? undefined };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to create allocation';
    return { success: false, error };
  }
}

/**
 * List all resource pools for a tenant
 * Optional filter by resource_type
 */
async function getPools(
  db: any,
  tenantId: string,
  resource_type?: string
): Promise<{ success: boolean; data?: ResourcePool[]; error?: string }> {
  try {
    let query = 'SELECT * FROM mission_resource_pools WHERE tenant_id = ?';
    const bindings: string[] = [tenantId];

    if (resource_type) {
      query += ' AND resource_type = ?';
      bindings.push(resource_type);
    }

    query += ' ORDER BY created_at DESC';

    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: result.results as ResourcePool[] };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to get pools';
    return { success: false, error };
  }
}

/**
 * Admin overview — aggregate stats across all tenants
 * Returns total allocations, pools, capacity utilization, top resource types
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: Record<string, unknown>; error?: string }> {
  try {
    const [allocStats, poolStats, topTypes] = await Promise.all([
      db
        .prepare(
          `SELECT
            COUNT(*) as total_allocations,
            SUM(allocated_amount) as total_allocated,
            SUM(used_amount) as total_used,
            COUNT(DISTINCT tenant_id) as active_tenants
           FROM mission_resource_allocations`
        )
        .first(),
      db
        .prepare(
          `SELECT
            COUNT(*) as total_pools,
            SUM(total_capacity) as total_capacity,
            SUM(available_capacity) as available_capacity
           FROM mission_resource_pools`
        )
        .first(),
      db
        .prepare(
          `SELECT resource_type, COUNT(*) as count, SUM(allocated_amount) as total_allocated
           FROM mission_resource_allocations
           GROUP BY resource_type
           ORDER BY count DESC
           LIMIT 10`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        allocations: allocStats,
        pools: poolStats,
        top_resource_types: topTypes.results,
      },
    };
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Failed to get admin overview';
    return { success: false, error };
  }
}

export const missionResourceAllocationService = {
  listAllocations,
  createAllocation,
  getPools,
  getAdminOverview,
};
