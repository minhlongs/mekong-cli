-- Migration: Tenant Data Masking
CREATE TABLE IF NOT EXISTS data_masking_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  field_pattern TEXT NOT NULL,
  masking_type TEXT NOT NULL DEFAULT 'redact',
  replacement_value TEXT DEFAULT '***',
  applies_to TEXT DEFAULT 'all',
  is_active INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_data_masking_tenant ON data_masking_policies(tenant_id);

CREATE TABLE IF NOT EXISTS data_masking_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  fields_masked INTEGER NOT NULL DEFAULT 0,
  request_path TEXT,
  masked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_data_masking_events_tenant ON data_masking_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_data_masking_events_policy ON data_masking_events(policy_id);
