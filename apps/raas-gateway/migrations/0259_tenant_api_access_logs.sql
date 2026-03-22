-- Migration 0259: Tenant API access logs and export tracking
-- Stores per-request HTTP logs and export job records per tenant

CREATE TABLE IF NOT EXISTS api_access_logs (
  id          TEXT    PRIMARY KEY,
  tenant_id   TEXT    NOT NULL,
  user_id     TEXT,
  method      TEXT    NOT NULL,
  path        TEXT    NOT NULL,
  status_code INTEGER,
  ip_address  TEXT,
  user_agent  TEXT,
  country     TEXT,
  created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_access_logs_tenant ON api_access_logs(tenant_id);

CREATE TABLE IF NOT EXISTS api_access_log_exports (
  id          TEXT    PRIMARY KEY,
  tenant_id   TEXT    NOT NULL,
  format      TEXT    NOT NULL DEFAULT 'csv',
  date_from   TEXT,
  date_to     TEXT,
  status      TEXT    NOT NULL DEFAULT 'pending',
  file_url    TEXT,
  created_at  TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_access_log_exports_tenant ON api_access_log_exports(tenant_id);
