-- Wave 59: Tenant Data Retention Policies for RaaS Gateway
-- Tables: data_retention_policies, data_retention_runs

CREATE TABLE IF NOT EXISTS data_retention_policies (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  retention_days INTEGER NOT NULL,
  action TEXT DEFAULT 'archive',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS data_retention_runs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  records_processed INTEGER DEFAULT 0,
  records_affected INTEGER DEFAULT 0,
  started_at TEXT,
  completed_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for data_retention_policies
CREATE INDEX IF NOT EXISTS idx_data_retention_policies_tenant_id ON data_retention_policies(tenant_id);

-- Indexes for data_retention_runs
CREATE INDEX IF NOT EXISTS idx_data_retention_runs_tenant_id ON data_retention_runs(tenant_id);
