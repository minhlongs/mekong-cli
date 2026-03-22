-- Migration: Tenant Performance Profiling
-- Stores per-endpoint latency profiles and baselines for alerting

CREATE TABLE IF NOT EXISTS performance_profiles (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  profile_name TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  avg_response_ms REAL,
  p95_response_ms REAL,
  p99_response_ms REAL,
  sample_count INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_performance_profiles_tenant ON performance_profiles(tenant_id);

CREATE TABLE IF NOT EXISTS performance_baselines (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  baseline_avg_ms REAL NOT NULL,
  baseline_p95_ms REAL,
  threshold_multiplier REAL NOT NULL DEFAULT 1.5,
  alert_enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_performance_baselines_tenant ON performance_baselines(tenant_id);
