-- Wave 53: Platform Analytics Dashboard
-- Tables: dashboard_widgets, saved_queries, analytics_snapshots

CREATE TABLE IF NOT EXISTS dashboard_widgets (
  id TEXT PRIMARY KEY,
  tenant_id TEXT,
  name TEXT NOT NULL,
  widget_type TEXT NOT NULL,
  query_json TEXT NOT NULL DEFAULT '{}',
  config_json TEXT DEFAULT '{}',
  position_json TEXT DEFAULT '{"x":0,"y":0,"w":6,"h":4}',
  is_system INTEGER DEFAULT 0,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS saved_queries (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  name TEXT NOT NULL,
  query_type TEXT NOT NULL,
  parameters_json TEXT DEFAULT '{}',
  schedule TEXT,
  last_run_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS analytics_snapshots (
  id TEXT PRIMARY KEY,
  snapshot_type TEXT NOT NULL,
  data_json TEXT NOT NULL DEFAULT '{}',
  period TEXT NOT NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for dashboard_widgets
CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_tenant_id ON dashboard_widgets(tenant_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_widget_type ON dashboard_widgets(widget_type);

-- Indexes for saved_queries
CREATE INDEX IF NOT EXISTS idx_saved_queries_tenant_id ON saved_queries(tenant_id);
CREATE INDEX IF NOT EXISTS idx_saved_queries_query_type ON saved_queries(query_type);

-- Indexes for analytics_snapshots
CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_snapshot_type ON analytics_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_period ON analytics_snapshots(period);

-- Seed system widgets (5 default widgets visible to all tenants)
INSERT OR IGNORE INTO dashboard_widgets (id, tenant_id, name, widget_type, query_json, config_json, position_json, is_system) VALUES
  ('sys_widget_missions_overview', NULL, 'Missions Overview', 'missions_overview',
   '{"table":"missions","metrics":["total","active","completed","failed"]}',
   '{"chart":"summary","color":"blue"}',
   '{"x":0,"y":0,"w":6,"h":4}', 1),
  ('sys_widget_revenue_chart', NULL, 'Revenue Chart', 'revenue_chart',
   '{"table":"credit_transactions","type":"purchase","group_by":"day"}',
   '{"chart":"line","color":"green","days":30}',
   '{"x":6,"y":0,"w":6,"h":4}', 1),
  ('sys_widget_active_tenants', NULL, 'Active Tenants', 'active_tenants',
   '{"table":"tenants","filter":"active=1","metrics":["count","by_tier"]}',
   '{"chart":"donut","color":"purple"}',
   '{"x":0,"y":4,"w":4,"h":3}', 1),
  ('sys_widget_api_latency', NULL, 'API Latency', 'api_latency',
   '{"table":"api_logs","metrics":["p50","p95","p99"],"window":"1h"}',
   '{"chart":"bar","color":"orange","unit":"ms"}',
   '{"x":4,"y":4,"w":4,"h":3}', 1),
  ('sys_widget_error_rates', NULL, 'Error Rates', 'error_rates',
   '{"table":"api_logs","filter":"status>=400","group_by":"status"}',
   '{"chart":"area","color":"red","threshold":5}',
   '{"x":8,"y":4,"w":4,"h":3}', 1);
