CREATE TABLE IF NOT EXISTS webhook_templates (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  template_name TEXT NOT NULL,
  event_type TEXT NOT NULL,
  url_pattern TEXT NOT NULL,
  headers_json TEXT DEFAULT '{}',
  payload_template TEXT,
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_webhook_templates_tenant ON webhook_templates(tenant_id);

CREATE TABLE IF NOT EXISTS webhook_template_usage (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  template_id TEXT NOT NULL,
  webhook_id TEXT NOT NULL,
  applied_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_webhook_template_usage_tenant ON webhook_template_usage(tenant_id);
CREATE INDEX IF NOT EXISTS idx_webhook_template_usage_template ON webhook_template_usage(template_id);
