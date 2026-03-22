CREATE TABLE IF NOT EXISTS tenant_notes (
  id TEXT PRIMARY KEY DEFAULT ('tn_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  author TEXT NOT NULL, -- admin who wrote it
  content TEXT NOT NULL,
  note_type TEXT NOT NULL DEFAULT 'general', -- general, support, billing, escalation, technical
  is_pinned INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_tn_tenant ON tenant_notes(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tn_type ON tenant_notes(note_type);

CREATE TABLE IF NOT EXISTS tenant_tags (
  id TEXT PRIMARY KEY DEFAULT ('tt_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  tag TEXT NOT NULL,
  color TEXT DEFAULT '#6366f1',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_tt_unique ON tenant_tags(tenant_id, tag);
CREATE INDEX IF NOT EXISTS idx_tt_tag ON tenant_tags(tag);

CREATE TABLE IF NOT EXISTS tenant_risk_scores (
  id TEXT PRIMARY KEY DEFAULT ('trs_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL UNIQUE,
  churn_risk REAL NOT NULL DEFAULT 0, -- 0-100
  health_score REAL NOT NULL DEFAULT 100, -- 0-100
  engagement_score REAL NOT NULL DEFAULT 50, -- 0-100
  payment_reliability REAL NOT NULL DEFAULT 100, -- 0-100
  last_calculated_at TEXT NOT NULL DEFAULT (datetime('now')),
  factors TEXT DEFAULT '{}', -- JSON breakdown
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_trs_churn ON tenant_risk_scores(churn_risk DESC);
