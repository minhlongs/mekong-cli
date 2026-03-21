-- Migration 0038: Mission Execution Timeline & Tracing
-- Tracks granular execution events and aggregate trace summaries per mission

CREATE TABLE IF NOT EXISTS mission_timeline_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id INTEGER NOT NULL,
  tenant_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  event_data TEXT NOT NULL DEFAULT '{}',
  duration_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (mission_id) REFERENCES missions(id)
);

CREATE INDEX idx_timeline_mission ON mission_timeline_events(mission_id, created_at);
CREATE INDEX idx_timeline_tenant ON mission_timeline_events(tenant_id, created_at);

CREATE TABLE IF NOT EXISTS mission_traces (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  mission_id INTEGER NOT NULL UNIQUE,
  tenant_id TEXT NOT NULL,
  trace_id TEXT NOT NULL,
  total_duration_ms INTEGER,
  step_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'running',
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  completed_at TEXT,
  FOREIGN KEY (mission_id) REFERENCES missions(id)
);

CREATE INDEX idx_trace_id ON mission_traces(trace_id);
