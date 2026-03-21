-- Platform KPI snapshots for admin dashboard — daily aggregated metrics
CREATE TABLE IF NOT EXISTS kpi_snapshots (
  id TEXT PRIMARY KEY,
  snapshot_date TEXT NOT NULL,
  mrr REAL DEFAULT 0,
  arr REAL DEFAULT 0,
  total_tenants INTEGER DEFAULT 0,
  active_tenants INTEGER DEFAULT 0,
  churned_tenants INTEGER DEFAULT 0,
  new_tenants INTEGER DEFAULT 0,
  total_missions INTEGER DEFAULT 0,
  total_revenue REAL DEFAULT 0,
  avg_revenue_per_tenant REAL DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_kpi_snapshots_date ON kpi_snapshots(snapshot_date);

-- Lifetime value calculations per tenant — churn risk and spend analytics
CREATE TABLE IF NOT EXISTS ltv_calculations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  lifetime_value REAL DEFAULT 0,
  months_active INTEGER DEFAULT 0,
  total_spent REAL DEFAULT 0,
  avg_monthly_spend REAL DEFAULT 0,
  churn_risk TEXT DEFAULT 'low' CHECK(churn_risk IN ('low','medium','high')),
  calculated_at TEXT DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_ltv_tenant ON ltv_calculations(tenant_id);
