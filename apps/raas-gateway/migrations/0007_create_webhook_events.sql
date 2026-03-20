-- Migration: 0007_create_webhook_events
-- Created: 2026-03-19
-- Description: Create webhook_events table for idempotency and replay attack prevention

CREATE TABLE IF NOT EXISTS webhook_events (
  id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,  -- Polar event ID (unique constraint for idempotency)
  event_type TEXT NOT NULL,
  processed INTEGER DEFAULT 1 CHECK(processed IN (0, 1)),
  error_message TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

-- Index for event lookup by Polar event_id
CREATE INDEX IF NOT EXISTS idx_webhook_events_event_id ON webhook_events(event_id);

-- Index for event type analysis
CREATE INDEX IF NOT EXISTS idx_webhook_events_type ON webhook_events(event_type);

-- Index for unprocessed events (for retry monitoring)
CREATE INDEX IF NOT EXISTS idx_webhook_events_unprocessed ON webhook_events(processed) WHERE processed = 0;
