CREATE TABLE IF NOT EXISTS roles (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  permissions TEXT NOT NULL DEFAULT '[]', -- JSON array of permission strings
  is_system BOOLEAN DEFAULT FALSE,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_roles_tenant ON roles(tenant_id);
CREATE UNIQUE INDEX idx_roles_tenant_name ON roles(tenant_id, name);

CREATE TABLE IF NOT EXISTS role_assignments (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  user_id TEXT NOT NULL,
  role_id TEXT NOT NULL,
  assigned_by TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_role_assignments_tenant ON role_assignments(tenant_id);
CREATE INDEX idx_role_assignments_user ON role_assignments(tenant_id, user_id);
CREATE UNIQUE INDEX idx_role_assignments_unique ON role_assignments(tenant_id, user_id, role_id);
