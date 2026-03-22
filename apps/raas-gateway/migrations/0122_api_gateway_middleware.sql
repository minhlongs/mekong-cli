-- Migration 0122: API Gateway Middleware Config
-- Custom middleware chains per tenant: request/response transforms, header injection, body rewriting

CREATE TABLE IF NOT EXISTS middleware_configs (
  id TEXT PRIMARY KEY DEFAULT ('mc_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  middleware_type TEXT NOT NULL CHECK (middleware_type IN ('request_transform','response_transform','header_inject','body_rewrite','cors_override')),
  config_json TEXT NOT NULL DEFAULT '{}',
  priority INTEGER NOT NULL DEFAULT 100,
  is_active INTEGER NOT NULL DEFAULT 1,
  endpoint_pattern TEXT NOT NULL DEFAULT '*',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_middleware_configs_tenant_id ON middleware_configs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_middleware_configs_middleware_type ON middleware_configs(middleware_type);
CREATE INDEX IF NOT EXISTS idx_middleware_configs_is_active ON middleware_configs(is_active);
CREATE INDEX IF NOT EXISTS idx_middleware_configs_priority ON middleware_configs(priority);

CREATE TABLE IF NOT EXISTS middleware_execution_logs (
  id TEXT PRIMARY KEY DEFAULT ('mel_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  middleware_id TEXT NOT NULL,
  request_path TEXT NOT NULL,
  execution_time_ms INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK (status IN ('success','error','skipped')) DEFAULT 'success',
  error_message TEXT,
  executed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_middleware_logs_tenant_id ON middleware_execution_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_middleware_logs_middleware_id ON middleware_execution_logs(middleware_id);
CREATE INDEX IF NOT EXISTS idx_middleware_logs_executed_at ON middleware_execution_logs(executed_at);

CREATE TABLE IF NOT EXISTS middleware_templates (
  id TEXT PRIMARY KEY DEFAULT ('mt_' || lower(hex(randomblob(8)))),
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  middleware_type TEXT NOT NULL,
  default_config_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Seed built-in templates
INSERT OR IGNORE INTO middleware_templates (name, description, middleware_type, default_config_json) VALUES
  ('Add Correlation ID', 'Injects X-Correlation-ID header into every request', 'header_inject', '{"header":"X-Correlation-ID","value":"{{uuid}}"}'),
  ('Strip Internal Headers', 'Removes internal headers before forwarding upstream', 'request_transform', '{"remove_headers":["X-Internal-Token","X-Debug"]}'),
  ('Append Tenant ID Header', 'Appends X-Tenant-ID to upstream requests', 'header_inject', '{"header":"X-Tenant-ID","value":"{{tenant_id}}"}'),
  ('CORS Override Allow All', 'Sets permissive CORS headers on responses', 'cors_override', '{"allow_origin":"*","allow_methods":"GET,POST,PUT,DELETE,OPTIONS","allow_headers":"*"}'),
  ('JSON Body Envelope', 'Wraps response body in a standard envelope', 'response_transform', '{"envelope":{"success":true,"data":"{{body}}"},"content_type":"application/json"}');
