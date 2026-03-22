-- Migration 0100: Tenant SSO V2 — SAML and OIDC identity provider management
CREATE TABLE IF NOT EXISTS sso_configurations (
  id TEXT PRIMARY KEY DEFAULT ('sso_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  provider_type TEXT NOT NULL DEFAULT 'oidc', -- oidc, saml
  provider_name TEXT NOT NULL,
  client_id TEXT,
  client_secret_hash TEXT,
  issuer_url TEXT,
  metadata_url TEXT,
  saml_certificate TEXT,
  entity_id TEXT,
  acs_url TEXT,
  slo_url TEXT,
  attribute_mapping TEXT DEFAULT '{}', -- JSON
  is_active INTEGER NOT NULL DEFAULT 1,
  enforce_sso INTEGER NOT NULL DEFAULT 0, -- force all users through SSO
  allowed_domains TEXT DEFAULT '[]', -- JSON array of email domains
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sso_tenant ON sso_configurations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sso_active ON sso_configurations(tenant_id, is_active);

CREATE TABLE IF NOT EXISTS sso_sessions (
  id TEXT PRIMARY KEY DEFAULT ('ssosess_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  sso_config_id TEXT NOT NULL,
  user_email TEXT NOT NULL,
  external_id TEXT,
  state TEXT NOT NULL, -- CSRF state param
  nonce TEXT,
  status TEXT NOT NULL DEFAULT 'pending', -- pending, authenticated, failed, expired
  identity_data TEXT DEFAULT '{}', -- JSON claims/attributes
  ip_address TEXT,
  user_agent TEXT,
  authenticated_at TEXT,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sso_sess_state ON sso_sessions(state);
CREATE INDEX IF NOT EXISTS idx_sso_sess_tenant ON sso_sessions(tenant_id, status);
