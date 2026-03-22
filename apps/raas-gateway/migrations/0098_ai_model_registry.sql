-- AI Model Registry: providers, model definitions, usage tracking
-- Wave 40.2

CREATE TABLE IF NOT EXISTS ai_model_providers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  base_url TEXT NOT NULL,
  auth_type TEXT DEFAULT 'bearer', -- bearer, api_key, none
  is_active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS ai_model_definitions (
  id TEXT PRIMARY KEY,
  provider_id TEXT NOT NULL,
  model_id TEXT NOT NULL, -- e.g. gpt-4, claude-opus-4-6
  display_name TEXT NOT NULL,
  category TEXT DEFAULT 'general', -- general, coding, creative, analysis, fast
  context_window INTEGER DEFAULT 4096,
  cost_per_1k_input REAL DEFAULT 0,
  cost_per_1k_output REAL DEFAULT 0,
  max_output_tokens INTEGER DEFAULT 4096,
  supports_tools INTEGER DEFAULT 0,
  supports_vision INTEGER DEFAULT 0,
  is_active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  UNIQUE(provider_id, model_id)
);
CREATE INDEX idx_models_provider ON ai_model_definitions(provider_id);
CREATE INDEX idx_models_category ON ai_model_definitions(category);

CREATE TABLE IF NOT EXISTS model_usage_tracking (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  input_tokens INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0,
  cost_usd REAL DEFAULT 0,
  mission_id TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_model_usage_tenant ON model_usage_tracking(tenant_id, created_at);
CREATE INDEX idx_model_usage_model ON model_usage_tracking(model_id);
