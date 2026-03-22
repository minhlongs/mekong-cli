/**
 * Platform Resource Pools Service — admin capacity management across tenants
 * Manages resource_pools and pool_allocations tables
 */

// db typed as any per project constraint (no generic type args on D1 calls)

export interface ResourcePool {
  id: string;
  pool_name: string;
  resource_type: string;
  total_capacity: number;
  allocated: number;
  available: number;
  status: string;
  created_at: string;
}

export interface PoolAllocation {
  id: string;
  pool_id: string;
  tenant_id: string;
  amount: number;
  allocated_at: string;
  released_at: string | null;
}

export interface CreatePoolInput {
  pool_name: string;
  resource_type: string;
  total_capacity: number;
  status?: string;
}

export interface ResourcePoolDashboard {
  totalPools: number;
  activePools: number;
  totalCapacity: number;
  totalAllocated: number;
  totalAvailable: number;
  utilizationPct: number;
  byResourceType: Record<string, { capacity: number; allocated: number; available: number }>;
}

/** List all resource pools, optional filter by status */
async function listPools(db: any, status?: string): Promise<ResourcePool[]> {
  try {
    const query = status
      ? `SELECT * FROM resource_pools WHERE status = ? ORDER BY created_at DESC`
      : `SELECT * FROM resource_pools ORDER BY created_at DESC`;
    const result = status
      ? await db.prepare(query).bind(status).all()
      : await db.prepare(query).all();
    return result.results as ResourcePool[];
  } catch {
    return [];
  }
}

/** Create a new resource pool — available initialised to total_capacity */
async function createPool(db: any, input: CreatePoolInput): Promise<ResourcePool | null> {
  try {
    const id = crypto.randomUUID();
    const status = input.status ?? 'active';
    await db.prepare(
      `INSERT INTO resource_pools (id, pool_name, resource_type, total_capacity, allocated, available, status)
       VALUES (?, ?, ?, ?, 0, ?, ?)`
    ).bind(id, input.pool_name, input.resource_type, input.total_capacity, input.total_capacity, status).run();

    const row = await db.prepare(
      `SELECT * FROM resource_pools WHERE id = ?`
    ).bind(id).first();
    return row as ResourcePool | null;
  } catch {
    return null;
  }
}

/** List allocations — optional filter by pool_id and/or active-only (released_at IS NULL) */
async function getAllocations(
  db: any,
  poolId?: string,
  activeOnly?: boolean
): Promise<PoolAllocation[]> {
  try {
    const conditions: string[] = [];
    const binds: unknown[] = [];

    if (poolId) {
      conditions.push('pool_id = ?');
      binds.push(poolId);
    }
    if (activeOnly) {
      conditions.push('released_at IS NULL');
    }

    const where = conditions.length > 0 ? `WHERE ${conditions.join(' AND ')}` : '';
    const query = `SELECT * FROM pool_allocations ${where} ORDER BY allocated_at DESC`;

    const result = binds.length > 0
      ? await db.prepare(query).bind(...binds).all()
      : await db.prepare(query).all();
    return result.results as PoolAllocation[];
  } catch {
    return [];
  }
}

/** Dashboard summary — utilization by pool and by resource_type */
async function getDashboard(db: any): Promise<ResourcePoolDashboard> {
  try {
    const pools = await listPools(db);

    const totalPools = pools.length;
    const activePools = pools.filter(p => p.status === 'active').length;
    const totalCapacity = pools.reduce((s, p) => s + p.total_capacity, 0);
    const totalAllocated = pools.reduce((s, p) => s + p.allocated, 0);
    const totalAvailable = pools.reduce((s, p) => s + p.available, 0);
    const utilizationPct =
      totalCapacity > 0 ? Math.round((totalAllocated / totalCapacity) * 1000) / 10 : 0;

    const byResourceType: ResourcePoolDashboard['byResourceType'] = {};
    for (const pool of pools) {
      const rt = pool.resource_type;
      if (!byResourceType[rt]) {
        byResourceType[rt] = { capacity: 0, allocated: 0, available: 0 };
      }
      byResourceType[rt].capacity += pool.total_capacity;
      byResourceType[rt].allocated += pool.allocated;
      byResourceType[rt].available += pool.available;
    }

    return { totalPools, activePools, totalCapacity, totalAllocated, totalAvailable, utilizationPct, byResourceType };
  } catch {
    return {
      totalPools: 0, activePools: 0, totalCapacity: 0, totalAllocated: 0,
      totalAvailable: 0, utilizationPct: 0, byResourceType: {},
    };
  }
}

export const platformResourcePoolsService = {
  listPools,
  createPool,
  getAllocations,
  getDashboard,
};
