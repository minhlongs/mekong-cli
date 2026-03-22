-- Migration: Mission Retry Policies
-- Tables for configuring retry behavior on missions and tracking retry attempts

CREATE TABLE IF NOT EXISTS retry_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_name TEXT NOT NULL,
  max_retries INTEGER NOT NULL DEFAULT 3,
  backoff_type TEXT NOT NULL DEFAULT 'exponential',
  initial_delay_ms INTEGER NOT NULL DEFAULT 1000,
  max_delay_ms INTEGER NOT NULL DEFAULT 60000,
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_retry_policies_tenant_id ON retry_policies (tenant_id);

CREATE TABLE IF NOT EXISTS retry_attempts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  attempt_number INTEGER NOT NULL,
  status TEXT NOT NULL,
  error_message TEXT,
  next_retry_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_retry_attempts_tenant_id ON retry_attempts (tenant_id);
