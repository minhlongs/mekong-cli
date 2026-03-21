-- Daily snapshots for trend tracking
CREATE TABLE IF NOT EXISTS analytics_snapshots (
  id TEXT PRIMARY KEY,
  snapshot_date TEXT NOT NULL,
  metric_type TEXT NOT NULL,
  metric_value REAL NOT NULL,
  metadata TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON analytics_snapshots(snapshot_date);
CREATE INDEX IF NOT EXISTS idx_snapshots_type ON analytics_snapshots(metric_type);
CREATE UNIQUE INDEX IF NOT EXISTS idx_snapshots_unique ON analytics_snapshots(snapshot_date, metric_type);

-- Churn risk cache (updated by scheduled handler)
CREATE TABLE IF NOT EXISTS churn_risk_cache (
  tenant_id TEXT PRIMARY KEY,
  risk_score INTEGER DEFAULT 0,
  risk_factors TEXT,
  last_active TEXT,
  calculated_at TEXT DEFAULT (datetime('now'))
);
