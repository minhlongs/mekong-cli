-- Tenant custom domains: allow tenants to map their own domains to the platform
CREATE TABLE IF NOT EXISTS tenant_custom_domains (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  domain TEXT NOT NULL,
  ssl_status TEXT NOT NULL DEFAULT 'pending',
  verified INTEGER NOT NULL DEFAULT 0,
  dns_record TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_custom_domains_tenant ON tenant_custom_domains(tenant_id);

-- Domain ownership verification records
CREATE TABLE IF NOT EXISTS tenant_domain_verifications (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  domain_id TEXT NOT NULL,
  verification_type TEXT NOT NULL DEFAULT 'dns',
  verification_token TEXT,
  verified_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tenant_domain_verifications_domain ON tenant_domain_verifications(domain_id);
