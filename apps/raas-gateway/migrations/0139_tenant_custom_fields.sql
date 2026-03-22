-- Wave 54: Tenant Custom Fields
-- Tables: custom_field_definitions, custom_field_values

CREATE TABLE IF NOT EXISTS custom_field_definitions (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  field_name TEXT NOT NULL,
  field_type TEXT DEFAULT 'text',
  label TEXT NOT NULL,
  description TEXT,
  required INTEGER DEFAULT 0,
  default_value TEXT,
  validation_json TEXT DEFAULT '{}',
  sort_order INTEGER DEFAULT 0,
  searchable INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS custom_field_values (
  id TEXT PRIMARY KEY,
  definition_id TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  value TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(definition_id, entity_id)
);

-- Indexes for custom_field_definitions
CREATE INDEX IF NOT EXISTS idx_custom_field_defs_tenant_id ON custom_field_definitions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_defs_entity_type ON custom_field_definitions(entity_type);
CREATE INDEX IF NOT EXISTS idx_custom_field_defs_tenant_entity ON custom_field_definitions(tenant_id, entity_type);

-- Indexes for custom_field_values
CREATE INDEX IF NOT EXISTS idx_custom_field_vals_definition_id ON custom_field_values(definition_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_vals_entity_id ON custom_field_values(entity_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_vals_tenant_id ON custom_field_values(tenant_id);
CREATE INDEX IF NOT EXISTS idx_custom_field_vals_tenant_entity ON custom_field_values(tenant_id, entity_id);
