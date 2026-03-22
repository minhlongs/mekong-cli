-- Platform License Management — tracks licenses and activations
CREATE TABLE IF NOT EXISTS platform_licenses (
  id TEXT PRIMARY KEY,
  license_key TEXT NOT NULL UNIQUE,
  tenant_id TEXT,
  license_type TEXT NOT NULL DEFAULT 'standard',
  features_json TEXT DEFAULT '{}',
  max_users INTEGER DEFAULT 10,
  status TEXT NOT NULL DEFAULT 'active',
  issued_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  expires_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_platform_licenses_tenant ON platform_licenses(tenant_id);
CREATE INDEX IF NOT EXISTS idx_platform_licenses_key ON platform_licenses(license_key);

CREATE TABLE IF NOT EXISTS license_activations (
  id TEXT PRIMARY KEY,
  license_id TEXT NOT NULL,
  activated_by TEXT,
  machine_fingerprint TEXT,
  ip_address TEXT,
  activated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_license_activations_license ON license_activations(license_id);
