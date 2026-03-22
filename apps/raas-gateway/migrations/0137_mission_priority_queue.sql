-- Wave 53: Mission Priority Queue for RaaS Gateway
-- Creates priority_queue, priority_rules, and queue_metrics tables

CREATE TABLE IF NOT EXISTS priority_queue (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  priority INTEGER DEFAULT 5,
  status TEXT DEFAULT 'queued',
  sla_deadline TEXT,
  queued_at TEXT DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  completed_at TEXT,
  worker_id TEXT,
  retry_count INTEGER DEFAULT 0,
  max_retries INTEGER DEFAULT 3
);

CREATE TABLE IF NOT EXISTS priority_rules (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  condition_json TEXT NOT NULL DEFAULT '{}',
  priority_boost INTEGER DEFAULT 0,
  sla_minutes INTEGER DEFAULT 60,
  tenant_id TEXT,
  is_global INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS queue_metrics (
  id TEXT PRIMARY KEY,
  timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
  queue_depth INTEGER DEFAULT 0,
  avg_wait_ms INTEGER DEFAULT 0,
  p95_wait_ms INTEGER DEFAULT 0,
  throughput_per_min REAL DEFAULT 0,
  priority_distribution_json TEXT DEFAULT '{}'
);

-- Indexes for priority_queue
CREATE INDEX IF NOT EXISTS idx_priority_queue_tenant_id ON priority_queue(tenant_id);
CREATE INDEX IF NOT EXISTS idx_priority_queue_priority ON priority_queue(priority);
CREATE INDEX IF NOT EXISTS idx_priority_queue_status ON priority_queue(status);
CREATE INDEX IF NOT EXISTS idx_priority_queue_sla_deadline ON priority_queue(sla_deadline);
CREATE INDEX IF NOT EXISTS idx_priority_queue_mission_id ON priority_queue(mission_id);

-- Indexes for priority_rules
CREATE INDEX IF NOT EXISTS idx_priority_rules_tenant_id ON priority_rules(tenant_id);
CREATE INDEX IF NOT EXISTS idx_priority_rules_is_global ON priority_rules(is_global);
