-- Wave 53: Tenant SSO Providers
-- Tables: sso_providers, sso_sessions, sso_login_attempts

CREATE TABLE IF NOT EXISTS sso_providers (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  provider_type TEXT NOT NULL,
  name TEXT NOT NULL,
  client_id TEXT,
  client_secret TEXT,
  metadata_url TEXT,
  issuer_url TEXT,
  callback_url TEXT,
  scopes_json TEXT DEFAULT '["openid","profile","email"]',
  status TEXT DEFAULT 'active',
  auto_provision INTEGER DEFAULT 0,
  default_role TEXT DEFAULT 'member',
  config_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sso_sessions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  user_email TEXT NOT NULL,
  external_id TEXT,
  session_token TEXT,
  expires_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sso_login_attempts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  provider_id TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  error TEXT,
  ip_address TEXT,
  user_agent TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for sso_providers
CREATE INDEX IF NOT EXISTS idx_sso_providers_tenant_id ON sso_providers(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sso_providers_provider_type ON sso_providers(provider_type);
CREATE INDEX IF NOT EXISTS idx_sso_providers_status ON sso_providers(status);

-- Indexes for sso_sessions
CREATE INDEX IF NOT EXISTS idx_sso_sessions_tenant_id ON sso_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sso_sessions_user_email ON sso_sessions(user_email);
CREATE INDEX IF NOT EXISTS idx_sso_sessions_session_token ON sso_sessions(session_token);

-- Indexes for sso_login_attempts
CREATE INDEX IF NOT EXISTS idx_sso_login_attempts_tenant_id ON sso_login_attempts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sso_login_attempts_provider_id ON sso_login_attempts(provider_id);
