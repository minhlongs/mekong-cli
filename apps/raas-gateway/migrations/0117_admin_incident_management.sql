-- Migration 0117: Admin Incident Management
-- Incident tracking, status updates, and postmortem tables

CREATE TABLE IF NOT EXISTS incidents (
  id TEXT PRIMARY KEY DEFAULT ('inc_' || lower(hex(randomblob(8)))),
  title TEXT NOT NULL,
  description TEXT,
  severity TEXT NOT NULL DEFAULT 'medium', -- critical, high, medium, low
  status TEXT NOT NULL DEFAULT 'investigating', -- investigating, identified, monitoring, resolved, postmortem
  impact TEXT NOT NULL DEFAULT 'partial', -- none, partial, major, full
  affected_services TEXT DEFAULT '[]', -- JSON array
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  identified_at TEXT,
  resolved_at TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity);

CREATE TABLE IF NOT EXISTS incident_updates (
  id TEXT PRIMARY KEY DEFAULT ('iu_' || lower(hex(randomblob(8)))),
  incident_id TEXT NOT NULL,
  update_type TEXT NOT NULL DEFAULT 'status', -- status, note, resolution
  message TEXT NOT NULL,
  new_status TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_inc_updates_incident ON incident_updates(incident_id);

CREATE TABLE IF NOT EXISTS incident_postmortems (
  id TEXT PRIMARY KEY DEFAULT ('pm_' || lower(hex(randomblob(8)))),
  incident_id TEXT NOT NULL UNIQUE,
  summary TEXT NOT NULL,
  root_cause TEXT,
  timeline TEXT, -- JSON
  action_items TEXT DEFAULT '[]', -- JSON array
  lessons_learned TEXT,
  created_by TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_postmortem_incident ON incident_postmortems(incident_id);
