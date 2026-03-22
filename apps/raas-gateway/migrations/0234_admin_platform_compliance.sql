-- Migration: admin platform compliance requirements and audits
-- Track regulatory compliance requirements and internal audit records

CREATE TABLE IF NOT EXISTS platform_compliance_requirements (
  id TEXT PRIMARY KEY,
  requirement_name TEXT NOT NULL,
  regulation TEXT NOT NULL,
  description TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  due_date TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_compliance_status ON platform_compliance_requirements(status);

CREATE TABLE IF NOT EXISTS platform_compliance_audits (
  id TEXT PRIMARY KEY,
  requirement_id TEXT NOT NULL,
  audit_type TEXT NOT NULL DEFAULT 'internal',
  findings TEXT,
  audited_by TEXT,
  audited_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_compliance_audits_req ON platform_compliance_audits(requirement_id);
