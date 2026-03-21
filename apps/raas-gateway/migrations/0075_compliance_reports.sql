-- Migration 0075: Compliance Reports tables
-- Stores SOC2/GDPR/HIPAA/PCI compliance reports and check results

CREATE TABLE IF NOT EXISTS compliance_reports (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  report_type TEXT NOT NULL, -- soc2, gdpr, hipaa, pci, custom
  title TEXT NOT NULL,
  status TEXT DEFAULT 'generating', -- generating, ready, expired
  report_data TEXT, -- JSON report content
  coverage_start TEXT NOT NULL,
  coverage_end TEXT NOT NULL,
  generated_at TEXT DEFAULT (datetime('now')),
  expires_at TEXT,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_compliance_tenant ON compliance_reports(tenant_id);
CREATE INDEX IF NOT EXISTS idx_compliance_type ON compliance_reports(report_type);

CREATE TABLE IF NOT EXISTS compliance_checks (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  check_type TEXT NOT NULL, -- data_encryption, access_control, audit_logging, data_retention, incident_response
  category TEXT NOT NULL, -- soc2, gdpr, hipaa
  status TEXT DEFAULT 'unknown', -- pass, fail, warning, unknown
  details TEXT, -- JSON details
  checked_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);

CREATE INDEX IF NOT EXISTS idx_compliance_check_tenant ON compliance_checks(tenant_id);
