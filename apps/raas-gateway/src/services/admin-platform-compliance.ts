/**
 * Admin platform compliance service — CRUD for compliance requirements and audits
 * All functions take db as first param (D1Database), return { success, data/error }
 */

// List all compliance requirements, optionally filtered by status
async function listRequirements(db: any, status?: string) {
  try {
    let query = 'SELECT * FROM platform_compliance_requirements';
    const params: any[] = [];

    if (status) {
      query += ' WHERE status = ?';
      params.push(status);
    }

    query += ' ORDER BY created_at DESC';

    const result = await db.prepare(query).bind(...params).all();
    return { success: true, data: result.results };
  } catch (error: any) {
    return { success: false, error: error.message ?? 'Failed to list requirements' };
  }
}

// Create a new compliance requirement
async function createRequirement(db: any, body: {
  id: string;
  requirement_name: string;
  regulation: string;
  description?: string;
  status?: string;
  due_date?: string;
}) {
  try {
    const { id, requirement_name, regulation, description, status, due_date } = body;

    await db.prepare(
      `INSERT INTO platform_compliance_requirements
        (id, requirement_name, regulation, description, status, due_date)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(
      id,
      requirement_name,
      regulation,
      description ?? null,
      status ?? 'pending',
      due_date ?? null
    ).run();

    const created = await db
      .prepare('SELECT * FROM platform_compliance_requirements WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (error: any) {
    return { success: false, error: error.message ?? 'Failed to create requirement' };
  }
}

// Get all audits for a specific requirement
async function getAudits(db: any, requirement_id?: string) {
  try {
    let query = 'SELECT * FROM platform_compliance_audits';
    const params: any[] = [];

    if (requirement_id) {
      query += ' WHERE requirement_id = ?';
      params.push(requirement_id);
    }

    query += ' ORDER BY audited_at DESC';

    const result = await db.prepare(query).bind(...params).all();
    return { success: true, data: result.results };
  } catch (error: any) {
    return { success: false, error: error.message ?? 'Failed to get audits' };
  }
}

// Dashboard: aggregate compliance status summary
async function getDashboard(db: any) {
  try {
    const [statusCounts, overdue, recentAudits] = await Promise.all([
      // Count requirements grouped by status
      db.prepare(
        `SELECT status, COUNT(*) as count
         FROM platform_compliance_requirements
         GROUP BY status`
      ).all(),
      // Count overdue requirements (past due_date, not completed)
      db.prepare(
        `SELECT COUNT(*) as count
         FROM platform_compliance_requirements
         WHERE due_date IS NOT NULL
           AND due_date < date('now')
           AND status != 'completed'`
      ).first(),
      // 5 most recent audits
      db.prepare(
        `SELECT a.*, r.requirement_name, r.regulation
         FROM platform_compliance_audits a
         LEFT JOIN platform_compliance_requirements r ON r.id = a.requirement_id
         ORDER BY a.audited_at DESC
         LIMIT 5`
      ).all(),
    ]);

    const summary: Record<string, number> = {};
    for (const row of statusCounts.results as any[]) {
      summary[row.status] = row.count;
    }

    return {
      success: true,
      data: {
        statusSummary: summary,
        overdueCount: (overdue as any)?.count ?? 0,
        recentAudits: recentAudits.results,
      },
    };
  } catch (error: any) {
    return { success: false, error: error.message ?? 'Failed to get dashboard' };
  }
}

export const adminPlatformComplianceService = {
  listRequirements,
  createRequirement,
  getAudits,
  getDashboard,
};
