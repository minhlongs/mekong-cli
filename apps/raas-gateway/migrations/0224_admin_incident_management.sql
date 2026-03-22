-- Admin incident management — platform incidents, outages, resolution tracking
CREATE TABLE IF NOT EXISTS platform_incidents (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  severity TEXT NOT NULL DEFAULT 'medium',
  status TEXT NOT NULL DEFAULT 'investigating',
  affected_services TEXT,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_platform_incidents_status ON platform_incidents(status);

CREATE TABLE IF NOT EXISTS platform_incident_updates (
  id TEXT PRIMARY KEY,
  incident_id TEXT NOT NULL,
  update_text TEXT NOT NULL,
  status TEXT NOT NULL,
  author TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_platform_incident_updates_incident ON platform_incident_updates(incident_id);
