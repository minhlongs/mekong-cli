-- Migration 0046: Tenant Portal self-service tables
-- Tables: plan_change_requests, tenant_notification_settings

CREATE TABLE IF NOT EXISTS plan_change_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  current_tier TEXT NOT NULL,
  requested_tier TEXT NOT NULL,
  reason TEXT,
  status TEXT DEFAULT 'pending',
  auto_approved INTEGER DEFAULT 0,
  reviewed_by TEXT,
  reviewed_at TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_plan_changes_tenant ON plan_change_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_plan_changes_status ON plan_change_requests(status);

CREATE TABLE IF NOT EXISTS tenant_notification_settings (
  tenant_id TEXT PRIMARY KEY,
  billing_alerts INTEGER DEFAULT 1,
  usage_warnings INTEGER DEFAULT 1,
  product_updates INTEGER DEFAULT 1,
  weekly_digest INTEGER DEFAULT 0,
  updated_at TEXT DEFAULT (datetime('now'))
);
