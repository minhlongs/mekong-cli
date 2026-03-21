-- Demo sandbox sessions
CREATE TABLE IF NOT EXISTS demo_sandboxes (
  id TEXT PRIMARY KEY,
  email TEXT,
  demo_tenant_id TEXT NOT NULL,
  demo_api_key TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  status TEXT DEFAULT 'active' CHECK(status IN ('active','expired','converted')),
  converted_tenant_id TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Trial signups
CREATE TABLE IF NOT EXISTS trial_signups (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  company_name TEXT,
  trial_tenant_id TEXT,
  trial_tier TEXT DEFAULT 'starter',
  trial_days INTEGER DEFAULT 14,
  trial_start TEXT DEFAULT (datetime('now')),
  trial_end TEXT,
  converted_at TEXT,
  status TEXT DEFAULT 'active' CHECK(status IN ('active','expired','converted','cancelled')),
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_demo_sandboxes_email ON demo_sandboxes(email);
CREATE INDEX IF NOT EXISTS idx_trial_signups_email ON trial_signups(email);
CREATE INDEX IF NOT EXISTS idx_trial_signups_status ON trial_signups(status);
