-- Wave 25.3: White-Label / Custom Branding per Tenant
CREATE TABLE IF NOT EXISTS tenant_branding (
  tenant_id TEXT PRIMARY KEY,
  company_name TEXT NOT NULL DEFAULT 'Mekong RaaS',
  logo_url TEXT,
  favicon_url TEXT,
  primary_color TEXT NOT NULL DEFAULT '#2563eb',
  secondary_color TEXT NOT NULL DEFAULT '#1e40af',
  custom_domain TEXT UNIQUE,
  email_from_name TEXT,
  email_from_address TEXT,
  footer_text TEXT,
  support_url TEXT,
  powered_by_visible INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_branding_domain ON tenant_branding(custom_domain);
