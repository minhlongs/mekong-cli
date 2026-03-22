-- Wave 60: Admin Capacity Planning for RaaS Gateway
-- Tables: capacity_plans, capacity_alerts

CREATE TABLE IF NOT EXISTS capacity_plans (
  id TEXT PRIMARY KEY,
  resource_type TEXT NOT NULL,
  current_usage REAL NOT NULL DEFAULT 0,
  max_capacity REAL NOT NULL DEFAULT 100,
  forecast_usage REAL,
  forecast_date TEXT,
  status TEXT NOT NULL DEFAULT 'normal',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS capacity_alerts (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  alert_type TEXT NOT NULL,
  threshold_percentage REAL NOT NULL,
  message TEXT NOT NULL,
  is_acknowledged INTEGER NOT NULL DEFAULT 0,
  triggered_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for capacity_plans
CREATE INDEX IF NOT EXISTS idx_capacity_plans_resource_type ON capacity_plans(resource_type);
CREATE INDEX IF NOT EXISTS idx_capacity_plans_status ON capacity_plans(status);

-- Indexes for capacity_alerts
CREATE INDEX IF NOT EXISTS idx_capacity_alerts_plan_id ON capacity_alerts(plan_id);
CREATE INDEX IF NOT EXISTS idx_capacity_alerts_is_acknowledged ON capacity_alerts(is_acknowledged);
