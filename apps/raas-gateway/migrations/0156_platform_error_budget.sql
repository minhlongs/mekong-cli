-- Wave 59: Platform Error Budget — cross-service SLO budget tracking
-- Tables: error_budgets, error_budget_events

CREATE TABLE IF NOT EXISTS error_budgets (
  id TEXT PRIMARY KEY,
  service_name TEXT NOT NULL,
  slo_target REAL DEFAULT 99.9,
  budget_remaining REAL DEFAULT 100.0,
  window_days INTEGER DEFAULT 30,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS error_budget_events (
  id TEXT PRIMARY KEY,
  budget_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  error_count INTEGER DEFAULT 0,
  total_requests INTEGER DEFAULT 0,
  impact_percentage REAL,
  recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for error_budgets
CREATE INDEX IF NOT EXISTS idx_error_budgets_service_name ON error_budgets(service_name);
CREATE INDEX IF NOT EXISTS idx_error_budgets_is_active ON error_budgets(is_active);

-- Indexes for error_budget_events
CREATE INDEX IF NOT EXISTS idx_error_budget_events_budget_id ON error_budget_events(budget_id);
CREATE INDEX IF NOT EXISTS idx_error_budget_events_recorded_at ON error_budget_events(recorded_at);
