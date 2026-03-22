-- Migration 0113: Mission Replay & Debug
-- Tables: mission_execution_steps, mission_debug_sessions, mission_replay_logs

CREATE TABLE IF NOT EXISTS mission_execution_steps (
  id TEXT PRIMARY KEY DEFAULT ('ms_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  step_number INTEGER NOT NULL,
  step_type TEXT NOT NULL, -- 'llm_call', 'tool_exec', 'validation', 'decision'
  input_data TEXT, -- JSON
  output_data TEXT, -- JSON
  duration_ms INTEGER,
  status TEXT NOT NULL DEFAULT 'completed', -- pending, running, completed, failed
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_exec_steps_mission ON mission_execution_steps(mission_id);
CREATE INDEX IF NOT EXISTS idx_exec_steps_tenant ON mission_execution_steps(tenant_id);

CREATE TABLE IF NOT EXISTS mission_debug_sessions (
  id TEXT PRIMARY KEY DEFAULT ('ds_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  debug_mode TEXT NOT NULL DEFAULT 'trace', -- trace, breakpoint, replay
  breakpoints TEXT DEFAULT '[]', -- JSON array of step numbers
  current_step INTEGER DEFAULT 0,
  session_status TEXT NOT NULL DEFAULT 'active', -- active, paused, completed
  notes TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_debug_sessions_tenant ON mission_debug_sessions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_debug_sessions_mission ON mission_debug_sessions(mission_id);

CREATE TABLE IF NOT EXISTS mission_replay_logs (
  id TEXT PRIMARY KEY DEFAULT ('rl_' || lower(hex(randomblob(8)))),
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  original_mission_id TEXT NOT NULL,
  replay_status TEXT NOT NULL DEFAULT 'pending', -- pending, running, completed, diverged
  divergence_point INTEGER, -- step where replay diverged
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_replay_tenant ON mission_replay_logs(tenant_id);
