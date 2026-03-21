-- Migration: 0073_error_budgets
-- Created: 2026-03-21
-- Description: SLO/SLI Error Budget Tracking — define SLOs, record measurements, track budget consumption and alerts

CREATE TABLE IF NOT EXISTS slo_definitions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,       -- e.g., "Mission Success Rate", "API Latency p99"
  slo_type TEXT NOT NULL,   -- availability, latency, error_rate, throughput
  target_value REAL NOT NULL, -- e.g., 99.9 (percent), 500 (ms)
  window_days INTEGER DEFAULT 30,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_slo_tenant ON slo_definitions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_slo_active ON slo_definitions(tenant_id, is_active);

CREATE TABLE IF NOT EXISTS sli_measurements (
  id TEXT PRIMARY KEY,
  slo_id TEXT NOT NULL,
  measured_value REAL NOT NULL,
  good_events INTEGER DEFAULT 0,
  total_events INTEGER DEFAULT 0,
  measured_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (slo_id) REFERENCES slo_definitions(id)
);

CREATE INDEX IF NOT EXISTS idx_sli_slo ON sli_measurements(slo_id);
CREATE INDEX IF NOT EXISTS idx_sli_measured ON sli_measurements(measured_at);
CREATE INDEX IF NOT EXISTS idx_sli_slo_measured ON sli_measurements(slo_id, measured_at);

CREATE TABLE IF NOT EXISTS error_budget_alerts (
  id TEXT PRIMARY KEY,
  slo_id TEXT NOT NULL,
  alert_type TEXT NOT NULL,   -- warning (50% consumed), critical (80% consumed), exhausted (100%)
  budget_remaining REAL,
  message TEXT,
  acknowledged INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (slo_id) REFERENCES slo_definitions(id)
);

CREATE INDEX IF NOT EXISTS idx_budget_alert_slo ON error_budget_alerts(slo_id);
CREATE INDEX IF NOT EXISTS idx_budget_alert_ack ON error_budget_alerts(slo_id, acknowledged);
CREATE INDEX IF NOT EXISTS idx_budget_alert_created ON error_budget_alerts(created_at);
