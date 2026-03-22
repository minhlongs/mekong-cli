-- Wave 57: Tenant Workspace Settings for RaaS Gateway
-- Tables: workspace_settings, workspace_invitations

CREATE TABLE IF NOT EXISTS workspace_settings (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL UNIQUE,
  workspace_name TEXT,
  theme TEXT DEFAULT 'system',
  timezone TEXT DEFAULT 'UTC',
  language TEXT DEFAULT 'en',
  date_format TEXT DEFAULT 'YYYY-MM-DD',
  notification_config_json TEXT DEFAULT '{"email":true,"slack":false,"webhook":true}',
  branding_json TEXT DEFAULT '{}',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workspace_invitations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  email TEXT NOT NULL,
  role TEXT DEFAULT 'member',
  status TEXT DEFAULT 'pending',
  invited_by TEXT,
  expires_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for workspace_settings
CREATE INDEX IF NOT EXISTS idx_workspace_settings_tenant_id ON workspace_settings(tenant_id);

-- Indexes for workspace_invitations
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_tenant_id ON workspace_invitations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_email ON workspace_invitations(email);
CREATE INDEX IF NOT EXISTS idx_workspace_invitations_status ON workspace_invitations(status);
