/**
 * Admin Cost Optimization Service
 * CRUD for cost optimization recommendations and applied actions, plus dashboard aggregation
 */

/** List all recommendations, optionally filtered by category or status */
async function listRecommendations(
  db: any,
  filters: { category?: string; status?: string; priority?: string } = {}
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = 'SELECT * FROM cost_optimization_recommendations WHERE 1=1';
    const bindings: unknown[] = [];

    if (filters.category) { query += ' AND category = ?'; bindings.push(filters.category); }
    if (filters.status)   { query += ' AND status = ?';   bindings.push(filters.status); }
    if (filters.priority) { query += ' AND priority = ?'; bindings.push(filters.priority); }

    query += ' ORDER BY created_at DESC';

    const { results } = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/** Create a new cost optimization recommendation */
async function createRecommendation(
  db: any,
  input: {
    category: string;
    title: string;
    description?: string;
    estimated_savings?: number;
    priority?: string;
    status?: string;
  }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();

    await db
      .prepare(
        `INSERT INTO cost_optimization_recommendations
         (id, category, title, description, estimated_savings, priority, status, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        input.category,
        input.title,
        input.description ?? null,
        input.estimated_savings ?? null,
        input.priority ?? 'medium',
        input.status ?? 'pending',
        now
      )
      .run();

    const row = await db
      .prepare('SELECT * FROM cost_optimization_recommendations WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: row };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/** List actions, optionally filtered by recommendation_id */
async function getActions(
  db: any,
  filters: { recommendation_id?: string; action_type?: string } = {}
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = 'SELECT * FROM cost_optimization_actions WHERE 1=1';
    const bindings: unknown[] = [];

    if (filters.recommendation_id) { query += ' AND recommendation_id = ?'; bindings.push(filters.recommendation_id); }
    if (filters.action_type)       { query += ' AND action_type = ?';        bindings.push(filters.action_type); }

    query += ' ORDER BY created_at DESC';

    const { results } = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: results };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

/** Aggregated dashboard: total savings, counts by status/priority/category */
async function getDashboard(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const [byStatus, byPriority, byCategory, actionStats] = await Promise.all([
      db
        .prepare('SELECT status, COUNT(*) as count FROM cost_optimization_recommendations GROUP BY status')
        .all(),
      db
        .prepare('SELECT priority, COUNT(*) as count FROM cost_optimization_recommendations GROUP BY priority')
        .all(),
      db
        .prepare(
          'SELECT category, COUNT(*) as count, SUM(estimated_savings) as total_estimated FROM cost_optimization_recommendations GROUP BY category'
        )
        .all(),
      db
        .prepare(
          'SELECT COUNT(*) as total_actions, SUM(savings_realized) as total_savings_realized FROM cost_optimization_actions'
        )
        .first(),
    ]);

    const totalEstimated = await db
      .prepare('SELECT SUM(estimated_savings) as total FROM cost_optimization_recommendations')
      .first();

    return {
      success: true,
      data: {
        by_status: byStatus.results,
        by_priority: byPriority.results,
        by_category: byCategory.results,
        total_estimated_savings: totalEstimated?.total ?? 0,
        total_actions: actionStats?.total_actions ?? 0,
        total_savings_realized: actionStats?.total_savings_realized ?? 0,
      },
    };
  } catch (err) {
    return { success: false, error: String(err) };
  }
}

export const adminCostOptimizationService = {
  listRecommendations,
  createRecommendation,
  getActions,
  getDashboard,
};
