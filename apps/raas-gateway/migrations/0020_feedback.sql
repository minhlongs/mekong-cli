-- Migration 0020: Tenant feedback and churn survey responses
CREATE TABLE IF NOT EXISTS tenant_feedback (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  type TEXT NOT NULL, -- 'churn', 'feature_request', 'bug', 'general'
  message TEXT,
  previous_tier TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
