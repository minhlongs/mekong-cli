CREATE TABLE IF NOT EXISTS mission_queue_configs (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  queue_name TEXT NOT NULL,
  priority_level INTEGER DEFAULT 5,
  max_concurrency INTEGER DEFAULT 10,
  timeout_ms INTEGER DEFAULT 60000,
  status TEXT DEFAULT 'active',
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_mission_queue_configs_tenant ON mission_queue_configs(tenant_id);

CREATE TABLE IF NOT EXISTS mission_queue_items (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  queue_id TEXT NOT NULL,
  mission_id TEXT NOT NULL,
  priority INTEGER DEFAULT 5,
  status TEXT DEFAULT 'pending',
  enqueued_at TEXT DEFAULT CURRENT_TIMESTAMP,
  started_at TEXT,
  completed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_mission_queue_items_tenant ON mission_queue_items(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_queue_items_queue ON mission_queue_items(queue_id);
CREATE INDEX IF NOT EXISTS idx_mission_queue_items_status ON mission_queue_items(status);
