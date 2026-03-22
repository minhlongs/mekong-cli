/**
 * Admin Deployment Pipeline Service — CRUD for pipelines and run history
 * All functions accept db: any (D1 duck-typed), return { success, data/error }
 */

export async function listPipelines(db: any, environment?: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    let query = `SELECT * FROM deployment_pipelines`;
    const bindings: string[] = [];
    if (environment) {
      query += ` WHERE environment = ?`;
      bindings.push(environment);
    }
    query += ` ORDER BY created_at DESC`;
    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: result.results };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

export async function createPipeline(db: any, body: {
  pipeline_name: string;
  environment?: string;
  stages_json: string;
}): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    const env = body.environment ?? 'production';
    await db.prepare(
      `INSERT INTO deployment_pipelines (id, pipeline_name, environment, stages_json, status, created_at, updated_at)
       VALUES (?, ?, ?, ?, 'idle', ?, ?)`
    ).bind(id, body.pipeline_name, env, body.stages_json, now, now).run();
    const pipeline = await db.prepare(`SELECT * FROM deployment_pipelines WHERE id = ?`).bind(id).first();
    return { success: true, data: pipeline };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

export async function getRuns(db: any, pipelineId?: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    let query = `SELECT * FROM deployment_pipeline_runs`;
    const bindings: string[] = [];
    if (pipelineId) {
      query += ` WHERE pipeline_id = ?`;
      bindings.push(pipelineId);
    }
    query += ` ORDER BY started_at DESC LIMIT 100`;
    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: result.results };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

export async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [total, byStatus, byEnv, recentRuns] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as count FROM deployment_pipelines`).first(),
      db.prepare(
        `SELECT status, COUNT(*) as count FROM deployment_pipelines GROUP BY status`
      ).all(),
      db.prepare(
        `SELECT environment, COUNT(*) as count FROM deployment_pipelines GROUP BY environment`
      ).all(),
      db.prepare(
        `SELECT r.*, p.pipeline_name FROM deployment_pipeline_runs r
         LEFT JOIN deployment_pipelines p ON p.id = r.pipeline_id
         ORDER BY r.started_at DESC LIMIT 10`
      ).all(),
    ]);
    return {
      success: true,
      data: {
        totalPipelines: total?.count ?? 0,
        byStatus: byStatus.results,
        byEnvironment: byEnv.results,
        recentRuns: recentRuns.results,
      },
    };
  } catch (e) {
    return { success: false, error: String(e) };
  }
}

export const adminDeploymentPipelineService = {
  listPipelines,
  createPipeline,
  getRuns,
  getDashboard,
};
