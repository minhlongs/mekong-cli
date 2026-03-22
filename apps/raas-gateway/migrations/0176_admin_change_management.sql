-- Admin Change Management: change_requests and change_logs tables
-- Migration 0176

CREATE TABLE IF NOT EXISTS change_requests (
  id           TEXT PRIMARY KEY,
  title        TEXT NOT NULL,
  description  TEXT,
  change_type  TEXT NOT NULL,
  priority     TEXT NOT NULL DEFAULT 'medium',
  status       TEXT NOT NULL DEFAULT 'pending',
  requested_by TEXT,
  approved_by  TEXT,
  scheduled_at TEXT,
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS change_logs (
  id           TEXT PRIMARY KEY,
  change_id    TEXT NOT NULL,
  action       TEXT NOT NULL,
  details      TEXT,
  performed_by TEXT,
  created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_change_requests_status ON change_requests (status);
CREATE INDEX IF NOT EXISTS idx_change_logs_change_id  ON change_logs (change_id);
