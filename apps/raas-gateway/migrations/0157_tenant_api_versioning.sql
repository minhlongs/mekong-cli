-- Wave 60: Tenant API Versioning for RaaS Gateway
-- Tables: api_versions, api_version_mappings

CREATE TABLE IF NOT EXISTS api_versions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  version_label TEXT NOT NULL,
  base_url TEXT NOT NULL,
  is_default INTEGER DEFAULT 0,
  is_deprecated INTEGER DEFAULT 0,
  deprecation_date TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_version_mappings (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  version_id TEXT NOT NULL,
  endpoint_pattern TEXT NOT NULL,
  target_handler TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for api_versions
CREATE INDEX IF NOT EXISTS idx_api_versions_tenant_id ON api_versions(tenant_id);

-- Indexes for api_version_mappings
CREATE INDEX IF NOT EXISTS idx_api_version_mappings_tenant_id ON api_version_mappings(tenant_id);
