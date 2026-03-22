CREATE TABLE IF NOT EXISTS tenant_groups (
  id TEXT PRIMARY KEY,
  group_name TEXT NOT NULL,
  description TEXT,
  parent_group_id TEXT,
  settings_json TEXT DEFAULT '{}',
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tenant_groups_name ON tenant_groups(group_name);
CREATE INDEX IF NOT EXISTS idx_tenant_groups_parent ON tenant_groups(parent_group_id);

CREATE TABLE IF NOT EXISTS tenant_group_members (
  id TEXT PRIMARY KEY,
  group_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  role TEXT DEFAULT 'member',
  joined_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tenant_group_members_group ON tenant_group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_tenant_group_members_tenant ON tenant_group_members(tenant_id);
