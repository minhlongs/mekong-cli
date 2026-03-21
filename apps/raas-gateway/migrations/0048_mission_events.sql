-- Migration 0048: mission_events table for SSE event streaming
CREATE TABLE IF NOT EXISTS mission_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload TEXT DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_mission_events_tenant ON mission_events(tenant_id, created_at);
CREATE INDEX IF NOT EXISTS idx_mission_events_mission ON mission_events(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_events_type ON mission_events(event_type);
