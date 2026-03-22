-- Admin Tenant Communication — messages from platform to tenants + reusable templates

CREATE TABLE IF NOT EXISTS tenant_messages (
  id           TEXT PRIMARY KEY,
  tenant_id    TEXT NOT NULL,
  subject      TEXT NOT NULL,
  body         TEXT NOT NULL,
  message_type TEXT NOT NULL DEFAULT 'info',   -- info | warning | action | announcement
  priority     TEXT NOT NULL DEFAULT 'normal', -- low | normal | high | urgent
  read_at      TEXT,
  sent_by      TEXT NOT NULL,
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenant_messages_tenant_type
  ON tenant_messages (tenant_id, message_type);

CREATE TABLE IF NOT EXISTS tenant_message_templates (
  id               TEXT PRIMARY KEY,
  template_name    TEXT NOT NULL UNIQUE,
  subject_template TEXT NOT NULL,
  body_template    TEXT NOT NULL,
  category         TEXT NOT NULL,  -- billing | security | onboarding | maintenance | general
  created_at       TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenant_message_templates_name
  ON tenant_message_templates (template_name);
