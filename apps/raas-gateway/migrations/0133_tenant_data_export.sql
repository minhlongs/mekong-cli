-- Wave 52: Tenant Data Export for RaaS Gateway
-- Creates data_export_requests and data_export_templates tables

CREATE TABLE IF NOT EXISTS data_export_requests (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  export_type TEXT NOT NULL,
  format TEXT DEFAULT 'json',
  filters_json TEXT DEFAULT '{}',
  status TEXT DEFAULT 'pending',
  file_url TEXT,
  file_size_bytes INTEGER,
  record_count INTEGER DEFAULT 0,
  requested_at TEXT DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  completed_at TEXT,
  expires_at TEXT,
  error TEXT
);

CREATE TABLE IF NOT EXISTS data_export_templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  export_type TEXT NOT NULL,
  default_filters_json TEXT DEFAULT '{}',
  default_format TEXT DEFAULT 'json',
  description TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_data_export_requests_tenant_id ON data_export_requests(tenant_id);
CREATE INDEX IF NOT EXISTS idx_data_export_requests_status ON data_export_requests(status);
CREATE INDEX IF NOT EXISTS idx_data_export_requests_export_type ON data_export_requests(export_type);

-- Seed export templates
INSERT OR IGNORE INTO data_export_templates (id, name, export_type, default_filters_json, default_format, description) VALUES
  ('tmpl_missions', 'Missions Export', 'missions', '{"limit":10000}', 'json', 'Export all mission records for the tenant'),
  ('tmpl_billing', 'Billing Export', 'billing', '{"include_transactions":true}', 'json', 'Export billing history and credit transactions'),
  ('tmpl_usage', 'Usage Analytics Export', 'usage', '{"period":"last_90_days"}', 'json', 'Export API usage logs and analytics data'),
  ('tmpl_team_members', 'Team Members Export', 'team_members', '{}', 'json', 'Export all team member records and roles'),
  ('tmpl_audit_logs', 'Audit Logs Export', 'audit_logs', '{"limit":50000}', 'json', 'Export complete audit trail for compliance');
