-- Migration: Tenant API Documentation
-- Stores documentation pages and version snapshots per tenant

CREATE TABLE IF NOT EXISTS api_doc_pages (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  title TEXT NOT NULL,
  slug TEXT NOT NULL,
  content TEXT NOT NULL DEFAULT '',
  category TEXT NOT NULL DEFAULT '',
  sort_order INTEGER NOT NULL DEFAULT 0,
  is_published INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_doc_pages_tenant_id ON api_doc_pages (tenant_id);

CREATE TABLE IF NOT EXISTS api_doc_versions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  version_label TEXT NOT NULL,
  is_current INTEGER NOT NULL DEFAULT 0,
  published_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_doc_versions_tenant_id ON api_doc_versions (tenant_id);
