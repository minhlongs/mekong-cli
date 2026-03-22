/**
 * Admin platform usage report service
 * Handles CRUD for platform_usage_reports and platform_usage_report_sections tables
 */

// List all platform usage reports, ordered by most recent first
async function listReports(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM platform_usage_reports ORDER BY generated_at DESC')
      .all();
    return { success: true, data: result.results };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to list reports' };
  }
}

// Create a new platform usage report row
async function createReport(
  db: any,
  payload: {
    id: string;
    report_name: string;
    period: string;
    total_tenants?: number;
    total_missions?: number;
    total_api_calls?: number;
    revenue?: number;
  }
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const { id, report_name, period, total_tenants = 0, total_missions = 0, total_api_calls = 0, revenue = 0 } = payload;
    await db
      .prepare(
        `INSERT INTO platform_usage_reports
           (id, report_name, period, total_tenants, total_missions, total_api_calls, revenue)
         VALUES (?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, report_name, period, total_tenants, total_missions, total_api_calls, revenue)
      .run();
    const created = await db
      .prepare('SELECT * FROM platform_usage_reports WHERE id = ?')
      .bind(id)
      .first();
    return { success: true, data: created };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to create report' };
  }
}

// Get all sections for a given report_id, ordered by display_order
async function getSections(
  db: any,
  reportId: string
): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const result = await db
      .prepare(
        'SELECT * FROM platform_usage_report_sections WHERE report_id = ? ORDER BY display_order ASC'
      )
      .bind(reportId)
      .all();
    return { success: true, data: result.results };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to get sections' };
  }
}

// Dashboard: aggregate totals across all reports and count reports per period
async function getDashboard(db: any): Promise<{ success: boolean; data?: any; error?: string }> {
  try {
    const [totals, byPeriod, recentReports] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total_reports,
             COALESCE(SUM(total_tenants), 0) as sum_tenants,
             COALESCE(SUM(total_missions), 0) as sum_missions,
             COALESCE(SUM(total_api_calls), 0) as sum_api_calls,
             COALESCE(SUM(revenue), 0) as sum_revenue
           FROM platform_usage_reports`
        )
        .first(),
      db
        .prepare(
          `SELECT period, COUNT(*) as report_count
           FROM platform_usage_reports
           GROUP BY period
           ORDER BY period DESC`
        )
        .all(),
      db
        .prepare(
          'SELECT * FROM platform_usage_reports ORDER BY generated_at DESC LIMIT 5'
        )
        .all(),
    ]);

    return {
      success: true,
      data: {
        totals,
        byPeriod: byPeriod.results,
        recentReports: recentReports.results,
      },
    };
  } catch (err: any) {
    return { success: false, error: err?.message ?? 'Failed to get dashboard' };
  }
}

export const adminPlatformUsageReportService = {
  listReports,
  createReport,
  getSections,
  getDashboard,
};
