-- Migration 0088: Custom domains for enterprise white-label branding
-- Allows tenants to configure custom API domains with DNS verification

CREATE TABLE IF NOT EXISTS custom_domains (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  domain TEXT NOT NULL UNIQUE,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, verifying, active, failed
  verification_method TEXT DEFAULT 'cname', -- cname, txt
  verification_token TEXT,
  ssl_status TEXT DEFAULT 'pending', -- pending, active, failed
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  verified_at TEXT,
  expires_at TEXT
);

CREATE INDEX idx_custom_domains_tenant ON custom_domains(tenant_id);
CREATE INDEX idx_custom_domains_domain ON custom_domains(domain);
CREATE INDEX idx_custom_domains_status ON custom_domains(status);
