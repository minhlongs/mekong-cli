-- Audit Log Streaming: destination configs and delivery tracking
CREATE TABLE IF NOT EXISTS audit_stream_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  stream_type TEXT NOT NULL DEFAULT 'webhook', -- webhook, s3, syslog
  destination_url TEXT NOT NULL,
  auth_header TEXT, -- encrypted auth token for destination
  event_filters TEXT DEFAULT '[]', -- JSON array of event types to stream
  is_active INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
CREATE INDEX idx_audit_stream_tenant ON audit_stream_configs(tenant_id);

CREATE TABLE IF NOT EXISTS audit_stream_deliveries (
  id TEXT PRIMARY KEY,
  config_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT NOT NULL, -- JSON
  status TEXT DEFAULT 'pending', -- pending, delivered, failed
  attempts INTEGER DEFAULT 0,
  last_error TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  delivered_at TEXT,
  FOREIGN KEY (config_id) REFERENCES audit_stream_configs(id)
);
CREATE INDEX idx_audit_delivery_config ON audit_stream_deliveries(config_id);
CREATE INDEX idx_audit_delivery_status ON audit_stream_deliveries(status);
