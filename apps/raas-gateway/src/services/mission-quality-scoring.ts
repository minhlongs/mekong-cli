/**
 * Mission Quality Scoring Service
 * Tenant-scoped quality scores (accuracy, completeness, timeliness) per mission
 * and configurable scoring criteria with weights.
 */

// ─── Types ───────────────────────────────────────────────────────────────────

type ScoreRow = {
  id: string;
  tenant_id: string;
  mission_id: string;
  accuracy_score: number | null;
  completeness_score: number | null;
  timeliness_score: number | null;
  overall_score: number | null;
  scored_by: string | null;
  created_at: string;
};

type CriteriaRow = {
  id: string;
  tenant_id: string;
  criteria_name: string;
  weight: number;
  description: string | null;
  created_at: string;
};

type OverviewRow = {
  tenant_id: string;
  total: number;
  avg_accuracy: number | null;
  avg_completeness: number | null;
  avg_timeliness: number | null;
  avg_overall: number | null;
};

// ─── Helpers ─────────────────────────────────────────────────────────────────

function mapScore(row: ScoreRow) {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    missionId: row.mission_id,
    accuracyScore: row.accuracy_score,
    completenessScore: row.completeness_score,
    timelinessScore: row.timeliness_score,
    overallScore: row.overall_score,
    scoredBy: row.scored_by,
    createdAt: row.created_at,
  };
}

function mapCriteria(row: CriteriaRow) {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    criteriaName: row.criteria_name,
    weight: row.weight,
    description: row.description,
    createdAt: row.created_at,
  };
}

// ─── Service functions ────────────────────────────────────────────────────────

/** List quality scores for a tenant, optionally filtered by mission_id */
async function listScores(db: any, tenantId: string, missionId?: string) {
  try {
    let query = 'SELECT * FROM mission_quality_scores WHERE tenant_id = ?';
    const bindings: string[] = [tenantId];
    if (missionId) {
      query += ' AND mission_id = ?';
      bindings.push(missionId);
    }
    query += ' ORDER BY created_at DESC LIMIT 200';
    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: ((result.results ?? []) as ScoreRow[]).map(mapScore) };
  } catch (err) {
    console.error('[missionQualityScoringService.listScores] error:', err);
    return { success: false, error: 'Failed to list quality scores' };
  }
}

/** Create a quality score entry for a mission */
async function createScore(
  db: any,
  tenantId: string,
  body: {
    mission_id: string;
    accuracy_score?: number;
    completeness_score?: number;
    timeliness_score?: number;
    overall_score?: number;
    scored_by?: string;
  }
) {
  try {
    const id = crypto.randomUUID();
    await db
      .prepare(
        `INSERT INTO mission_quality_scores
           (id, tenant_id, mission_id, accuracy_score, completeness_score,
            timeliness_score, overall_score, scored_by)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        body.mission_id,
        body.accuracy_score ?? null,
        body.completeness_score ?? null,
        body.timeliness_score ?? null,
        body.overall_score ?? null,
        body.scored_by ?? null
      )
      .run();
    const row = (await db
      .prepare('SELECT * FROM mission_quality_scores WHERE id = ?')
      .bind(id)
      .first()) as ScoreRow | null;
    if (!row) throw new Error('Score insert failed');
    return { success: true, data: mapScore(row) };
  } catch (err) {
    console.error('[missionQualityScoringService.createScore] error:', err);
    return { success: false, error: 'Failed to create quality score' };
  }
}

/** List quality criteria for a tenant */
async function getCriteria(db: any, tenantId: string) {
  try {
    const result = await db
      .prepare('SELECT * FROM mission_quality_criteria WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { success: true, data: ((result.results ?? []) as CriteriaRow[]).map(mapCriteria) };
  } catch (err) {
    console.error('[missionQualityScoringService.getCriteria] error:', err);
    return { success: false, error: 'Failed to fetch quality criteria' };
  }
}

/** Admin: per-tenant scoring overview (avg scores, total scored missions) */
async function getAdminOverview(db: any) {
  try {
    const result = await db
      .prepare(
        `SELECT tenant_id,
                COUNT(*) as total,
                AVG(accuracy_score) as avg_accuracy,
                AVG(completeness_score) as avg_completeness,
                AVG(timeliness_score) as avg_timeliness,
                AVG(overall_score) as avg_overall
         FROM mission_quality_scores
         GROUP BY tenant_id
         ORDER BY total DESC
         LIMIT 500`
      )
      .all();
    const data = ((result.results ?? []) as OverviewRow[]).map((r) => ({
      tenantId: r.tenant_id,
      total: r.total,
      avgAccuracy: r.avg_accuracy != null ? Math.round(r.avg_accuracy * 100) / 100 : null,
      avgCompleteness: r.avg_completeness != null ? Math.round(r.avg_completeness * 100) / 100 : null,
      avgTimeliness: r.avg_timeliness != null ? Math.round(r.avg_timeliness * 100) / 100 : null,
      avgOverall: r.avg_overall != null ? Math.round(r.avg_overall * 100) / 100 : null,
    }));
    return { success: true, data };
  } catch (err) {
    console.error('[missionQualityScoringService.getAdminOverview] error:', err);
    return { success: false, error: 'Failed to fetch admin overview' };
  }
}

// ─── Export ───────────────────────────────────────────────────────────────────

export const missionQualityScoringService = {
  listScores,
  createScore,
  getCriteria,
  getAdminOverview,
};
