-- Migration: Tenant API deprecation notices and acknowledgements
-- Tracks deprecated endpoints, sunset dates, and tenant acknowledgements

CREATE TABLE IF NOT EXISTS api_deprecation_notices (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  endpoint TEXT NOT NULL,
  deprecation_date TEXT,
  sunset_date TEXT,
  replacement_endpoint TEXT,
  message TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_deprecation_acknowledgements (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  notice_id TEXT,
  acknowledged_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_api_deprecation_notices_tenant_id
  ON api_deprecation_notices (tenant_id);

CREATE INDEX IF NOT EXISTS idx_api_deprecation_acknowledgements_tenant_id
  ON api_deprecation_acknowledgements (tenant_id);

CREATE INDEX IF NOT EXISTS idx_api_deprecation_acknowledgements_notice_id
  ON api_deprecation_acknowledgements (notice_id);
