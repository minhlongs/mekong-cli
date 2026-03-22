-- Migration: Tenant Usage Quotas Management
-- Tracks per-tenant resource quotas and threshold alerts

CREATE TABLE IF NOT EXISTS usage_quotas (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  quota_limit INTEGER NOT NULL,
  current_usage INTEGER NOT NULL DEFAULT 0,
  period TEXT NOT NULL DEFAULT 'monthly',
  reset_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_quotas_tenant ON usage_quotas(tenant_id);

CREATE TABLE IF NOT EXISTS usage_quota_alerts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  quota_id TEXT NOT NULL,
  alert_threshold REAL NOT NULL DEFAULT 0.8,
  notification_sent INTEGER NOT NULL DEFAULT 0,
  triggered_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_usage_quota_alerts_tenant ON usage_quota_alerts(tenant_id);
