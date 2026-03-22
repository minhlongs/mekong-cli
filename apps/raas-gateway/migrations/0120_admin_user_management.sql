-- Migration 0120: Admin User Management
-- Admin users, roles, permissions, and activity log tables

CREATE TABLE IF NOT EXISTS admin_users (
  id TEXT PRIMARY KEY DEFAULT ('au_' || lower(hex(randomblob(8)))),
  email TEXT NOT NULL UNIQUE,
  display_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'viewer', -- super_admin, admin, viewer
  permissions_json TEXT NOT NULL DEFAULT '[]', -- JSON array of permission strings
  is_active INTEGER NOT NULL DEFAULT 1,
  last_login_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_admin_users_email ON admin_users(email);
CREATE INDEX IF NOT EXISTS idx_admin_users_role ON admin_users(role);
CREATE INDEX IF NOT EXISTS idx_admin_users_is_active ON admin_users(is_active);

CREATE TABLE IF NOT EXISTS admin_roles (
  id TEXT PRIMARY KEY DEFAULT ('ar_' || lower(hex(randomblob(8)))),
  role_name TEXT NOT NULL UNIQUE,
  description TEXT,
  permissions_json TEXT NOT NULL DEFAULT '[]', -- JSON array of permission strings
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed default roles
INSERT OR IGNORE INTO admin_roles (role_name, description, permissions_json) VALUES
  ('super_admin', 'Full platform access', '["*"]'),
  ('admin', 'Standard admin access', '["users.read","users.write","tenants.read","incidents.read","incidents.write"]'),
  ('viewer', 'Read-only access', '["users.read","tenants.read","incidents.read"]');

CREATE TABLE IF NOT EXISTS admin_activity_log (
  id TEXT PRIMARY KEY DEFAULT ('aal_' || lower(hex(randomblob(8)))),
  admin_user_id TEXT NOT NULL,
  action TEXT NOT NULL, -- e.g. create_user, update_user, deactivate_user
  resource_type TEXT NOT NULL, -- user, role, tenant, etc.
  resource_id TEXT,
  details TEXT, -- JSON blob with before/after or context
  ip_address TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_activity_log_admin_user ON admin_activity_log(admin_user_id);
CREATE INDEX IF NOT EXISTS idx_activity_log_action ON admin_activity_log(action);
CREATE INDEX IF NOT EXISTS idx_activity_log_created_at ON admin_activity_log(created_at);
