-- Tenant API Documentation: pages + version history
CREATE TABLE IF NOT EXISTS api_documentation_pages (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  page_title TEXT NOT NULL,
  slug TEXT NOT NULL,
  content TEXT,
  category TEXT NOT NULL DEFAULT 'guide',
  published INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_documentation_pages_tenant ON api_documentation_pages(tenant_id);

CREATE TABLE IF NOT EXISTS api_documentation_versions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  page_id TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  content TEXT,
  edited_by TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_documentation_versions_page ON api_documentation_versions(page_id);
