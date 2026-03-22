-- Migration: Platform tenant scoring — health, engagement, revenue, and overall scores
-- Tracks current scores per tenant and historical score snapshots over time

CREATE TABLE IF NOT EXISTS tenant_scores (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  health_score REAL DEFAULT 0,
  engagement_score REAL DEFAULT 0,
  revenue_score REAL DEFAULT 0,
  overall_score REAL DEFAULT 0,
  tier TEXT DEFAULT 'standard',
  last_calculated TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_score_history (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  overall_score REAL NOT NULL,
  factors_json TEXT DEFAULT '{}',
  recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_tenant_scores_tenant_id
  ON tenant_scores (tenant_id);

CREATE INDEX IF NOT EXISTS idx_tenant_scores_overall_score
  ON tenant_scores (overall_score);

CREATE INDEX IF NOT EXISTS idx_tenant_score_history_tenant_id
  ON tenant_score_history (tenant_id);

CREATE INDEX IF NOT EXISTS idx_tenant_score_history_overall_score
  ON tenant_score_history (overall_score);
