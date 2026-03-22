-- Mission Template Library
-- Wave 49: reusable config templates with versioning and categories

CREATE TABLE IF NOT EXISTS mission_templates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  name TEXT NOT NULL,
  description TEXT,
  category TEXT DEFAULT 'general',
  config_json TEXT NOT NULL DEFAULT '{}',
  parameters_json TEXT DEFAULT '[]',
  version INTEGER DEFAULT 1,
  is_public INTEGER DEFAULT 0,
  usage_count INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS template_categories (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  icon TEXT,
  sort_order INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS template_versions (
  id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  config_json TEXT NOT NULL,
  changelog TEXT,
  created_by TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_mission_templates_tenant ON mission_templates(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_templates_category ON mission_templates(category);
CREATE INDEX IF NOT EXISTS idx_mission_templates_public ON mission_templates(is_public);
CREATE INDEX IF NOT EXISTS idx_template_versions_template ON template_versions(template_id);

-- Seed default categories
INSERT OR IGNORE INTO template_categories (id, name, description, icon, sort_order) VALUES
  ('cat_general', 'general', 'General purpose templates', '🔧', 0),
  ('cat_data', 'data-processing', 'Data transformation and analysis templates', '📊', 1),
  ('cat_monitoring', 'monitoring', 'System health and alerting templates', '📡', 2),
  ('cat_automation', 'automation', 'Workflow and process automation templates', '⚡', 3),
  ('cat_integration', 'integration', 'Third-party integration templates', '🔗', 4);
