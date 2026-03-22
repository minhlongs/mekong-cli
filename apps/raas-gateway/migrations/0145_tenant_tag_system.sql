-- Wave 56: Tenant Tag System for RaaS Gateway
-- Tables: tags, entity_tags

CREATE TABLE IF NOT EXISTS tags (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  color TEXT DEFAULT '#6B7280',
  description TEXT,
  usage_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS entity_tags (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  tag_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for tags
CREATE INDEX IF NOT EXISTS idx_tags_tenant_id ON tags(tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tags_tenant_name ON tags(tenant_id, name);

-- Indexes for entity_tags
CREATE INDEX IF NOT EXISTS idx_entity_tags_tenant_id ON entity_tags(tenant_id);
CREATE INDEX IF NOT EXISTS idx_entity_tags_tag_id ON entity_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_entity_tags_entity_type ON entity_tags(entity_type);
CREATE INDEX IF NOT EXISTS idx_entity_tags_entity_id ON entity_tags(entity_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_entity_tags_unique ON entity_tags(tag_id, entity_type, entity_id);
