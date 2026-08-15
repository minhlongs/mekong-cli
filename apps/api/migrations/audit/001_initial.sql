-- Audit/request logs table
CREATE TABLE IF NOT EXISTS request_logs (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  method TEXT NOT NULL,
  status INTEGER NOT NULL,
  timestamp TEXT NOT NULL,
  user_agent TEXT,
  ip TEXT
);

CREATE INDEX IF NOT EXISTS idx_request_logs_timestamp ON request_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_request_logs_path ON request_logs(path);

-- Payment events table
CREATE TABLE IF NOT EXISTS payment_events (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  amount REAL NOT NULL,
  currency TEXT NOT NULL,
  status TEXT NOT NULL,
  raw_payload TEXT NOT NULL,
  received_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payment_events_user ON payment_events(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_events_timestamp ON payment_events(received_at);

-- User events table
CREATE TABLE IF NOT EXISTS user_events (
  id TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  email TEXT,
  event_type TEXT NOT NULL,
  raw_payload TEXT NOT NULL,
  received_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_user_events_user ON user_events(user_id);
CREATE INDEX IF NOT EXISTS idx_user_events_type ON user_events(event_type);
