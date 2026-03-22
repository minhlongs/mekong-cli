-- Migration: mission_completion_certificates
-- Stores certificates issued upon mission completion and their templates

CREATE TABLE IF NOT EXISTS mission_completion_certificates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  certificate_number TEXT NOT NULL,
  issued_to TEXT NOT NULL,
  issued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT,
  verification_hash TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_completion_certificates_tenant ON mission_completion_certificates(tenant_id);

CREATE TABLE IF NOT EXISTS mission_certificate_templates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  template_name TEXT NOT NULL,
  template_html TEXT,
  logo_url TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_mission_certificate_templates_tenant ON mission_certificate_templates(tenant_id);
