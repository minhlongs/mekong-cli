CREATE TABLE IF NOT EXISTS conflicts (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  reporter_id TEXT NOT NULL REFERENCES stakeholders(id),
  against_id TEXT REFERENCES stakeholders(id),
  conflict_type TEXT NOT NULL CHECK (conflict_type IN ('resource','equity','decision','conduct','constitutional')),
  description TEXT NOT NULL,
  severity TEXT NOT NULL DEFAULT 'medium' CHECK (severity IN ('low','medium','high','critical')),
  resolution_level INTEGER NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','auto_resolved','negotiating','under_review','arbitration','constitutional_review','resolved','dismissed')),
  resolution_notes TEXT,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_conflict_tenant ON conflicts(tenant_id);

CREATE TABLE IF NOT EXISTS conflict_escalations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conflict_id TEXT NOT NULL REFERENCES conflicts(id),
  from_level INTEGER NOT NULL,
  to_level INTEGER NOT NULL,
  reason TEXT NOT NULL,
  escalated_by TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
