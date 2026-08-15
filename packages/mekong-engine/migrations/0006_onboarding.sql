CREATE TABLE IF NOT EXISTS tenant_profiles (
  tenant_id TEXT PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
  business_name TEXT NOT NULL, industry TEXT NOT NULL DEFAULT 'cafe', address TEXT, phone TEXT, hours TEXT,
  logo_url TEXT, menu_data JSON, onboarding_step INTEGER DEFAULT 0, onboarding_completed INTEGER DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')), updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
