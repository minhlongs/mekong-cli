/**
 * Tenant Usage Alerts Service — alert rules and trigger history per tenant
 * Methods: listRules, createRule, getTriggers, getAdminOverview
 */

// Row shapes for D1 queries — avoids generic type args on .first()/.all()
type AlertRuleRow = {
  id: string; tenant_id: string; metric_name: string; threshold: number;
  comparison: string; notification_channel: string; is_active: number; created_at: string;
};

type AlertTriggerRow = {
  id: string; tenant_id: string; rule_id: string;
  current_value: number; triggered_at: string; acknowledged: number;
};

type AdminOverviewRow = {
  metric_name: string; trigger_count: number;
};

type AdminTenantCountRow = {
  tenants_with_rules: number;
};

export interface AlertRule {
  id: string;
  tenantId: string;
  metricName: string;
  threshold: number;
  comparison: string;
  notificationChannel: string;
  isActive: number;
  createdAt: string;
}

export interface AlertTrigger {
  id: string;
  tenantId: string;
  ruleId: string;
  currentValue: number;
  triggeredAt: string;
  acknowledged: number;
}

export interface AdminOverview {
  topTriggeredMetrics: { metricName: string; triggerCount: number }[];
  tenantsWithRules: number;
  totalActiveRules: number;
}

function mapRule(row: AlertRuleRow): AlertRule {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    metricName: row.metric_name,
    threshold: row.threshold,
    comparison: row.comparison,
    notificationChannel: row.notification_channel,
    isActive: row.is_active,
    createdAt: row.created_at,
  };
}

function mapTrigger(row: AlertTriggerRow): AlertTrigger {
  return {
    id: row.id,
    tenantId: row.tenant_id,
    ruleId: row.rule_id,
    currentValue: row.current_value,
    triggeredAt: row.triggered_at,
    acknowledged: row.acknowledged,
  };
}

export const tenantUsageAlertsService = {
  /** List all alert rules for a tenant, ordered by created_at DESC */
  async listRules(db: any, tenantId: string): Promise<AlertRule[]> {
    try {
      const result = await db
        .prepare('SELECT * FROM usage_alert_rules WHERE tenant_id = ? ORDER BY created_at DESC')
        .bind(tenantId)
        .all();
      return (result.results as AlertRuleRow[]).map(mapRule);
    } catch (err) {
      throw new Error(`listRules failed: ${String(err)}`);
    }
  },

  /** Create a new alert rule for a tenant */
  async createRule(
    db: any,
    tenantId: string,
    metricName: string,
    threshold: number,
    comparison: string,
    notificationChannel: string
  ): Promise<AlertRule> {
    try {
      const id = crypto.randomUUID();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO usage_alert_rules
             (id, tenant_id, metric_name, threshold, comparison, notification_channel, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)`
        )
        .bind(id, tenantId, metricName, threshold, comparison, notificationChannel, now)
        .run();
      const row = (await db
        .prepare('SELECT * FROM usage_alert_rules WHERE id = ?')
        .bind(id)
        .first()) as AlertRuleRow | null;
      if (!row) throw new Error('Row not found after insert');
      return mapRule(row);
    } catch (err) {
      throw new Error(`createRule failed: ${String(err)}`);
    }
  },

  /** Get trigger history for a tenant, most recent first */
  async getTriggers(db: any, tenantId: string, limit = 50): Promise<AlertTrigger[]> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM usage_alert_triggers WHERE tenant_id = ? ORDER BY triggered_at DESC LIMIT ?'
        )
        .bind(tenantId, limit)
        .all();
      return (result.results as AlertTriggerRow[]).map(mapTrigger);
    } catch (err) {
      throw new Error(`getTriggers failed: ${String(err)}`);
    }
  },

  /** Admin overview: top triggered metrics + tenant/rule counts across all tenants */
  async getAdminOverview(db: any): Promise<AdminOverview> {
    try {
      const [metricsResult, countRow, activeCountRow] = await Promise.all([
        db
          .prepare(
            `SELECT uar.metric_name, COUNT(uat.id) as trigger_count
             FROM usage_alert_triggers uat
             JOIN usage_alert_rules uar ON uat.rule_id = uar.id
             GROUP BY uar.metric_name
             ORDER BY trigger_count DESC
             LIMIT 10`
          )
          .all(),
        db
          .prepare(
            'SELECT COUNT(DISTINCT tenant_id) as tenants_with_rules FROM usage_alert_rules'
          )
          .first(),
        db
          .prepare('SELECT COUNT(*) as total FROM usage_alert_rules WHERE is_active = 1')
          .first(),
      ]);

      const metrics = metricsResult.results as AdminOverviewRow[];
      const counts = countRow as AdminTenantCountRow | null;
      const active = activeCountRow as { total: number } | null;

      return {
        topTriggeredMetrics: metrics.map(r => ({
          metricName: r.metric_name,
          triggerCount: r.trigger_count,
        })),
        tenantsWithRules: counts?.tenants_with_rules ?? 0,
        totalActiveRules: active?.total ?? 0,
      };
    } catch (err) {
      throw new Error(`getAdminOverview failed: ${String(err)}`);
    }
  },
};
