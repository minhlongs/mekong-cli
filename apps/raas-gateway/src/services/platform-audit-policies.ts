// Platform Audit Policies Service — manage audit policies and violations

export const platformAuditPoliciesService = {
  /** List all audit policies */
  async listPolicies(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM audit_policies ORDER BY created_at DESC`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`listPolicies failed: ${(e as Error).message}`);
    }
  },

  /** Create a new audit policy */
  async createPolicy(db: any, data: {
    policy_name: string;
    description?: string;
    event_types?: string;
    retention_days?: number;
    is_active?: number;
  }): Promise<unknown> {
    try {
      const id = crypto.randomUUID();
      const result = await db.prepare(
        `INSERT INTO audit_policies
           (id, policy_name, description, event_types, retention_days, is_active)
         VALUES (?, ?, ?, ?, ?, ?)
         RETURNING *`
      ).bind(
        id,
        data.policy_name,
        data.description ?? null,
        data.event_types ?? null,
        data.retention_days ?? 365,
        data.is_active ?? 1
      ).first();
      return result;
    } catch (e: unknown) {
      throw new Error(`createPolicy failed: ${(e as Error).message}`);
    }
  },

  /** List all audit policy violations */
  async getViolations(db: any): Promise<unknown[]> {
    try {
      const rows = await db.prepare(
        `SELECT * FROM audit_policy_violations ORDER BY created_at DESC`
      ).all();
      return rows.results;
    } catch (e: unknown) {
      throw new Error(`getViolations failed: ${(e as Error).message}`);
    }
  },

  /** Get dashboard stats for audit policies and violations */
  async getDashboard(db: any): Promise<unknown> {
    try {
      const [totalPolicies, activePolicies, totalViolations, unresolvedViolations] =
        await Promise.all([
          db.prepare(`SELECT COUNT(*) as count FROM audit_policies`).first(),
          db.prepare(`SELECT COUNT(*) as count FROM audit_policies WHERE is_active = 1`).first(),
          db.prepare(`SELECT COUNT(*) as count FROM audit_policy_violations`).first(),
          db.prepare(`SELECT COUNT(*) as count FROM audit_policy_violations WHERE resolved = 0`).first(),
        ]);

      const bySeverity = await db.prepare(
        `SELECT severity, COUNT(*) as count
         FROM audit_policy_violations
         GROUP BY severity`
      ).all();

      return {
        policies: {
          total: totalPolicies?.count ?? 0,
          active: activePolicies?.count ?? 0,
        },
        violations: {
          total: totalViolations?.count ?? 0,
          unresolved: unresolvedViolations?.count ?? 0,
          by_severity: bySeverity.results,
        },
      };
    } catch (e: unknown) {
      throw new Error(`getDashboard failed: ${(e as Error).message}`);
    }
  },
};
