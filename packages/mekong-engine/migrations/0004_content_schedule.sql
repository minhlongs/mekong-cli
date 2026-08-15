CREATE TABLE IF NOT EXISTS content_posts (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  channel TEXT NOT NULL DEFAULT 'facebook', content_text TEXT NOT NULL, image_prompt TEXT, image_url TEXT,
  status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','approved','scheduled','published','rejected')),
  scheduled_at TEXT, published_at TEXT, engagement JSON DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_content_tenant ON content_posts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_content_status ON content_posts(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_content_schedule ON content_posts(status, scheduled_at);
CREATE TABLE IF NOT EXISTS content_templates (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, industry TEXT NOT NULL DEFAULT 'cafe',
  template_type TEXT NOT NULL DEFAULT 'social_post', prompt_template TEXT NOT NULL, example_output TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
