CREATE TABLE IF NOT EXISTS contacts (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  external_id TEXT, platform TEXT DEFAULT 'zalo', name TEXT, phone TEXT, email TEXT,
  tags JSON DEFAULT '[]', first_contact_at TEXT NOT NULL DEFAULT (datetime('now')),
  last_contact_at TEXT NOT NULL DEFAULT (datetime('now')), visit_count INTEGER DEFAULT 1,
  total_spend REAL DEFAULT 0, notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_contacts_tenant ON contacts(tenant_id);
CREATE TABLE IF NOT EXISTS remarketing_campaigns (
  id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, name TEXT NOT NULL,
  trigger_type TEXT NOT NULL CHECK (trigger_type IN ('days_since_visit','birthday','manual','tag_match')),
  trigger_value TEXT, message_template TEXT NOT NULL, channel TEXT DEFAULT 'zalo',
  active INTEGER DEFAULT 1, sent_count INTEGER DEFAULT 0, created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS remarketing_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id TEXT NOT NULL, contact_id TEXT NOT NULL,
  sent_at TEXT NOT NULL DEFAULT (datetime('now')), status TEXT DEFAULT 'sent'
);
