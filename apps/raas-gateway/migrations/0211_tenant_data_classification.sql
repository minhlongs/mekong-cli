-- Migration: Tenant data classification — field-level classification policies and scan results
-- Tracks data sensitivity classifications per tenant field path with scan history

CREATE TABLE IF NOT EXISTS data_classifications (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  field_path TEXT NOT NULL,
  classification_level TEXT NOT NULL DEFAULT 'internal',
  sensitivity TEXT NOT NULL DEFAULT 'low',
  handling_rules TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_classification_scans (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  classification_id TEXT NOT NULL,
  records_scanned INTEGER NOT NULL DEFAULT 0,
  findings_count INTEGER NOT NULL DEFAULT 0,
  scanned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_data_classifications_tenant_id
  ON data_classifications (tenant_id);

CREATE INDEX IF NOT EXISTS idx_data_classification_scans_tenant_id
  ON data_classification_scans (tenant_id);

CREATE INDEX IF NOT EXISTS idx_data_classification_scans_classification_id
  ON data_classification_scans (classification_id);
