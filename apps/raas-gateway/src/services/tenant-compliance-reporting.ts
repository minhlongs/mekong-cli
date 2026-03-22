/**
 * Tenant Compliance Reporting Service
 * Manages compliance reports and rules per tenant
 */

export const tenantComplianceReportingService = {
  /** List all compliance reports for a tenant */
  async listReports(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM compliance_reports WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { reports: results };
    } catch (err) {
      console.error('[compliance] listReports error', err);
      throw err;
    }
  },

  /** Create a new compliance report for a tenant */
  async createReport(db: any, tenantId: string, data: Record<string, any>) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO compliance_reports
           (id, tenant_id, report_type, period_start, period_end, status, findings_count, report_data, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.report_type,
          data.period_start,
          data.period_end,
          data.status ?? 'draft',
          data.findings_count ?? 0,
          data.report_data ?? null,
          now,
          now
        )
        .run();
      return { id, tenant_id: tenantId, ...data, created_at: now, updated_at: now };
    } catch (err) {
      console.error('[compliance] createReport error', err);
      throw err;
    }
  },

  /** List all compliance rules for a tenant */
  async listRules(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare('SELECT * FROM compliance_rules WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return { rules: results };
    } catch (err) {
      console.error('[compliance] listRules error', err);
      throw err;
    }
  },

  /** Admin overview — counts of reports and rules across all tenants */
  async getAdminOverview(db: any) {
    try {
      const [reports, rules] = await Promise.all([
        db.prepare('SELECT COUNT(*) as count, status FROM compliance_reports GROUP BY status').all(),
        db.prepare('SELECT COUNT(*) as count, category FROM compliance_rules GROUP BY category').all(),
      ]);
      return {
        reports: reports.results,
        rules: rules.results,
      };
    } catch (err) {
      console.error('[compliance] getAdminOverview error', err);
      throw err;
    }
  },
};
