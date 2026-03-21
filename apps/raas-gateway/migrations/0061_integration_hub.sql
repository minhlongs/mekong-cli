-- Integration Hub: catalog, tenant installations, event log
-- Migration: 0061_integration_hub

-- Integration catalog (available connectors)
CREATE TABLE IF NOT EXISTS integration_catalog (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  slug TEXT NOT NULL UNIQUE,
  category TEXT NOT NULL CHECK(category IN ('communication', 'project_management', 'devops', 'crm', 'analytics', 'storage', 'other')),
  description TEXT,
  icon_url TEXT,
  auth_type TEXT DEFAULT 'oauth2' CHECK(auth_type IN ('oauth2', 'api_key', 'webhook', 'none')),
  config_schema TEXT DEFAULT '{}',
  supported_events TEXT DEFAULT '[]',
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Tenant integrations (installed connectors)
CREATE TABLE IF NOT EXISTS tenant_integrations (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  catalog_id TEXT NOT NULL,
  config TEXT DEFAULT '{}',
  credentials TEXT DEFAULT '{}',
  status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'error')),
  last_sync_at TEXT,
  error_message TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  UNIQUE(tenant_id, catalog_id)
);
CREATE INDEX idx_tenant_integ_tenant ON tenant_integrations(tenant_id);

-- Integration event log
CREATE TABLE IF NOT EXISTS integration_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  integration_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  direction TEXT DEFAULT 'outbound' CHECK(direction IN ('inbound', 'outbound')),
  payload TEXT DEFAULT '{}',
  status TEXT DEFAULT 'success' CHECK(status IN ('success', 'failed')),
  error TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX idx_integ_events_tenant ON integration_events(tenant_id);
CREATE INDEX idx_integ_events_integ ON integration_events(integration_id);
