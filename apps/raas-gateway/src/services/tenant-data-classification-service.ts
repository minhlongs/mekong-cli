/**
 * Tenant Data Classification Service
 * Manages field-level data classification policies and scan results per tenant
 */

export const tenantDataClassificationService = {
  /** List all classifications for a tenant */
  async listClassifications(db: any, tenantId: string) {
    try {
      const { results } = await db
        .prepare(
          'SELECT * FROM data_classifications WHERE tenant_id = ? ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all();
      return { classifications: results as any[] };
    } catch (err) {
      console.error('[data-classification] listClassifications error', err);
      throw err;
    }
  },

  /** Create a new data classification for a tenant */
  async createClassification(db: any, tenantId: string, data: Record<string, any>) {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO data_classifications
           (id, tenant_id, field_path, classification_level, sensitivity, handling_rules, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.field_path,
          data.classification_level ?? 'internal',
          data.sensitivity ?? 'low',
          typeof data.handling_rules === 'object'
            ? JSON.stringify(data.handling_rules)
            : (data.handling_rules ?? '{}'),
          now,
          now
        )
        .run();
      const row = await db
        .prepare('SELECT * FROM data_classifications WHERE id = ?')
        .bind(id)
        .first();
      return { classification: row as any };
    } catch (err) {
      console.error('[data-classification] createClassification error', err);
      throw err;
    }
  },

  /** List scan results for a tenant, optionally filtered by classification */
  async getScans(db: any, tenantId: string, classificationId?: string) {
    try {
      let query = 'SELECT * FROM data_classification_scans WHERE tenant_id = ?';
      const bindings: any[] = [tenantId];
      if (classificationId) {
        query += ' AND classification_id = ?';
        bindings.push(classificationId);
      }
      query += ' ORDER BY scanned_at DESC LIMIT 100';
      const { results } = await db
        .prepare(query)
        .bind(...bindings)
        .all();
      return { scans: results as any[] };
    } catch (err) {
      console.error('[data-classification] getScans error', err);
      throw err;
    }
  },

  /** Admin overview — classification and scan counts across all tenants */
  async getAdminOverview(db: any) {
    try {
      const [classifications, scans] = await Promise.all([
        db
          .prepare(
            'SELECT COUNT(*) as count, classification_level FROM data_classifications GROUP BY classification_level'
          )
          .all(),
        db
          .prepare(
            'SELECT COUNT(*) as count, tenant_id FROM data_classification_scans GROUP BY tenant_id'
          )
          .all(),
      ]);
      return {
        classifications: classifications.results as any[],
        scans: scans.results as any[],
      };
    } catch (err) {
      console.error('[data-classification] getAdminOverview error', err);
      throw err;
    }
  },
};
