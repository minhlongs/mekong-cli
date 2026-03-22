-- Migration 0268: Tenant API Event Sourcing
-- Tables: api_event_store (append-only events) + api_event_snapshots (aggregate state cache)

CREATE TABLE IF NOT EXISTS api_event_store (
  id             TEXT    PRIMARY KEY,
  tenant_id      TEXT    NOT NULL,
  aggregate_id   TEXT    NOT NULL,
  aggregate_type TEXT    NOT NULL,
  event_type     TEXT    NOT NULL,
  event_data     TEXT    NOT NULL,
  version        INTEGER NOT NULL DEFAULT 1,
  created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_event_store_tenant ON api_event_store(tenant_id);

CREATE TABLE IF NOT EXISTS api_event_snapshots (
  id             TEXT    PRIMARY KEY,
  tenant_id      TEXT    NOT NULL,
  aggregate_id   TEXT    NOT NULL,
  aggregate_type TEXT    NOT NULL,
  snapshot_data  TEXT    NOT NULL,
  version        INTEGER NOT NULL,
  created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_event_snapshots_tenant ON api_event_snapshots(tenant_id);
