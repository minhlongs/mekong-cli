-- Admin Cost Optimization: recommendations + applied actions tracking
CREATE TABLE IF NOT EXISTS cost_optimization_recommendations (
  id TEXT PRIMARY KEY,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT,
  estimated_savings REAL,
  priority TEXT NOT NULL DEFAULT 'medium',
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cost_optimization_category ON cost_optimization_recommendations(category);

CREATE TABLE IF NOT EXISTS cost_optimization_actions (
  id TEXT PRIMARY KEY,
  recommendation_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  applied_by TEXT,
  applied_at TEXT,
  savings_realized REAL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cost_optimization_actions_rec ON cost_optimization_actions(recommendation_id);
