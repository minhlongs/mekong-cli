/**
 * Mission Quality Gates Service
 * Manage tenant-scoped quality gate definitions and mission evaluations
 */

export interface QualityGate {
  id: string;
  tenantId: string;
  gateName: string;
  criteriaJson: string;
  isBlocking: number;
  isActive: number;
  createdAt: string;
}

export interface GateEvaluation {
  id: string;
  tenantId: string;
  gateId: string;
  missionId: string;
  passed: number;
  details: string | null;
  evaluatedAt: string;
}

type GateRow = {
  id: string;
  tenant_id: string;
  gate_name: string;
  criteria_json: string;
  is_blocking: number;
  is_active: number;
  created_at: string;
};

type EvalRow = {
  id: string;
  tenant_id: string;
  gate_id: string;
  mission_id: string;
  passed: number;
  details: string | null;
  evaluated_at: string;
};

function mapGate(row: GateRow): QualityGate {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    gateName: row.gate_name,
    criteriaJson: row.criteria_json,
    isBlocking: row.is_blocking,
    isActive: row.is_active,
    createdAt: row.created_at,
  };
}

function mapEval(row: EvalRow): GateEvaluation {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    gateId: row.gate_id,
    missionId: row.mission_id,
    passed: row.passed,
    details: row.details,
    evaluatedAt: row.evaluated_at,
  };
}

/** List all active quality gates for a tenant */
async function listGates(db: any, tenantId: string): Promise<QualityGate[]> {
  try {
    const result = await db
      .prepare('SELECT * FROM quality_gates WHERE tenant_id = ? AND is_active = 1 ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return ((result.results ?? []) as GateRow[]).map(mapGate);
  } catch (err) {
    console.error('[missionQualityGatesService.listGates] error:', err);
    throw err;
  }
}

/** Create a new quality gate for a tenant */
async function createGate(
  db: any,
  tenantId: string,
  gateName: string,
  criteriaJson: string,
  isBlocking = 1
): Promise<QualityGate> {
  try {
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO quality_gates (id, tenant_id, gate_name, criteria_json, is_blocking)
         VALUES (?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, gateName, criteriaJson, isBlocking)
      .run();
    const row = (await db
      .prepare('SELECT * FROM quality_gates WHERE id = ?')
      .bind(id)
      .first()) as GateRow | null;
    if (!row) throw new Error('Gate insert failed');
    return mapGate(row);
  } catch (err) {
    console.error('[missionQualityGatesService.createGate] error:', err);
    throw err;
  }
}

/** Get all evaluations for a tenant, optionally filtered by mission_id */
async function getEvaluations(
  db: any,
  tenantId: string,
  missionId?: string
): Promise<GateEvaluation[]> {
  try {
    let query = 'SELECT * FROM gate_evaluations WHERE tenant_id = ?';
    const bindings: string[] = [tenantId];
    if (missionId) {
      query += ' AND mission_id = ?';
      bindings.push(missionId);
    }
    query += ' ORDER BY evaluated_at DESC';
    const result = await db
      .prepare(query)
      .bind(...bindings)
      .all();
    return ((result.results ?? []) as EvalRow[]).map(mapEval);
  } catch (err) {
    console.error('[missionQualityGatesService.getEvaluations] error:', err);
    throw err;
  }
}

/** Admin: overview of gate pass/fail rates across all tenants (last 500 evals) */
async function getAdminOverview(db: any): Promise<{
  tenantId: string;
  gateId: string;
  total: number;
  passed: number;
  failed: number;
  passRate: number;
}[]> {
  try {
    type OverviewRow = { tenant_id: string; gate_id: string; total: number; passed: number; failed: number };
    const result = await db
      .prepare(
        `SELECT tenant_id, gate_id,
                COUNT(*) as total,
                SUM(passed) as passed,
                COUNT(*) - SUM(passed) as failed
         FROM gate_evaluations
         GROUP BY tenant_id, gate_id
         ORDER BY total DESC
         LIMIT 500`
      )
      .all();
    return ((result.results ?? []) as OverviewRow[]).map((r) => ({
      tenantId: r.tenant_id,
      gateId: r.gate_id,
      total: r.total,
      passed: r.passed,
      failed: r.failed,
      passRate: r.total > 0 ? Math.round((r.passed / r.total) * 100) : 0,
    }));
  } catch (err) {
    console.error('[missionQualityGatesService.getAdminOverview] error:', err);
    throw err;
  }
}

export const missionQualityGatesService = {
  listGates,
  createGate,
  getEvaluations,
  getAdminOverview,
};
