-- Wave 55: Platform Rate Limit Analytics for RaaS Gateway
-- Tables: rate_limit_events, abuse_detections, throttle_history

CREATE TABLE IF NOT EXISTS rate_limit_events (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  ip_address TEXT,
  action TEXT DEFAULT 'throttled',
  remaining INTEGER,
  limit_value INTEGER,
  window_seconds INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS abuse_detections (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  ip_address TEXT NOT NULL,
  detection_type TEXT DEFAULT 'brute_force',
  severity TEXT DEFAULT 'medium',
  details_json TEXT DEFAULT '{}',
  resolved INTEGER DEFAULT 0,
  detected_at TEXT DEFAULT CURRENT_TIMESTAMP,
  resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS throttle_history (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  period TEXT NOT NULL,
  total_requests INTEGER DEFAULT 0,
  throttled_requests INTEGER DEFAULT 0,
  unique_ips INTEGER DEFAULT 0,
  top_endpoints_json TEXT DEFAULT '[]',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for rate_limit_events
CREATE INDEX IF NOT EXISTS idx_rate_limit_events_tenant_id ON rate_limit_events(tenant_id);
CREATE INDEX IF NOT EXISTS idx_rate_limit_events_endpoint ON rate_limit_events(endpoint);
CREATE INDEX IF NOT EXISTS idx_rate_limit_events_ip_address ON rate_limit_events(ip_address);

-- Indexes for abuse_detections
CREATE INDEX IF NOT EXISTS idx_abuse_detections_ip_address ON abuse_detections(ip_address);
CREATE INDEX IF NOT EXISTS idx_abuse_detections_detection_type ON abuse_detections(detection_type);
CREATE INDEX IF NOT EXISTS idx_abuse_detections_severity ON abuse_detections(severity);

-- Indexes for throttle_history
CREATE INDEX IF NOT EXISTS idx_throttle_history_tenant_id ON throttle_history(tenant_id);
CREATE INDEX IF NOT EXISTS idx_throttle_history_period ON throttle_history(period);
