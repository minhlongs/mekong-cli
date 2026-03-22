/**
 * Admin Capacity Planning Service
 * Manage resource utilization plans and scale recommendations for platform ops
 */

// List all capacity plans, optionally filtered by resource_type
async function listPlans(db: any, resourceType?: string): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    let query = 'SELECT * FROM capacity_plans ORDER BY created_at DESC';
    const params: string[] = [];

    if (resourceType) {
      query = 'SELECT * FROM capacity_plans WHERE resource_type = ? ORDER BY created_at DESC';
      params.push(resourceType);
    }

    const stmt = db.prepare(query);
    const result = params.length > 0
      ? await stmt.bind(...params).all()
      : await stmt.all();

    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Create a new capacity plan entry; auto-computes utilization_pct
async function createPlan(
  db: any,
  body: {
    plan_name: string;
    resource_type: string;
    current_usage: number;
    max_capacity: number;
    forecast_date?: string;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const utilization_pct = body.max_capacity > 0
      ? Math.round((body.current_usage / body.max_capacity) * 10000) / 100
      : 0;

    await db
      .prepare(
        `INSERT INTO capacity_plans (id, plan_name, resource_type, current_usage, max_capacity, utilization_pct, forecast_date)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        body.plan_name,
        body.resource_type,
        body.current_usage,
        body.max_capacity,
        utilization_pct,
        body.forecast_date ?? null
      )
      .run();

    const created = await db
      .prepare('SELECT * FROM capacity_plans WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Get all recommendations for a given plan_id
async function getRecommendations(
  db: any,
  planId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM capacity_recommendations WHERE plan_id = ? ORDER BY created_at DESC')
      .bind(planId)
      .all();

    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

// Aggregate dashboard: per-resource utilization summary + pending recommendation counts
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [utilization, recommendations] = await Promise.all([
      db
        .prepare(
          `SELECT resource_type,
                  COUNT(*) as plan_count,
                  ROUND(AVG(utilization_pct), 2) as avg_utilization,
                  MAX(utilization_pct) as max_utilization
           FROM capacity_plans
           GROUP BY resource_type
           ORDER BY avg_utilization DESC`
        )
        .all(),
      db
        .prepare(
          `SELECT priority, COUNT(*) as count
           FROM capacity_recommendations
           WHERE status = 'pending'
           GROUP BY priority`
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        utilization: utilization.results,
        pendingRecommendations: recommendations.results,
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminCapacityPlanningService = {
  listPlans,
  createPlan,
  getRecommendations,
  getDashboard,
};
