// Platform Compliance Audit Service — SOC2/compliance check management and result tracking

export const platformComplianceAuditService = {

  /** List all active compliance checks */
  async listChecks(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM compliance_checks WHERE is_active = 1 ORDER BY category, severity, check_name`
      ).all();
      return (rows.results as unknown[]);
    } catch (e: unknown) {
      throw new Error(`listChecks failed: ${(e as Error).message}`);
    }
  },

  /** Create a new compliance check definition */
  async createCheck(db: any, data: {
    check_name: string;
    category: string;
    standard?: string;
    severity?: string;
    check_query: string;
    is_active?: number;
  }): Promise<unknown> {
    try {
      return db.prepare(
        `INSERT INTO compliance_checks
           (id, check_name, category, standard, severity, check_query, is_active, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
         RETURNING *`
      ).bind(
        crypto.randomUUID(),
        data.check_name,
        data.category,
        data.standard ?? 'SOC2',
        data.severity ?? 'medium',
        data.check_query,
        data.is_active ?? 1
      ).first();
    } catch (e: unknown) {
      throw new Error(`createCheck failed: ${(e as Error).message}`);
    }
  },

  /** Get results for a specific check or all recent results */
  async getResults(db: any, checkId?: string): Promise<unknown[]> {
    try {
      const rows = checkId
        ? await db.prepare(
            `SELECT r.*, c.check_name, c.category, c.severity
             FROM compliance_results r
             JOIN compliance_checks c ON c.id = r.check_id
             WHERE r.check_id = ?
             ORDER BY r.checked_at DESC LIMIT 100`
          ).bind(checkId).all()
        : await db.prepare(
            `SELECT r.*, c.check_name, c.category, c.severity
             FROM compliance_results r
             JOIN compliance_checks c ON c.id = r.check_id
             ORDER BY r.checked_at DESC LIMIT 200`
          ).all();
      return (rows.results as unknown[]);
    } catch (e: unknown) {
      throw new Error(`getResults failed: ${(e as Error).message}`);
    }
  },

  /** Dashboard summary — counts by status and severity */
  async getDashboard(db: any): Promise<unknown> {
    try {
      const [totalChecks, activeChecks, passFail, bySeverity] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM compliance_checks`).first() as Promise<{ count: number } | null>,
        db.prepare(`SELECT COUNT(*) as count FROM compliance_checks WHERE is_active = 1`).first() as Promise<{ count: number } | null>,
        db.prepare(
          `SELECT status, COUNT(*) as count FROM compliance_results GROUP BY status`
        ).all(),
        db.prepare(
          `SELECT c.severity, COUNT(*) as total,
                  SUM(CASE WHEN r.status = 'pass' THEN 1 ELSE 0 END) as passed
           FROM compliance_checks c
           LEFT JOIN compliance_results r ON r.check_id = c.id
           GROUP BY c.severity`
        ).all(),
      ]);
      return {
        total_checks: (totalChecks as { count: number } | null)?.count ?? 0,
        active_checks: (activeChecks as { count: number } | null)?.count ?? 0,
        results_by_status: (passFail.results as unknown[]),
        results_by_severity: (bySeverity.results as unknown[]),
      };
    } catch (e: unknown) {
      throw new Error(`getDashboard failed: ${(e as Error).message}`);
    }
  },
};
