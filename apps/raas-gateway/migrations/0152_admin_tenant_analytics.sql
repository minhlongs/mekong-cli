-- Wave 58: Admin Tenant Analytics for RaaS Gateway
-- Tables: tenant_health_scores, tenant_usage_trends, tenant_risk_indicators

CREATE TABLE IF NOT EXISTS tenant_health_scores (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  score INTEGER DEFAULT 100,
  risk_level TEXT DEFAULT 'low',
  factors_json TEXT DEFAULT '{}',
  calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_usage_trends (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  missions_count INTEGER DEFAULT 0,
  api_calls INTEGER DEFAULT 0,
  credits_used INTEGER DEFAULT 0,
  revenue_cents INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tenant_risk_indicators (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  indicator_type TEXT NOT NULL,
  severity TEXT DEFAULT 'low',
  description TEXT,
  resolved INTEGER DEFAULT 0,
  detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT
);

-- Indexes for tenant_health_scores
CREATE INDEX IF NOT EXISTS idx_tenant_health_scores_tenant_id ON tenant_health_scores(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_health_scores_risk_level ON tenant_health_scores(risk_level);

-- Indexes for tenant_usage_trends
CREATE INDEX IF NOT EXISTS idx_tenant_usage_trends_tenant_id ON tenant_usage_trends(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_trends_period ON tenant_usage_trends(period);

-- Indexes for tenant_risk_indicators
CREATE INDEX IF NOT EXISTS idx_tenant_risk_indicators_tenant_id ON tenant_risk_indicators(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_risk_indicators_indicator_type ON tenant_risk_indicators(indicator_type);
CREATE INDEX IF NOT EXISTS idx_tenant_risk_indicators_severity ON tenant_risk_indicators(severity);
