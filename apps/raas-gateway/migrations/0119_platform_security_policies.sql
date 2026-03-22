-- Migration 0119: Platform Security Policies
-- Security policy templates, enforcement rules, violation tracking per tenant

CREATE TABLE IF NOT EXISTS security_policies (
  id TEXT PRIMARY KEY DEFAULT ('sp_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  policy_name TEXT NOT NULL,
  policy_type TEXT NOT NULL DEFAULT 'access', -- password, access, data, network
  rules_json TEXT NOT NULL DEFAULT '{}',
  is_enforced INTEGER NOT NULL DEFAULT 1,
  severity TEXT NOT NULL DEFAULT 'medium', -- low, medium, high, critical
  deleted INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_sec_policies_tenant ON security_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sec_policies_type ON security_policies(policy_type);
CREATE INDEX IF NOT EXISTS idx_sec_policies_enforced ON security_policies(is_enforced);

CREATE TABLE IF NOT EXISTS security_policy_templates (
  id TEXT PRIMARY KEY DEFAULT ('spt_' || lower(hex(randomblob(8)))),
  name TEXT NOT NULL,
  description TEXT,
  policy_type TEXT NOT NULL DEFAULT 'access', -- password, access, data, network
  default_rules_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS security_violations (
  id TEXT PRIMARY KEY DEFAULT ('sv_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  policy_id TEXT NOT NULL,
  violation_type TEXT NOT NULL,
  details TEXT,
  resolved INTEGER NOT NULL DEFAULT 0,
  detected_at TEXT NOT NULL DEFAULT (datetime('now')),
  resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_sec_violations_tenant ON security_violations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_sec_violations_resolved ON security_violations(resolved);

-- Seed default templates
INSERT OR IGNORE INTO security_policy_templates (id, name, description, policy_type, default_rules_json) VALUES
  ('spt_password_default', 'Strong Password Policy', 'Enforce strong password requirements', 'password', '{"min_length":12,"require_uppercase":true,"require_numbers":true,"require_symbols":true,"max_age_days":90}'),
  ('spt_access_default', 'Least Privilege Access', 'Restrict access to minimum required', 'access', '{"mfa_required":true,"session_timeout_minutes":60,"max_sessions":3,"ip_whitelist_enabled":false}'),
  ('spt_data_default', 'Data Protection Policy', 'Encrypt and protect sensitive data', 'data', '{"encryption_at_rest":true,"encryption_in_transit":true,"data_retention_days":365,"pii_masking":true}'),
  ('spt_network_default', 'Network Security Policy', 'Control network access and traffic', 'network', '{"tls_min_version":"1.2","block_tor_exit_nodes":true,"rate_limit_enabled":true,"ddos_protection":true}');
