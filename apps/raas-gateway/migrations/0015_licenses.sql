CREATE TABLE IF NOT EXISTS licenses (
  id TEXT PRIMARY KEY,
  license_key TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL CHECK(type IN ('personal', 'team', 'enterprise', 'oem')),
  owner_email TEXT,
  owner_name TEXT,
  max_activations INTEGER DEFAULT 1,
  current_activations INTEGER DEFAULT 0,
  status TEXT DEFAULT 'active' CHECK(status IN ('active', 'revoked', 'expired')),
  expires_at TEXT,
  metadata TEXT DEFAULT '{}',
  created_at TEXT DEFAULT (datetime('now')),
  activated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_licenses_key ON licenses(license_key);
CREATE INDEX IF NOT EXISTS idx_licenses_email ON licenses(owner_email);
