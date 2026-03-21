-- Migration: 0034_tenant_health.sql
-- Tenant health scoring table — tracks score history per tenant

CREATE TABLE IF NOT EXISTS tenant_health_scores (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  tenant_id TEXT NOT NULL,
  score INTEGER NOT NULL DEFAULT 100,
  factors TEXT NOT NULL DEFAULT '{}',
  risk_level TEXT NOT NULL DEFAULT 'low',
  calculated_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX idx_health_tenant ON tenant_health_scores(tenant_id, calculated_at);
