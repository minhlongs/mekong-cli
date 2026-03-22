// Mission Chain Orchestration Service — CRUD for chains + runs, admin overview

const uid = () => crypto.randomUUID();

/** List all chains for a tenant */
async function listChains(db: any, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM mission_chains WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenantId).all();
  return rows.results as unknown[];
}

/** Create a new mission chain */
async function createChain(
  db: any,
  tenantId: string,
  chainName: string,
  opts: { stepsJson?: string; maxRetries?: number } = {}
): Promise<unknown> {
  const id  = uid();
  const now = new Date().toISOString();
  return db.prepare(
    `INSERT INTO mission_chains
       (id, tenant_id, chain_name, steps_json, max_retries, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id,
    tenantId,
    chainName,
    opts.stepsJson  ?? '[]',
    opts.maxRetries ?? 3,
    now,
    now
  ).first();
}

/** List runs for a tenant, optionally filtered by chain_id */
async function getRuns(
  db: any,
  tenantId: string,
  chainId?: string,
  limit = 50
): Promise<unknown[]> {
  const safeLimit = Math.min(limit, 200);
  if (chainId) {
    const rows = await db.prepare(
      `SELECT * FROM mission_chain_runs
       WHERE tenant_id = ? AND chain_id = ?
       ORDER BY started_at DESC LIMIT ?`
    ).bind(tenantId, chainId, safeLimit).all();
    return rows.results as unknown[];
  }
  const rows = await db.prepare(
    `SELECT * FROM mission_chain_runs
     WHERE tenant_id = ?
     ORDER BY started_at DESC LIMIT ?`
  ).bind(tenantId, safeLimit).all();
  return rows.results as unknown[];
}

/** Admin overview: chain + run counts by status across all tenants */
async function getAdminOverview(db: any): Promise<unknown> {
  const [totalChains, activeChains, totalRuns, runsByStatus] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM mission_chains`).first() as Promise<{ count: number } | null>,
    db.prepare(`SELECT COUNT(*) as count FROM mission_chains WHERE status = 'active'`).first() as Promise<{ count: number } | null>,
    db.prepare(`SELECT COUNT(*) as count FROM mission_chain_runs`).first() as Promise<{ count: number } | null>,
    db.prepare(
      `SELECT status, COUNT(*) as count FROM mission_chain_runs GROUP BY status`
    ).all(),
  ]);

  return {
    chains: {
      total:  (totalChains  as any)?.count ?? 0,
      active: (activeChains as any)?.count ?? 0,
    },
    runs: {
      total:    (totalRuns as any)?.count ?? 0,
      byStatus: runsByStatus.results as unknown[],
    },
  };
}

export const missionChainOrchestrationService = {
  listChains,
  createChain,
  getRuns,
  getAdminOverview,
};
