-- Migration 0016: Pilot Single-Use Invite Codes, Mission Outbox, and Idempotent Credit Events
-- Strictly additive migration for Mekong Invited Pilot Go-Live

CREATE TABLE IF NOT EXISTS pilot_invites (
  id TEXT PRIMARY KEY,
  code_hash TEXT NOT NULL UNIQUE,
  partner_label TEXT,
  status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'redeemed', 'revoked')),
  issued_by TEXT NOT NULL DEFAULT 'operator',
  redeemed_by_tenant_id TEXT REFERENCES tenants(id) ON DELETE SET NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  redeemed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_pilot_invites_status ON pilot_invites(status);
CREATE INDEX IF NOT EXISTS idx_pilot_invites_code_hash ON pilot_invites(code_hash);

CREATE TABLE IF NOT EXISTS mission_outbox (
  id TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL UNIQUE REFERENCES missions(id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'processed', 'dlq')),
  attempts INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mission_outbox_status ON mission_outbox(status, created_at);

CREATE TABLE IF NOT EXISTS mission_credit_events (
  idempotency_key TEXT PRIMARY KEY,
  mission_id TEXT NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL CHECK (event_type IN ('debit', 'refund')),
  amount INTEGER NOT NULL,
  credit_entry_id TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mission_credit_events_mission ON mission_credit_events(mission_id, event_type);

CREATE TABLE IF NOT EXISTS mission_feedback (
  mission_id TEXT PRIMARY KEY REFERENCES missions(id) ON DELETE CASCADE,
  tenant_id TEXT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  comment TEXT,
  within_48h INTEGER NOT NULL DEFAULT 1,
  submitted_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mission_feedback_tenant ON mission_feedback(tenant_id, submitted_at);

