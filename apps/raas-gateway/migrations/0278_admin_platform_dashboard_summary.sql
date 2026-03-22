-- Admin platform dashboard summary: widgets config + point-in-time snapshots
CREATE TABLE IF NOT EXISTS platform_dashboard_widgets (
  id                  TEXT     PRIMARY KEY,
  widget_name         TEXT     NOT NULL,
  widget_type         TEXT     NOT NULL DEFAULT 'metric',
  data_source         TEXT     NOT NULL,
  refresh_interval_ms INTEGER  DEFAULT 60000,
  position            INTEGER  DEFAULT 0,
  enabled             INTEGER  NOT NULL DEFAULT 1,
  created_at          TEXT     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_dashboard_widgets_type ON platform_dashboard_widgets(widget_type);

CREATE TABLE IF NOT EXISTS platform_dashboard_snapshots (
  id              TEXT    PRIMARY KEY,
  snapshot_data   TEXT    NOT NULL,
  total_tenants   INTEGER,
  total_missions  INTEGER,
  total_revenue   REAL,
  mrr             REAL,
  arr             REAL,
  created_at      TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_platform_dashboard_snapshots_date ON platform_dashboard_snapshots(created_at);
