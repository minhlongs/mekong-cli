-- Wave 60: Tenant Compliance Reporting
-- Tables: compliance_reports, compliance_rules

CREATE TABLE IF NOT EXISTS compliance_reports (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  report_type TEXT NOT NULL,
  period_start TEXT NOT NULL,
  period_end TEXT NOT NULL,
  status TEXT DEFAULT 'draft',
  findings_count INTEGER DEFAULT 0,
  report_data TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS compliance_rules (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  rule_name TEXT NOT NULL,
  category TEXT NOT NULL,
  severity TEXT DEFAULT 'medium',
  is_active INTEGER DEFAULT 1,
  check_query TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tenant-scoped queries
CREATE INDEX IF NOT EXISTS idx_compliance_reports_tenant_id ON compliance_reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_compliance_rules_tenant_id ON compliance_rules(tenant_id);
