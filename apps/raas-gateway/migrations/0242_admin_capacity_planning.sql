-- Admin Capacity Planning: track resource utilization and scale recommendations
CREATE TABLE IF NOT EXISTS capacity_plans (
  id TEXT PRIMARY KEY,
  plan_name TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  current_usage REAL NOT NULL DEFAULT 0,
  max_capacity REAL NOT NULL,
  utilization_pct REAL,
  forecast_date TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_capacity_plans_resource ON capacity_plans(resource_type);

CREATE TABLE IF NOT EXISTS capacity_recommendations (
  id TEXT PRIMARY KEY,
  plan_id TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'medium',
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_capacity_recommendations_plan ON capacity_recommendations(plan_id);
