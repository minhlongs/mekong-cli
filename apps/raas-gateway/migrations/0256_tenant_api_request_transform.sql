-- Migration: Tenant API request transform rules and application logs
-- Allows tenants to define field-level transform rules applied to incoming requests

CREATE TABLE IF NOT EXISTS api_request_transforms (
  id             TEXT    PRIMARY KEY,
  tenant_id      TEXT    NOT NULL,
  transform_name TEXT    NOT NULL,
  source_path    TEXT    NOT NULL,
  target_path    TEXT    NOT NULL,
  transform_type TEXT    NOT NULL DEFAULT 'map',
  transform_config TEXT,
  enabled        INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_request_transforms_tenant ON api_request_transforms(tenant_id);

-- Log each request where transforms were evaluated
CREATE TABLE IF NOT EXISTS api_request_transform_logs (
  id             TEXT    PRIMARY KEY,
  tenant_id      TEXT    NOT NULL,
  transform_id   TEXT    NOT NULL,
  request_path   TEXT,
  applied        INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_request_transform_logs_tenant ON api_request_transform_logs(tenant_id);
